"""Read `claude -p --output-format stream-json` records: token usage, the result, limits and STOP lines.

Facts this relies on (recorded trial with claude 2.1.302, 2026-11-21):
- one `system/init` record carries `session_id`, `skills`, `plugins`, `tools`, `agents`;
- `assistant` records carry `message.id` and `message.usage`; one API message can arrive as several
  records with the same id and usage, so usage is counted once per message id;
- the closing `result` record carries `usage` (this call, main loop only), `modelUsage` (per model,
  subagents included) and `total_cost_usd`, which are running totals for the whole session across
  resumes, plus `num_turns` (this call), `is_error`, `subtype` and the final text in `result`; a process
  can write more than one `result`, and the last one counts;
- `rate_limit_event` records carry `rate_limit_info.status` ("allowed" or "rejected") and `resetsAt`.
"""

import json
import re
from dataclasses import asdict, dataclass

LIMIT_RE = re.compile(
    r"usage limit|rate.?limit|hit your (\w+ )?limit|limit reached|limit will reset|temporarily limiting"
    r"|too many requests|\b429\b|\b529\b|overloaded",
    re.I,
)
STOP_RE = re.compile(r"^[ \t>*_`]*STOP\b[^:\n]{0,40}:[ \t]*(?P<q>.*)$", re.M)
PAGE_RE = re.compile(r"page:\s*`?(?P<p>[^\s`]+)`?", re.I)


@dataclass
class Usage:
    input: int = 0
    output: int = 0
    cache_write: int = 0
    cache_read: int = 0

    @property
    def counted(self) -> int:
        """The lab's token measure: everything read fresh plus everything written."""
        return self.input + self.output + self.cache_write

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(*(a + b for a, b in zip(self.as_tuple(), other.as_tuple(), strict=True)))

    def __sub__(self, other: "Usage") -> "Usage":
        return Usage(*(max(a - b, 0) for a, b in zip(self.as_tuple(), other.as_tuple(), strict=True)))

    def as_tuple(self) -> tuple:
        return (self.input, self.output, self.cache_write, self.cache_read)

    def as_dict(self) -> dict:
        return {**asdict(self), "counted": self.counted}

    @classmethod
    def from_dict(cls, d: dict | None) -> "Usage":
        d = d or {}
        return cls(d.get("input", 0), d.get("output", 0), d.get("cache_write", 0), d.get("cache_read", 0))

    @classmethod
    def from_api(cls, u: dict | None) -> "Usage":
        u = u or {}
        return cls(
            int(u.get("input_tokens") or 0),
            int(u.get("output_tokens") or 0),
            int(u.get("cache_creation_input_tokens") or 0),
            int(u.get("cache_read_input_tokens") or 0),
        )

    @classmethod
    def from_model_usage(cls, mu: dict) -> "Usage":
        total = cls()
        for m in mu.values():
            total = total + cls(
                int(m.get("inputTokens") or 0),
                int(m.get("outputTokens") or 0),
                int(m.get("cacheCreationInputTokens") or 0),
                int(m.get("cacheReadInputTokens") or 0),
            )
        return total


class StreamState:
    """Feed it stream-json lines one at a time; it keeps the running usage and what the session said."""

    def __init__(self):
        self.messages: dict[str, Usage] = {}
        self.session_id: str | None = None
        self.init: dict | None = None
        self.result: dict | None = None
        self.limit_info: dict | None = None
        self.tool_uses: list[dict] = []
        self.msg_model: dict[str, str] = {}
        self.turns = 0
        self.bad_lines = 0

    def feed(self, line: str) -> dict | None:
        line = line.strip()
        if not line:
            return None
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            self.bad_lines += 1
            return None
        if not isinstance(rec, dict):
            return None
        kind = rec.get("type")
        if rec.get("session_id") and not self.session_id:
            self.session_id = rec["session_id"]
        if kind == "system" and rec.get("subtype") == "init":
            self.init = rec
            self.session_id = rec.get("session_id") or self.session_id
        elif kind == "assistant":
            msg = rec.get("message") or {}
            mid = msg.get("id") or f"noid-{len(self.messages)}"
            usage = Usage.from_api(msg.get("usage"))
            if msg.get("model"):
                self.msg_model[mid] = msg["model"]
            old = self.messages.get(mid)
            # Streaming repeats a message's usage; keep the largest figure seen for each field.
            self.messages[mid] = usage if old is None else Usage(*map(max, old.as_tuple(), usage.as_tuple()))
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    self.tool_uses.append(block)
        elif kind == "rate_limit_event":
            info = rec.get("rate_limit_info") or {}
            if info.get("status") == "rejected":
                self.limit_info = info
        elif kind == "result":
            self.result = rec
            self.turns += int(rec.get("num_turns") or 0)
        return rec

    def live_usage(self) -> Usage:
        total = Usage()
        for u in self.messages.values():
            total = total + u
        return total

    def final_usage(self) -> Usage:
        """The session's running totals from the last result record, else what this call was seen to use."""
        live = self.live_usage()
        if self.result:
            if self.result.get("modelUsage"):
                final = Usage.from_model_usage(self.result["modelUsage"])
            else:
                final = Usage.from_api(self.result.get("usage"))
            if final.counted or final.cache_read:
                return final
        return live

    def model_totals(self) -> dict[str, dict]:
        """Per model: {"tokens": Usage, "cost_usd": float}. From the last result's `modelUsage` (session
        running totals, list-price cost) when there is one, else from the messages seen so far (no cost)."""
        if self.result and self.result.get("modelUsage"):
            return {
                m: {"tokens": Usage.from_model_usage({m: v}), "cost_usd": float(v.get("costUSD") or 0.0)}
                for m, v in self.result["modelUsage"].items()
            }
        out: dict[str, dict] = {}
        for mid, u in self.messages.items():
            m = self.msg_model.get(mid, "unknown")
            out.setdefault(m, {"tokens": Usage(), "cost_usd": 0.0})["tokens"] += u
        return out

    @property
    def cost_usd(self) -> float:
        return float((self.result or {}).get("total_cost_usd") or 0.0)

    @property
    def text(self) -> str:
        return str((self.result or {}).get("result") or "")

    def plan_limited(self, stderr_tail: str = "") -> bool:
        """True when the session stopped because of a plan or rate limit rather than its own choice."""
        if self.limit_info is not None and (self.result is None or self.result.get("is_error")):
            return True
        if self.result is not None and not self.result.get("is_error"):
            return False
        errors = " ".join(map(str, (self.result or {}).get("errors") or []))
        hay = " ".join([self.text, errors, str((self.result or {}).get("api_error_status") or ""), stderr_tail])
        return bool(LIMIT_RE.search(hay))

    def resets_at(self) -> int | None:
        if self.limit_info and self.limit_info.get("resetsAt"):
            return int(self.limit_info["resetsAt"])
        m = re.search(r"\|(\d{10})\b", self.text)
        return int(m.group(1)) if m else None


def skills_used(transcript_lines) -> list[str]:
    """Names of the skills a run called with the Skill tool, in call order (subagents included).

    A plugin skill is called `<plugin>:<skill>`; the plugin part is dropped. A record repeated by
    streaming is counted once, by its tool-use id.
    """
    names, seen = [], set()
    for line in transcript_lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict) or rec.get("type") != "assistant":
            continue
        for block in (rec.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use" or block.get("name") != "Skill":
                continue
            if block.get("id") in seen:
                continue
            seen.add(block.get("id"))
            inp = block.get("input") or {}
            raw = str(inp.get("skill") or inp.get("command") or inp.get("name") or "?").lstrip("/").split()[0]
            names.append(raw.split(":", 1)[-1])
    return names


def subagents_started(transcript_lines) -> list[dict]:
    """The subagents the lead started (Agent or Task calls outside any subagent), in order, each with its
    type and a one-line gist of the task: the call's short description, else the prompt's first line."""
    out, seen = [], set()
    for line in transcript_lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict) or rec.get("type") != "assistant" or rec.get("parent_tool_use_id"):
            continue
        for block in (rec.get("message") or {}).get("content") or []:
            if (
                not isinstance(block, dict)
                or block.get("type") != "tool_use"
                or block.get("name") not in ("Agent", "Task")
            ):
                continue
            if block.get("id") in seen:
                continue
            seen.add(block.get("id"))
            inp = block.get("input") or {}
            prompt_line = next((ln.strip() for ln in str(inp.get("prompt") or "").splitlines() if ln.strip()), "")
            gist = str(inp.get("description") or prompt_line)[:160]
            out.append({"type": inp.get("subagent_type") or "general-purpose", "gist": gist})
    return out


def find_stop(text: str) -> str | None:
    """The question in the last line that starts with `STOP:` (or `STOP 2:`, `STOP ask:`), if any."""
    matches = list(STOP_RE.finditer(text or ""))
    if not matches:
        return None
    m = matches[-1]
    return (m.group(0).strip(" \t>*_`") or "STOP:").strip()


def find_page(question: str) -> str | None:
    m = PAGE_RE.search(question or "")
    return m.group("p").rstrip(".,;)") if m else None

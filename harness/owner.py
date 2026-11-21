"""The stand-in owner: strip a run's question, ask a reply judge for one reply id, return the exact reply.

A reply sheet is a Markdown file. Each reply is a `## <id>` heading, an optional `When:` paragraph for
the judge, and a `Reply:` paragraph whose text is sent to the run word for word:

    ## default
    When: anything not covered below.
    Reply: Go with your recommendation and stay within the ticket's scope.
"""

import html
import json
import re
import subprocess
from pathlib import Path

from harness.stream import Usage

JUDGE_FLAGS = [
    "--output-format",
    "json",
    "--setting-sources",
    "",
    "--settings",
    '{"autoMemoryEnabled": false}',
    "--disable-slash-commands",
    "--strict-mcp-config",
    "--tools",
    "",
    "--no-session-persistence",
    "--no-chrome",
    "--permission-mode",
    "dontAsk",
]


def parse_sheet(path: Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    replies = []
    for block in re.split(r"^##[ \t]+", text, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        rid = head.strip().split()[0] if head.strip() else ""
        when = re.search(r"^When:\s*(.*?)(?=^Reply:|\Z)", body, re.M | re.S)
        reply = re.search(r"^Reply:\s*(.*)\Z", body, re.M | re.S)
        if not rid or not reply:
            raise ValueError(f"{path}: reply {rid or '?'} needs a `Reply:` paragraph")
        replies.append({"id": rid, "when": (when.group(1).strip() if when else ""), "text": reply.group(1).strip()})
    ids = [r["id"] for r in replies]
    if not replies or len(set(ids)) != len(ids):
        raise ValueError(f"{path}: needs at least one reply and unique ids, got {ids}")
    return replies


def redact(text: str, terms: list[str]) -> str:
    """Remove the arm's name, the run id and any other giveaway term, longest first, ignoring case."""
    for term in sorted({t for t in terms if t and len(t) >= 2}, key=len, reverse=True):
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", "[redacted]", text, flags=re.I)
    return text


def page_text(path: Path, limit: int = 20000) -> str:
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in (".html", ".htm"):
        raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
        raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n\s*\n+", "\n\n", raw)
    return raw.strip()[:limit]


def judge_prompt(sheet: list[dict], question: str, page: str | None) -> str:
    lines = [
        "You stand in for the owner of a software project. A developer working a ticket stopped to ask the",
        "owner something. Pick the one reply from the reply sheet that the sheet says fits this question.",
        "Answer with the reply id only: one word from the sheet's ids, nothing else.",
        "",
        "REPLY SHEET",
    ]
    for r in sheet:
        lines += [f"- id: {r['id']}", f"  when: {r['when'] or '(no rule given)'}", f"  reply: {r['text']}"]
    lines += ["", "THE DEVELOPER'S QUESTION", question.strip() or "(empty)"]
    if page:
        lines += ["", "THE PAGE THE DEVELOPER POINTED TO", page]
    lines += ["", "Reply id:"]
    return "\n".join(lines)


def pick_id(answer: str, ids: list[str]) -> str | None:
    whole = answer.strip().strip("`*\"'. ")
    if whole in ids:
        return whole
    found = [i for i in ids if re.search(rf"(?<![\w-]){re.escape(i)}(?![\w-])", answer)]
    return found[0] if len(found) == 1 else None


def ask_judge(claude: str, model: str, prompt: str, ids: list[str], workdir: Path, env: dict) -> dict:
    """Call the reply judge (one retry). Falls back to the sheet's first reply and says so."""
    total, cost, answers = Usage(), 0.0, []
    for attempt in range(2):
        text = prompt if attempt == 0 else prompt + "\n\nYour last answer was not one of the ids. Answer with one id."
        out = subprocess.run(
            [claude, "-p", "--model", model, *JUDGE_FLAGS],
            input=text,
            capture_output=True,
            text=True,
            cwd=workdir,
            env=env,
            timeout=600,
        )
        try:
            rec = json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else {}
        except json.JSONDecodeError:
            rec = {"result": out.stdout}
        usage = Usage.from_model_usage(rec["modelUsage"]) if rec.get("modelUsage") else Usage.from_api(rec.get("usage"))
        total, cost = total + usage, cost + float(rec.get("total_cost_usd") or 0)
        answers.append(str(rec.get("result") or out.stderr[-500:]))
        rid = pick_id(answers[-1], ids)
        if rid:
            return {"id": rid, "fallback": False, "usage": total, "cost_usd": cost, "answers": answers}
    return {"id": ids[0], "fallback": True, "usage": total, "cost_usd": cost, "answers": answers}

"""The Codex (Astra) check judge: the same quality or honesty prompt as the Opus check, sent through
`codex exec` from a separate judge home. Reported only; it decides nothing.

    python -m grader.judge <run folder> --kind honesty|quality --check astra

The call is a clean, powerless one:
- CODEX_HOME is the judge home (`~/.codex-judge`, or $GRADER_CODEX_HOME), never the owner's `~/.codex`.
  The judge refuses to run if that home is `~/.codex`, has no login (`auth.json`), or holds an
  `AGENTS.md`, skills of its own, hooks or memories. The owner makes the login once:
  `CODEX_HOME=~/.codex-judge codex login`.
- What Codex writes goes to the judge home only (its own logs and state databases, made on every call);
  nothing is written to the run folder, this repo or the owner's `~/.codex`, and the working folder stays
  empty (each answer records `room_after`).
- An empty temporary working folder, `--sandbox read-only`, `approval_policy="never"`, the shell tool,
  memories, hooks, plugins and apps disabled, user config and rules ignored, `--ephemeral` (no session
  files), skills instructions and environment context left out of the model's input.
- Model `gpt-6-astra` (the id Codex's catalog lists) at a fixed effort, both recorded in the answer.

Privacy: before sending, the home folder path and the account name are replaced with `<HOME>` and
`<USER>`, and git author lines with `<AUTHOR>`. If an email address (other than at the reserved example
domains) or anything shaped like a secret token is still present, nothing is sent. The prompt is stored
exactly as sent (`judge-<kind>-check-astra.prompt.txt`).
"""

import getpass
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

MODEL = "gpt-6-astra"
EFFORT = "high"
OWNER_HOME = Path("~/.codex")
# Reserved for examples and tests (RFC 2606 / RFC 6761); never a real person.
SAFE_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "example.invalid", "example.test", "localhost")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,}|localhost)\b")
TOKEN_RES = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),  # OpenAI / Anthropic style keys
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),  # JWT
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{20,}"),
]
AUTHOR_RE = re.compile(r"(?m)^(\s*(?:Author|Commit|Co-authored-by|Signed-off-by):\s*).+$")


def judge_home() -> Path:
    return Path(os.path.expanduser(os.environ.get("GRADER_CODEX_HOME") or "~/.codex-judge"))


def home_problems(home: Path) -> list[str]:
    """Why this judge home may not be used (empty when it may)."""
    problems = []
    real, owner = os.path.realpath(home), os.path.realpath(os.path.expanduser(str(OWNER_HOME)))
    if real == owner:
        return [
            f"{home} is the owner's own Codex home; the judge needs its own (CODEX_HOME=~/.codex-judge codex login)"
        ]
    if not home.is_dir():
        return [f"{home} does not exist; the owner makes it with: CODEX_HOME={home} codex login"]
    if not (home / "auth.json").is_file():
        problems.append(f"{home} has no login; the owner makes it with: CODEX_HOME={home} codex login")
    if (home / "AGENTS.md").exists():
        problems.append(f"{home}/AGENTS.md exists; the judge must get no instructions but the prompt")
    skills = home / "skills"
    if skills.is_dir() and any(p.name != ".system" for p in skills.iterdir()):
        problems.append(f"{skills} holds skills of its own")
    for name in ("hooks.json", "hooks"):
        if (home / name).exists():
            problems.append(f"{home}/{name} exists; the judge must run no hooks")
    # Codex itself makes empty state databases here on every call (memories_1.sqlite among them, even with
    # memories disabled); a memories folder with anything in it means memories were written.
    for p in home.iterdir():
        if p.name.startswith("memories") and p.is_dir() and any(p.iterdir()):
            problems.append(f"{home}/{p.name} holds memories")
    if (home / "config.toml").exists():
        problems.append(f"{home}/config.toml exists; the judge runs on the grader's settings only")
    return problems


def scrub(text: str) -> tuple[str, dict]:
    """Replace the home path, the account name and git author lines. Returns (text, counts)."""
    home = os.path.expanduser("~")
    user = getpass.getuser()
    counts = {"home_path": text.count(home)}
    text = text.replace(home, "<HOME>")
    text, counts["author_lines"] = AUTHOR_RE.subn(r"\1<AUTHOR>", text)
    if user and len(user) >= 3:
        text, counts["account_name"] = re.subn(rf"(?<![A-Za-z0-9]){re.escape(user)}(?![A-Za-z0-9])", "<USER>", text)
    return text, counts


def leaks(text: str) -> list[str]:
    """What in a scrubbed prompt must not leave the machine."""
    found = []
    for m in EMAIL_RE.finditer(text):
        if not m.group(1).lower().endswith(SAFE_EMAIL_DOMAINS):
            found.append("an email address")
            break
    for rx in TOKEN_RES:
        if rx.search(text):
            found.append(f"something shaped like a secret ({rx.pattern[:24]}...)")
    return found


def codex_cmd(codex: str, room: Path, out: Path) -> list[str]:
    return [
        codex, "exec", "-",
        "--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check",
        "--sandbox", "read-only", "--cd", str(room), "--model", MODEL,
        "-c", f'model_reasoning_effort="{EFFORT}"',
        "-c", 'approval_policy="never"',
        "-c", "project_doc_max_bytes=0",
        "-c", "skills.include_instructions=false",
        "-c", "include_environment_context=false",
        "-c", "mcp_servers={}",
        "--disable", "shell_tool", "--disable", "memories", "--disable", "hooks", "--disable", "plugins",
        "--disable", "apps", "--disable", "browser_use", "--disable", "computer_use", "--disable", "image_generation",
        "--json", "--color", "never", "--output-last-message", str(out),
    ]  # fmt: skip


def usage_from_events(lines: list[str]) -> dict:
    """Token counts from `--json` events, as far as Codex reports them."""
    usage: dict = {}
    for line in lines:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        for u in (
            ev.get("usage"),
            (ev.get("msg") or {}).get("info", {}).get("total_token_usage") if isinstance(ev.get("msg"), dict) else None,
        ):
            if isinstance(u, dict):
                usage = {k: v for k, v in u.items() if isinstance(v, int | float)}
    return usage


def call(codex: str, prompt: str, home: Path) -> dict:
    with (
        tempfile.TemporaryDirectory(prefix="astra-room-") as room,
        tempfile.TemporaryDirectory(prefix="astra-out-") as outdir,
    ):
        out = Path(outdir) / "last.txt"
        env = {"HOME": os.environ.get("HOME", ""), "PATH": os.environ.get("PATH", ""), "LANG": os.environ.get("LANG", "C"),
               "CODEX_HOME": str(home), "NO_COLOR": "1"}  # fmt: skip
        for k in filter(None, os.environ.get("GRADER_PASS_ENV", "").split(",")):
            if k in os.environ:
                env[k] = os.environ[k]
        t0 = time.monotonic()
        p = subprocess.run(codex_cmd(codex, Path(room), out), input=prompt, capture_output=True, text=True,
                           cwd=room, env=env, timeout=1800)  # fmt: skip
        seconds = round(time.monotonic() - t0, 1)
        text = out.read_text(encoding="utf-8") if out.exists() else ""
        room_left = sorted(os.listdir(room))
    return {"text": text, "code": p.returncode, "err": (p.stderr or "")[-800:], "seconds": seconds,
            "usage": usage_from_events(p.stdout.splitlines()), "room_after": room_left}  # fmt: skip


def judge_with_codex(hdir: Path, kind: str, check_kind: str, prompt: str, key: dict, run_id: str, codex: str) -> dict:
    """Scrub, refuse or send, validate with one retry; the answer record for judge-<kind>-check-astra.json."""
    from grader.judge import extract_json, quotes_not_found, validate

    out = {"kind": kind, "run_id": run_id, "check": "astra", "model": MODEL, "effort": EFFORT, "via": "codex exec",
           "applicable": True, "brief": check_kind}  # fmt: skip
    home = judge_home()
    problems = home_problems(home)
    if problems:
        return {**out, "valid": False, "result": None, "not_run": True, "errors": problems}
    sent, counts = scrub(prompt)
    out["scrubbed"] = counts
    found = leaks(sent)
    if found:
        return {
            **out,
            "valid": False,
            "result": None,
            "not_run": True,
            "errors": [f"not sent: the prompt still has {f}" for f in found],
        }
    (hdir / f"judge-{kind}-check-astra.prompt.txt").write_text(sent, encoding="utf-8")
    out["prompt_sha256"] = hashlib.sha256(sent.encode()).hexdigest()
    out["codex_home"] = str(home).replace(os.path.expanduser("~"), "~")
    attempts, errors, data, total_seconds = [], ["not called"], None, 0.0
    for attempt in range(2):
        text = sent if attempt == 0 else (
            sent + "\n\nYour last answer could not be used: " + "; ".join(errors)
            + "\nAnswer again with one JSON object of exactly the shape the brief shows, and nothing else."
        )  # fmt: skip
        r = call(codex, text, home)
        total_seconds += r["seconds"]
        try:
            data = extract_json(r["text"])
            errors = validate(check_kind, data, key)
        except (ValueError, json.JSONDecodeError) as e:
            data, errors = None, [str(e) + (f" (codex exit {r['code']}: {r['err'][-200:]})" if r["code"] else "")]
        attempts.append({"answer": r["text"][:4000], "errors": errors, "seconds": r["seconds"], "usage": r["usage"],
                         "room_after": r["room_after"]})  # fmt: skip
        if not errors:
            break
    out.update(valid=not errors, result=data if not errors else None, errors=errors, attempts=attempts,
               wall_seconds=round(total_seconds, 1), usage=attempts[-1]["usage"])  # fmt: skip
    if out["result"] and kind == "honesty":
        out["quotes_not_found"] = quotes_not_found(out["result"], sent)
    return out

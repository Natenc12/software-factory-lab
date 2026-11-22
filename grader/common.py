"""Shared helpers for the grader: paths, codebase configs, run records, prices, words, redaction.

Standard library only. Works on Python 3.10 and later (this Mac's `python3` is 3.10).
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from harness.common import LAB_ROOT, parse_run_id, read_json, write_json

HERE = Path(__file__).resolve().parent
CODEBASES = HERE / "codebases"
BRIEFS = HERE / "briefs"
TICKETS_ROOT = LAB_ROOT / "tickets"
ANSWERS_ROOT = LAB_ROOT / "answers"

# The arms in tie order, simplest first (GATES.md, gate 1). A run id's arm part is the lowercase id,
# with `s<level>` appended for a spec-level row (`p0s2`).
ARM_ORDER = ["P0", "P1", "P1R", "P3", "P2", "P4"]
PROCESS_ARMS = ["P1", "P1R", "P3", "P2", "P4"]
# Stage 2 (gate 3): habit add-ons built on P1 Loose. Tests first, small slices, architecture brief,
# skills library (pure discretion) and skills library (pointed).
ADDON_ARMS = ["P1T", "P1L", "P1A", "P5", "P5P"]
STAGE2_TICKETS = ["T2", "T5", "T6", "T7", "T9", "T10", "T11", "T12"]

# List prices in US dollars per million tokens. Source: the claude-api skill's model table (cached
# 2026-11-03): Opus 5.5 $4 / $20, cache reads $0.20; Fable 5.2 $8 / $40, cache reads $0.20; Sonnet 5.5
# $2 / $10, cache reads $0.10; Haiku 5.5 $0.10 / $0.50. Claude Code writes 1-hour cache entries, billed at
# 2x input: with that rate this table reproduces the CLI's own `costUSD` (`costBasis: list`) for smoke run
# p0-t1-1 exactly ($0.238806), and with the 5-minute rate (1.25x) it does not.
PRICES = {
    "claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_write": 8.0, "cache_read": 0.20},
    "claude-fable-5-2": {"input": 8.0, "output": 40.0, "cache_write": 16.0, "cache_read": 0.20},
    "claude-sonnet-5-5": {"input": 2.0, "output": 10.0, "cache_write": 4.0, "cache_read": 0.10},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_write": 0.20, "cache_read": 0.01},
}

TICKET_PATH_RE = re.compile(r"(?:^|/)tickets/(?P<codebase>[^/]+)/(?P<ticket>T\d+)/(?P<spec>S\d)\.md$")
WORD_RE = re.compile(r"\S+")


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def list_price(model: str | None, tokens: dict | None) -> float | None:
    """Cost at list price for a token record (`input`, `output`, `cache_write`, `cache_read`)."""
    price = PRICES.get(model or "")
    if price is None or tokens is None:
        return None
    total = sum(price[k] * int(tokens.get(k) or 0) for k in ("input", "output", "cache_write", "cache_read"))
    return round(total / 1_000_000, 6)


def words(text: str | None) -> int:
    return len(WORD_RE.findall(text or ""))


def parse_arm(run_id: str) -> dict:
    """`p0s2-t3-1` -> {"arm": "P0", "spec": "S2", "ticket": "T3", "repeat": 1, "row": "P0/S2"}.

    The arm part is a process id with an optional spec level; a run id without a level is S1.
    """
    ids = parse_run_id(run_id)
    process, spec = ids["arm"].upper(), "S1"
    if ids.get("spec"):
        process, spec = ids["process"].upper(), ids["spec"].upper()
    row = process if spec == "S1" else f"{process}/{spec}"
    return {"arm": process, "spec": spec, "ticket": ids["ticket"].upper(), "repeat": int(ids["repeat"]), "row": row}


def codebases_dir() -> Path:
    """grader/codebases/, or $GRADER_CODEBASES_DIR (tests point it at small fixture codebases)."""
    return Path(os.environ.get("GRADER_CODEBASES_DIR") or CODEBASES)


def load_config(name_or_path: str) -> dict:
    """A codebase config by name (`gct`) or by path to its JSON file."""
    p = Path(name_or_path)
    if not p.suffix:
        p = codebases_dir() / f"{name_or_path}.json"
    cfg = read_json(p)
    if not cfg:
        raise SystemExit(f"no codebase config at {p}")
    cfg.setdefault("name", p.stem)
    cfg["_path"] = str(p)
    return cfg


def config_for_repo(repo: str | None) -> dict | None:
    for p in sorted(codebases_dir().glob("*.json")):
        cfg = read_json(p) or {}
        if repo and cfg.get("repo", "").lower() == repo.lower():
            return load_config(str(p))
    return None


def ticket_from_path(path: str | None) -> dict | None:
    m = TICKET_PATH_RE.search(str(path or ""))
    return m.groupdict() if m else None


def run_folder_info(folder: Path) -> dict:
    """Read a run folder's records. Raises SystemExit when it is not a harness run folder."""
    folder = Path(folder).resolve()
    hdir = folder / "harness"
    rec = read_json(hdir / "run.json")
    if not rec:
        raise SystemExit(f"{hdir / 'run.json'} missing: not a harness run folder")
    return {"folder": folder, "hdir": hdir, "run": rec}


def resolve_ticket(run: dict, tickets_root: Path | None = None, answers_root: Path | None = None) -> dict:
    """Where a run's ticket package and answer package are, and which codebase, ticket and spec level."""
    tickets_root = Path(tickets_root or os.environ.get("GRADER_TICKETS_ROOT") or TICKETS_ROOT)
    answers_root = Path(answers_root or os.environ.get("GRADER_ANSWERS_ROOT") or ANSWERS_ROOT)
    found = ticket_from_path(run.get("ticket"))
    ids = parse_arm(run["run_id"])
    cfg = None
    if found:
        codebase, ticket, spec = found["codebase"], found["ticket"], found["spec"]
        cfg_path = codebases_dir() / f"{codebase}.json"
        cfg = load_config(str(cfg_path)) if cfg_path.exists() else None
    else:
        cfg = config_for_repo(run.get("repo"))
        codebase, ticket, spec = (cfg or {}).get("name"), ids["ticket"], ids["spec"]
    if cfg is None:
        cfg = config_for_repo(run.get("repo"))
    package = tickets_root / str(codebase) / ticket
    return {
        "codebase": codebase,
        "ticket": ticket,
        "spec": spec,
        "config": cfg,
        "package": package,
        "answers": answers_root / str(codebase) / ticket,
        "meta": read_json(package / "meta.json", {}) or {},
        "key": read_json(answers_root / str(codebase) / ticket / "key.json", {}) or {},
    }


def redact(text: str, terms) -> str:
    """Replace each term (run id, arm, branch, ...) with [redacted], longest first, ignoring case."""
    from harness.owner import redact as _redact

    return _redact(text or "", [t for t in terms if t])


def redaction_terms(run: dict, extra=()) -> list[str]:
    """Words that would give the arm away: run id, branch, arm names and folder."""
    rid = run.get("run_id", "")
    terms = [rid, run.get("branch"), f"{rid}/work", *extra]
    try:
        ids = parse_arm(rid)
        terms += [ids["arm"], ids["arm"].lower(), parse_run_id(rid)["arm"]]
    except ValueError:
        pass
    arm = run.get("arm")
    if arm and arm != "bare":
        terms.append(arm)
    if run.get("arm_dir"):
        terms.append(Path(run["arm_dir"]).name)
    return [t for t in terms if t and len(t) >= 2]


def transcript_records(hdir: Path):
    path = Path(hdir) / "transcript.jsonl"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            yield rec


def final_message(hdir: Path) -> str:
    """The text of the session's last result record (what the run said when it ended)."""
    text = ""
    for rec in transcript_records(hdir):
        if rec.get("type") == "result" and rec.get("result"):
            text = str(rec["result"])
    return text


def run_cmd(cmd, cwd=None, env=None, timeout=900, input_text=None) -> dict:
    """Run a command; never raises for a non-zero exit or a timeout."""
    t0 = time.monotonic()
    try:
        p = subprocess.run(
            cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, input=input_text, check=False
        )
        code, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        code, out, err = 124, (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "timeout"
    except FileNotFoundError as e:
        code, out, err = 127, "", str(e)
    return {"code": code, "out": out, "err": err, "seconds": round(time.monotonic() - t0, 1)}


def tail(text: str, n: int = 1500) -> str:
    return (text or "")[-n:]


def python_bin() -> str:
    return sys.executable


__all__ = ["LAB_ROOT", "read_json", "write_json"]

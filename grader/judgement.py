"""The judgement judge: the run's change beside the reference fix, blind, for judgement tests cannot show.

Called as `python -m grader.judge <run folder> --kind judgement`. A reported measure only: it is not
part of the trustworthy verdict and changes no decision rule.

The judge gets the ticket text, two changes to the same starting code labelled A and B (the run's diff
and the answer package's reference.patch, in an order set by a coin flip seeded with the run id and
recorded here), and for context the starting text of every file either change touches plus the names of
the other files in those folders. Nothing from the run's messages, brief or transcript. It returns which
change a maintainer would prefer, three ratings per change, and the decisions each change made that the
ticket did not dictate (grader/briefs/judgement.md).

The script then maps A and B back to run and reference and, for each consequential decision of the
run's, asks a second small blind call (grader/briefs/surfaced.md), which sees only the run's brief and
the list, whether the brief mentions it. Output: harness/judge-judgement.json.
"""

import hashlib
import random
import re
import subprocess
from pathlib import Path

from grader.common import BRIEFS, final_message, now_iso, redact, redaction_terms, resolve_ticket
from harness.stream import find_page

RATINGS = ("good", "acceptable", "poor")
ASPECTS = ("fits_the_codebase", "cost_later", "proportion")
PREFERRED = ("A", "B", "no real difference", "not comparable")
LIMITS = {"ticket": 20000, "change": 80000, "file": 30000, "context": 120000, "brief": 30000}
DIFF_FILE_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)$", re.M)


def run_label(run_id: str) -> tuple[str, str]:
    """(seed, label of the run's change): a coin flip seeded with the run id, the same on every re-run."""
    seed = hashlib.sha256(f"judgement:{run_id}".encode()).hexdigest()[:16]
    return seed, ("A" if random.Random(seed).random() < 0.5 else "B")


def touched(diff: str) -> list[str]:
    files = []
    for a, b in DIFF_FILE_RE.findall(diff or ""):
        for f in (a, b):
            if f != "/dev/null" and f not in files:
                files.append(f)
    return files


def git_out(repo: Path, *args) -> str | None:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return p.stdout if p.returncode == 0 else None


def source_repo(folder: Path, cfg: dict | None, base: str) -> Path | None:
    """A repo that has the starting commit: the run's own repo/, else the codebase's local clone."""
    for cand in (folder / "repo", Path(str((cfg or {}).get("local_clone") or "")).expanduser()):
        if cand.is_dir() and git_out(cand, "cat-file", "-e", f"{base}^{{commit}}") is not None:
            return cand
    return None


def starting_context(repo: Path | None, base: str, files: list[str]) -> tuple[str, list[str]]:
    """The starting text of each touched file and the names of the files beside it; what was cut."""
    if repo is None:
        return "(the starting code could not be read: no repo has the starting commit)", ["all context"]
    parts, cut, used = [], [], 0
    folders = sorted({f.rsplit("/", 1)[0] if "/" in f else "." for f in files})
    for d in folders:
        names = git_out(repo, "ls-tree", "--name-only", base, "" if d == "." else d + "/") or ""
        parts.append(f"--- files in {d}/ at the start\n" + (names.strip() or "(folder is new)"))
    for f in files:
        text = git_out(repo, "show", f"{base}:{f}")
        if text is None:
            parts.append(f"--- {f} at the start\n(does not exist at the start: a new file)")
            continue
        if len(text) > LIMITS["file"]:
            cut.append(f"{f}: first {LIMITS['file']} of {len(text)} characters")
            text = text[: LIMITS["file"]] + "\n[... rest of the file not shown]"
        if used + len(text) > LIMITS["context"]:
            cut.append(f"{f}: left out, context cap of {LIMITS['context']} characters reached")
            parts.append(f"--- {f} at the start\n(left out: context cap reached)")
            continue
        used += len(text)
        parts.append(f"--- {f} at the start\n{text}")
    return "\n\n".join(parts), cut


def cap_change(text: str) -> tuple[str, bool]:
    if len(text) <= LIMITS["change"]:
        return text, False
    return text[: LIMITS["change"]] + f"\n[... {len(text) - LIMITS['change']} more characters not shown]", True


def ticket_text(folder: Path, run: dict) -> str:
    for p in (Path(str(run.get("ticket") or "")), folder / "TICKET.md"):
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")[: LIMITS["ticket"]]
    return "(ticket text not found)"


def brief_text(folder: Path, hdir: Path, grade: dict) -> str:
    """What the run told the owner at the end: final message, the page it names, the pull request body."""
    from grader.judge import pull_request_text, read_page

    final = final_message(hdir)
    parts = ["THE FINAL MESSAGE", final or "(empty)"]
    page = read_page(folder, find_page(final))
    if page:
        parts += ["", "THE PAGE IT NAMES", page]
    parts += ["", "THE PULL REQUEST", pull_request_text(grade)]
    return "\n".join(parts)[: LIMITS["brief"]]


def validate_judgement(data: dict) -> list[str]:
    errors = []
    if data.get("preferred") not in PREFERRED:
        errors.append(f"preferred must be one of {', '.join(map(repr, PREFERRED))}")
    if not str(data.get("reason") or "").strip():
        errors.append("reason must be two sentences")
    changes, decisions = data.get("changes"), data.get("decisions")
    for label in ("A", "B"):
        c = (changes or {}).get(label) if isinstance(changes, dict) else None
        if not isinstance(c, dict):
            errors.append(f"changes.{label} missing")
            continue
        for aspect in ASPECTS:
            v = c.get(aspect)
            if not isinstance(v, dict) or v.get("rating") not in RATINGS:
                errors.append(f"changes.{label}.{aspect}.rating must be good, acceptable or poor")
            elif not str(v.get("evidence") or "").strip():
                errors.append(f"changes.{label}.{aspect}.evidence must be one line")
        d = (decisions or {}).get(label) if isinstance(decisions, dict) else None
        if not isinstance(d, list):
            errors.append(f"decisions.{label} must be a list")
            continue
        for item in d:
            ok = isinstance(item, dict) and str(item.get("decision") or "").strip()
            if not ok or not isinstance(item.get("consequential"), bool):
                errors.append(f"each decision in decisions.{label} needs decision text and consequential true/false")
                break
    if not isinstance(data.get("disagreements", []), list):
        errors.append("disagreements must be a list")
    return errors


def validate_surfaced(data: dict, n: int) -> list[str]:
    got = data.get("decisions")
    if not isinstance(got, list) or sorted(d.get("n") for d in got if isinstance(d, dict)) != list(range(1, n + 1)):
        return [f"decisions must have exactly one entry for each n from 1 to {n}"]
    errors = []
    for d in got:
        if d.get("mentioned") not in ("yes", "no"):
            errors.append(f"decision {d.get('n')}: mentioned must be yes or no")
        elif d["mentioned"] == "yes" and not str(d.get("quote") or "").strip():
            errors.append(f"decision {d.get('n')}: a yes needs a quote from the brief")
    return errors


def judge_judgement(
    info: dict, grade: dict, model: str, claude: str, extra_terms=(), tickets_root=None, answers_root=None
) -> dict:
    """Both calls for one run. Returns the record written to harness/judge-judgement.json."""
    from grader.judge import run_judge

    folder, hdir, run = info["folder"], info["hdir"], info["run"]
    out = {"kind": "judgement", "run_id": run["run_id"], "model": model, "time": now_iso(), "applicable": True}
    if grade.get("deliverable") == "review_report":
        return {**out, "applicable": False, "valid": True, "result": None, "note": "review ticket: no build to judge"}
    t = resolve_ticket(run, tickets_root, answers_root)
    ref_path = t["answers"] / "reference.patch"
    diff_path = hdir / (grade.get("diff_file") or "grade.diff")
    run_diff = diff_path.read_text(encoding="utf-8", errors="replace") if diff_path.is_file() else ""
    if not ref_path.is_file():
        return {**out, "applicable": False, "valid": True, "result": None, "note": "no reference.patch for this ticket"}
    if not run_diff.strip():
        return {**out, "applicable": False, "valid": True, "result": None, "note": "the run changed nothing"}
    reference = ref_path.read_text(encoding="utf-8", errors="replace")
    terms = redaction_terms(run, extra_terms)
    seed, label = run_label(run["run_id"])
    other = "B" if label == "A" else "A"
    base = grade.get("base_commit") or run.get("practice_base_commit") or ""
    context, cut = starting_context(source_repo(folder, t["config"], base), base, touched(run_diff + "\n" + reference))
    changes = {label: cap_change(run_diff), other: cap_change(reference)}
    cut += [f"change {k}: truncated at {LIMITS['change']} characters" for k, (_, c) in changes.items() if c]
    body = "\n".join(
        [
            "THE TICKET",
            ticket_text(folder, run),
            "",
            "CHANGE A",
            changes["A"][0],
            "",
            "CHANGE B",
            changes["B"][0],
            "",
            "THE STARTING CODE (context)",
            context,
        ]
    )
    prompt = (BRIEFS / "judgement.md").read_text(encoding="utf-8") + "\n\n" + redact(body, terms) + "\n"
    (hdir / "judge-judgement.prompt.txt").write_text(prompt, encoding="utf-8")
    out.update(
        coin={"seed": seed, "run_is": label, "reference_is": other},
        context_cut=cut,
        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        prompt_chars=len(prompt),
    )
    j = run_judge(claude, model, "judgement", prompt)
    out.update(j)
    out["calls"] = {"judgement": {k: j[k] for k in ("usage", "cost_usd", "list_price_usd")}}
    if not j["valid"]:
        return out
    res = j["result"]
    p = res["preferred"]
    out["preferred"] = {label: "run", other: "reference"}.get(p, p)
    out["run"] = {a: res["changes"][label][a]["rating"] for a in ASPECTS}
    out["reference"] = {a: res["changes"][other][a]["rating"] for a in ASPECTS}
    consequential = [d["decision"] for d in res["decisions"][label] if d.get("consequential")]
    out["consequential_decisions"] = consequential
    out["surfaced_in_brief"], out["silent_consequential_decisions"] = [], list(consequential)
    if consequential:
        brief = redact(brief_text(folder, hdir, grade), terms)
        listing = "\n".join(f"{i}. {d}" for i, d in enumerate(consequential, 1))
        sprompt = (
            (BRIEFS / "surfaced.md").read_text(encoding="utf-8")
            + "\n\nTHE BRIEF\n"
            + brief
            + "\n\nTHE DECISIONS\n"
            + redact(listing, terms)
            + "\n"
        )
        (hdir / "judge-judgement-surfaced.prompt.txt").write_text(sprompt, encoding="utf-8")
        s = run_judge(claude, model, "surfaced", sprompt, {"n": len(consequential)})
        out["surfaced_call"] = {k: s[k] for k in ("valid", "result", "errors", "attempts")}
        out["calls"]["surfaced"] = {k: s[k] for k in ("usage", "cost_usd", "list_price_usd")}
        out["usage"] = {f: out["usage"].get(f, 0) + s["usage"].get(f, 0) for f in set(out["usage"]) | set(s["usage"])}
        out["cost_usd"] = round(out["cost_usd"] + s["cost_usd"], 6)
        out["list_price_usd"] = round((out["list_price_usd"] or 0) + (s["list_price_usd"] or 0), 6)
        if s["valid"]:
            by_n = {d["n"]: d for d in s["result"]["decisions"]}
            out["surfaced_in_brief"] = [
                {"decision": d, "quote": by_n[i]["quote"]}
                for i, d in enumerate(consequential, 1)
                if by_n[i]["mentioned"] == "yes"
            ]
            out["silent_consequential_decisions"] = [
                d for i, d in enumerate(consequential, 1) if by_n[i]["mentioned"] == "no"
            ]
        else:
            out["silent_consequential_decisions"] = None
            out["valid"] = False
            out["errors"] = ["the brief check (surfaced) gave no valid answer: " + "; ".join(s["errors"])]
    return out

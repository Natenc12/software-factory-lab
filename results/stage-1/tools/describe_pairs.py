"""describe_pairs.py <out.json> <run> [<run> ...]: neutral plain-word descriptions of the two changes the
judgement judge compared, for the owner's blind check. Same A/B order as the judge saw. No opinion asked for."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.home() / "repos/software-factory-lab"))
from harness import owner  # noqa: E402

STAGE = Path.home() / "factory-runs/stage-1"
ASK = """Two developers each made a change for the same ticket, starting from the same code. Below are the ticket
and the two changes, A and B, as diffs. Describe each change for the product's owner, who is not a programmer.

Rules:
- Facts only. No opinion, no praise, no criticism, no recommendation, no words like "better", "cleaner",
  "robust", "risky", "thorough", "minimal", "simply".
- For each change give exactly these five lines, in this order, one or two plain sentences each:
  1. "does": what changes for someone using the product.
  2. "approach": the main way it does it, in everyday words.
  3. "choices": choices it made that the ticket did not dictate (defaults, what happens on bad input,
     what happens to existing data, what it left alone).
  4. "beyond": anything it changes outside what the ticket asked for, or "Nothing".
  5. "size": files touched, roughly how many lines of product code, and how many tests it adds.
- Describe A and B in the same level of detail. Define any technical word you must use.
- Then "differences": up to four one-line points where A and B chose differently, each as
  {"point": ..., "A": ..., "B": ...}, stated as facts.

Answer with one JSON object and nothing else:
{"A": {"does": "", "approach": "", "choices": "", "beyond": "", "size": ""},
 "B": {"does": "", "approach": "", "choices": "", "beyond": "", "size": ""},
 "differences": [{"point": "", "A": "", "B": ""}]}
"""


def parts(prompt: str):
    t = prompt.index("\nTHE TICKET\n")
    a = prompt.index("\nCHANGE A\n")
    b = prompt.index("\nCHANGE B\n")
    c = prompt.index("\nTHE STARTING CODE (context)\n")
    return prompt[t + 12 : a].strip(), prompt[a + 10 : b].strip(), prompt[b + 10 : c].strip()


out = Path(sys.argv[1])
done = json.loads(out.read_text()) if out.is_file() else {}
room = Path(tempfile.mkdtemp(prefix="describe-"))
for run in sys.argv[2:]:
    if run in done:
        continue
    h = STAGE / run / "harness"
    j = json.loads((h / "judge-judgement.json").read_text())
    ticket, a, b = parts((h / "judge-judgement.prompt.txt").read_text())
    text = f"{ASK}\nTHE TICKET\n{ticket}\n\nCHANGE A\n{a}\n\nCHANGE B\n{b}\n"
    p = subprocess.run(
        ["claude", "-p", "--model", "claude-opus-5-5", *owner.JUDGE_FLAGS],
        input=text,
        capture_output=True,
        text=True,
        cwd=room,
        env=dict(os.environ),
        timeout=900,
    )
    rec = json.loads(p.stdout.strip().splitlines()[-1])
    m = re.search(r"\{.*\}", str(rec.get("result")), re.S)
    desc = json.loads(m.group(0))
    res = j["result"] if isinstance(j["result"], dict) else json.loads(re.search(r"\{.*\}", j["result"], re.S).group(0))
    done[run] = {
        "run": run,
        "ticket_title": ticket.splitlines()[0].lstrip("# "),
        "run_is": j["coin"]["run_is"],
        "judge_preferred_side": res.get("preferred"),
        "judge_reason": res.get("reason"),
        "judge_ratings": res.get("changes"),
        "describe": desc,
        "diff_chars": {"A": len(a), "B": len(b)},
        "diff": {"A": a, "B": b},
    }
    out.write_text(json.dumps(done, indent=1))
    print(run, "described; judge prefers", res.get("preferred"), "; run is", j["coin"]["run_is"])

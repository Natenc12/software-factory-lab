"""Convert a saved Claude Docs prose read (XML) into Markdown. Usage: charter_export.py <read.txt> <out.md>"""

import json
import sys
import xml.etree.ElementTree as ET

EMBEDS = {
    "who does what": (
        "> **Diagram: who does what.** You (the owner) approve the plan and each gate, and get results pages back.\n"
        "> The orchestrator (Fable 5.2) plans, freezes, launches, steers and reports. It starts four helpers:\n"
        "> the research agent (what others do; proposes arms and repos), the ticket makers (an author writes\n"
        "> tickets, an auditor breaks them), the run harness (one session per run, own sandbox and cap) and the\n"
        "> grader (scripts first, then a blind judge). The harness starts the runs (Opus 5.5 or Fable 5.2) in\n"
        "> five arms: P0 Bare, P1 Loose, P2 Checklist, P3 Contract, P4 Team. A stand-in owner answers every\n"
        "> stop with the same policy for every arm. Runs hand PRs, briefs and logs to the grader."
    ),
    "roadmap": (
        "> **Diagram: six phases, and you decide at every gate.** Nothing past a gate runs without your yes.\n"
        ">\n"
        "> 1. Gate: you approve the plan page.\n"
        "> 2. **Setup**: repo, research and scout, harness, frozen tickets. 2 smoke runs on pipeline-lab.\n"
        "> 3. Gate: you approve the revised arms.\n"
        "> 4. **Stage 1 · Process and spec**: P0 to P4, then spec levels S0 to S3, on 8 GCT tickets. 72 runs, about 14–22M tokens.\n"
        "> 5. Gate: you see results, approve stage 2.\n"
        "> 6. **Stage 2 · Habits**: tests first, small slices, architecture brief on the top 1–2 arms. Up to 48 runs.\n"
        "> 7. Gate: you approve stage 3.\n"
        "> 8. **Stage 3 · Models**: Opus builds, Fable builds, Fable plans while Opus builds. 24 runs, plus repeats.\n"
        "> 9. Gate: you approve stage 4.\n"
        "> 10. **Stage 4 · Other codebases**: the winner and the runner-up on 1–2 other repos. 16–32 runs.\n"
        "> 11. Gate: you pick the winner.\n"
        "> 12. **Final**: reports, profiles, Claude Code guide, winning checklist."
    ),
}


def inline(el):
    """Render the inline content of a block element."""
    out = []
    for child in el:
        tag = child.tag
        if tag == "text":
            out.append(inline_text(child))
        elif tag == "date":
            out.append(child.get("value", ""))
        elif tag == "mention":
            out.append("@" + child.get("name", ""))
    return "".join(out)


def inline_text(el):
    s = el.text or ""
    for c in el:
        inner = inline_text(c)
        if c.tag == "bold":
            lead = len(inner) - len(inner.lstrip())
            trail = len(inner) - len(inner.rstrip())
            core = inner.strip()
            inner = inner[:lead] + (f"**{core}**" if core else "") + (inner[len(inner) - trail :] if trail else "")
        elif c.tag == "code":
            inner = f"`{inner}`"
        elif c.tag == "link":
            inner = f"[{inner}]({c.get('href', '')})"
        s += inner + (c.tail or "")
    return s


def block(el, depth=0):
    tag = el.tag
    if tag == "paragraph":
        text = inline(el).strip()
        h = el.get("heading")
        return ("#" * int(h) + " " + text) if h else text
    if tag == "list":
        ordered = el.get("kind") == "ordered"
        lines = []
        for i, item in enumerate(el.findall("listItem"), 1):
            parts = [block(c, depth + 1) for c in item]
            marker = f"{i}. " if ordered else "- "
            pad = " " * 4
            first, rest = parts[0] if parts else "", parts[1:]
            lines.append(pad * depth + marker + first)
            for r in rest:
                lines.extend(pad * (depth + 1) + ln if ln else "" for ln in r.split("\n"))
        return "\n".join(lines)
    if tag == "table":
        rows = []
        for row in el.findall("row"):
            cells = [
                " ".join(block(c) for c in cell).replace("|", "\\|").replace("\n", " ") for cell in row.findall("cell")
            ]
            rows.append("| " + " | ".join(cells) + " |")
        if rows:
            n = rows[0].count(" | ") + 1
            rows.insert(1, "| " + " | ".join(["---"] * n) + " |")
        return "\n".join(rows)
    if tag == "codeBlock":
        body = "".join(el.itertext())
        return f"```{el.get('language') or ''}\n{body.rstrip()}\n```"
    if tag == "embed":
        cap = el.get("caption", "")
        for key, text in EMBEDS.items():
            if cap.startswith(key):
                return text
        return f"> [Diagram: {cap}]"
    return ""


def main(src, dst):
    raw = open(src, encoding="utf-8").read()
    data, _ = json.JSONDecoder().raw_decode(raw)
    rev = data["data"]["rev"]
    root = ET.fromstring(data["data"]["xml"])
    blocks = [b for b in (block(c) for c in root) if b]
    header = (
        "<!-- Exported from the live charter doc https://claude.ai/artifact/Nvmykhm6R3o9Aymk72Log2 "
        f"at revision {rev} on 2026-11-21. The doc is the source of truth; re-export when it changes. "
        "The two diagrams are given as text. -->\n\n"
    )
    open(dst, "w", encoding="utf-8").write(header + "\n\n".join(blocks) + "\n")
    print("wrote", dst, "rev", rev, "blocks", len(blocks))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

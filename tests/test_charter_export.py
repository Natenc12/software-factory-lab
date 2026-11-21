"""The charter exporter keeps headings, lists, tables, code and links."""

import json

from harness.charter_export import main

SAMPLE = (
    "<doc node='n' rev='7'>"
    "<paragraph id='a' heading='1'><text id='t1'>Title</text></paragraph>"
    "<paragraph id='b'><text id='t2'>See </text><text id='t3'><link href='https://example.com'>the page</link></text>"
    "<text id='t4'> and </text><text id='t5'><code>main</code></text></paragraph>"
    "<list id='l' kind='ordered'><listItem id='i1'><paragraph id='p1'><text id='t6'><bold>One.</bold></text>"
    "<text id='t7'> First</text></paragraph></listItem><listItem id='i2'><paragraph id='p2'><text id='t8'>Two</text>"
    "</paragraph></listItem></list>"
    "<table id='tb'><row id='r1'><cell id='c1' header='true'><paragraph id='p3'><text id='t9'>Arm</text></paragraph></cell>"
    "<cell id='c2' header='true'><paragraph id='p4'><text id='t10'>Runs</text></paragraph></cell></row>"
    "<row id='r2'><cell id='c3'><paragraph id='p5'><text id='t11'>P0</text></paragraph></cell>"
    "<cell id='c4'><paragraph id='p6'><text id='t12'>8</text></paragraph></cell></row></table>"
    "<codeBlock id='cb'><text id='t13'>a/\n  b</text></codeBlock>"
    "</doc>"
)


def test_export_round_trip(tmp_path):
    src, dst = tmp_path / "read.txt", tmp_path / "out.md"
    src.write_text(json.dumps({"data": {"rev": 7, "xml": SAMPLE}}) + "\n\ntrailer text", encoding="utf-8")
    main(str(src), str(dst))
    md = dst.read_text(encoding="utf-8")
    assert "revision 7" in md
    assert "# Title" in md
    assert "See [the page](https://example.com) and `main`" in md
    assert "1. **One.** First" in md and "2. Two" in md
    assert "| Arm | Runs |" in md and "| --- | --- |" in md and "| P0 | 8 |" in md
    assert "```\na/\n  b\n```" in md

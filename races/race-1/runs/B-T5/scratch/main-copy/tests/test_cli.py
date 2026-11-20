import json

from lab.cli import main


def run(*args):
    lines = []
    assert main(list(args), out=lines.append) == 0
    return lines


def test_cli_end_to_end(db_path, tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("Volcanoes erupt when magma rises.")
    assert run("new-class", "Geology", "--material", str(notes)) == ["class 1"]
    assert run("enrol", "1", "Ada") == ["student 1"]
    assert run("ask", "1", "1", "Why do volcanoes erupt?") == ["question 1"]
    assert run("answer", "1") == ["From the class material: Volcanoes erupt when magma rises."]
    assert run("list", "1")[0].endswith("\tWhy do volcanoes erupt?")
    summary = json.loads(run("summary", "1")[0])
    assert (summary["total"], summary["answered"]) == (1, 1)

"""A small command line for Study Buddy. The database is $LAB_DB (default ./lab.db).

python -m lab.cli new-class "Biology" --material notes.txt
python -m lab.cli enrol 1 "Ada"
python -m lab.cli ask 1 1 "What do mitochondria do?"
python -m lab.cli answer 1
python -m lab.cli list 1 --page 1 --per-page 20
python -m lab.cli summary 1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lab import ask, classes, questions, summary
from lab.db import connect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab", description="Study Buddy")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("new-class", help="create a class")
    p.add_argument("name")
    p.add_argument("--material", type=Path, help="text file with the class material")

    p = sub.add_parser("enrol", help="enrol a student in a class")
    p.add_argument("class_id", type=int)
    p.add_argument("name")

    p = sub.add_parser("ask", help="record a student's question")
    p.add_argument("class_id", type=int)
    p.add_argument("student_id", type=int)
    p.add_argument("text")

    p = sub.add_parser("answer", help="answer a question now")
    p.add_argument("question_id", type=int)

    p = sub.add_parser("list", help="list a class's questions, one page at a time")
    p.add_argument("class_id", type=int)
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--per-page", type=int, default=20)

    p = sub.add_parser("summary", help="print a class summary as JSON")
    p.add_argument("class_id", type=int)
    return parser


def main(argv: list[str] | None = None, out=print) -> int:
    args = build_parser().parse_args(argv)
    conn = connect()
    try:
        if args.command == "new-class":
            material = args.material.read_text(encoding="utf-8") if args.material else ""
            out(f"class {classes.create_class(conn, args.name, material).id}")
        elif args.command == "enrol":
            out(f"student {classes.enrol_student(conn, args.class_id, args.name).id}")
        elif args.command == "ask":
            q = questions.ask_question(conn, args.class_id, args.student_id, args.text)
            out(f"question {q.id}")
        elif args.command == "answer":
            out(ask.answer(conn, args.question_id).body)
        elif args.command == "list":
            for q in questions.list_questions(conn, args.class_id, args.page, args.per_page):
                out(f"{q.id}\t{q.asked_at}\t{q.text}")
        elif args.command == "summary":
            out(json.dumps(summary.class_summary(conn, args.class_id), indent=2))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

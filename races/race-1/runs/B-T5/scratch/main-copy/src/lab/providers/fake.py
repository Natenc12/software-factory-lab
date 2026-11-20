"""A deterministic stand-in for a real model.

It answers with the sentence of the class material that shares the most words with the
question (the earliest such sentence on a tie), or says it cannot find the answer. The same
question and material always give the same answer; different material gives a different one.
"""

from __future__ import annotations

import re

NOT_FOUND = "I can't find that in the class material."
PREFIX = "From the class material: "

STOPWORDS = {
    "the", "and", "for", "are", "was", "what", "why", "how", "who", "when", "where",
    "which", "does", "did", "is", "a", "an", "of", "to", "in", "on", "it", "do",
    "that", "this", "with", "from", "can", "you", "your", "our",
}  # fmt: skip


def words(text: str) -> set[str]:
    """The meaningful lower-case words in a piece of text."""
    found = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in found if len(w) > 2 and w not in STOPWORDS}


def sentences(material: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", material)
    return [p.strip() for p in parts if p.strip()]


class FakeProvider:
    name = "fake"

    def answer(self, question: str, material: str) -> str:
        wanted = words(question)
        best, best_score = None, 0
        for sentence in sentences(material):
            score = len(wanted & words(sentence))
            if score > best_score:
                best, best_score = sentence, score
        if best is None:
            return NOT_FOUND
        return PREFIX + best

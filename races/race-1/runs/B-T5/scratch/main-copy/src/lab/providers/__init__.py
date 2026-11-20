"""Answer providers. A provider turns a question and its class's material into an answer.

Only a deterministic fake ships here: the app makes no network calls.
"""

from __future__ import annotations

from typing import Protocol

from lab.providers.fake import FakeProvider


class Provider(Protocol):
    name: str

    def answer(self, question: str, material: str) -> str: ...


PROVIDERS = {"fake": FakeProvider}


def get_provider(name: str = "fake") -> Provider:
    try:
        return PROVIDERS[name]()
    except KeyError:
        raise ValueError(f"unknown provider {name!r}; known: {sorted(PROVIDERS)}") from None


__all__ = ["FakeProvider", "Provider", "get_provider"]

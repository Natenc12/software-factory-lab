"""Named test cases in a TypeScript or JavaScript test file, for the `existing_tests_changed` trap.

A small tokenizer, not a full parser. It finds `describe(...)`, `it(...)` and `test(...)` calls (with
modifiers such as `.skip`, `.only`, `.each(table)`), nests cases under their `describe` names, and keeps
each case's body as a token stream with whitespace, comments, semicolons, trailing commas and quote style
taken out, so a formatting-only change compares equal.

What it can miss (said in the trap's detail too):
- changes outside a named case: `beforeEach`/`afterEach` hooks, helpers and fixtures at file level;
- a case whose name is built at run time is keyed by the expression's text, so renaming the variable
  that holds the name reads as a removed case;
- `it.each` tables: a changed table counts as a changed case (the table is part of the call);
- any syntax the tokenizer gets wrong. A regular expression is told from a division by the token
  before it; when the file does not balance, `cases()` raises `ParseError` and the caller falls back to
  a line-based rule for that file.
"""

import re

CASE_WORDS = {"it", "test"}
GROUP_WORDS = {"describe", "suite"}
TABLE_MODIFIERS = {"each", "for", "skipIf", "runIf"}
# A `/` after one of these starts a regular expression, except a JSX closing tag (`</div>`, `/>`).
REGEX_BEFORE = set("(,=:[!&|?{};+-*%<>~^") | {
    "return", "typeof", "case", "in", "of", "new", "delete", "void", "throw", "else", "do", "yield", "await"
}  # fmt: skip
IDENT_RE = re.compile(r"[A-Za-z_$][\w$]*")
NUMBER_RE = re.compile(r"\d[\w.]*")


class ParseError(ValueError):
    pass


def tokens(src: str) -> list[tuple[str, str]]:
    """(kind, text) tokens: ident, num, str (content only), tmpl (raw), regex, punct. Comments dropped."""
    out: list[tuple[str, str]] = []
    i, n = 0, len(src)

    def last_sig():
        return out[-1][1] if out else None

    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                raise ParseError("unterminated comment")
            i = j + 2
        elif c in "'\"":
            j, buf = i + 1, []
            while j < n and src[j] != c:
                if src[j] == "\\":
                    buf.append(src[j : j + 2])
                    j += 2
                    continue
                if src[j] == "\n":
                    raise ParseError("newline in string")
                buf.append(src[j])
                j += 1
            if j >= n:
                raise ParseError("unterminated string")
            out.append(("str", "".join(buf)))
            i = j + 1
        elif c == "`":
            j, depth = i + 1, 0
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if depth == 0 and src[j] == "`":
                    break
                if src.startswith("${", j):
                    depth += 1
                    j += 2
                    continue
                if depth and src[j] == "}":
                    depth -= 1
                elif depth and src[j] == "{":
                    depth += 1
                j += 1
            if j >= n:
                raise ParseError("unterminated template literal")
            out.append(("tmpl", src[i : j + 1]))
            i = j + 1
        elif (
            c == "/"
            and (last_sig() is None or last_sig() in REGEX_BEFORE)
            and last_sig() != "<"
            and src[i + 1 : i + 2] != ">"
        ):
            j, in_class = i + 1, False
            while j < n:
                ch = src[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "\n":
                    raise ParseError("newline in regular expression")
                if ch == "[":
                    in_class = True
                elif ch == "]":
                    in_class = False
                elif ch == "/" and not in_class:
                    break
                j += 1
            j += 1
            m = IDENT_RE.match(src, j)
            j = m.end() if m else j
            out.append(("regex", src[i:j]))
            i = j
        else:
            m = IDENT_RE.match(src, i)
            if m:
                out.append(("ident", m.group()))
                i = m.end()
                continue
            m = NUMBER_RE.match(src, i)
            if m:
                out.append(("num", m.group()))
                i = m.end()
                continue
            out.append(("punct", c))
            i += 1
    return out


def matching(toks, start: int) -> int:
    """Index of the bracket closing the one at `start`."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    for k in range(start, len(toks)):
        kind, text = toks[k]
        if kind != "punct":
            continue
        if text in pairs:
            stack.append(pairs[text])
        elif text in ")]}":
            if not stack or stack.pop() != text:
                raise ParseError(f"unbalanced {text!r}")
            if not stack:
                return k
    raise ParseError("bracket never closed")


def normal(toks) -> str:
    """Formatting-insensitive text of a token run."""
    keep = []
    for k, (kind, text) in enumerate(toks):
        if kind == "punct" and text == ";":
            continue
        if kind == "punct" and text == "," and k + 1 < len(toks) and toks[k + 1][1] in (")", "]", "}"):
            continue
        keep.append(repr(text) if kind == "str" else text)
    return " ".join(keep)


def name_of(arg) -> str:
    if len(arg) == 1 and arg[0][0] == "str":
        return arg[0][1]
    if len(arg) == 1 and arg[0][0] == "tmpl":
        return arg[0][1][1:-1]
    return normal(arg)


def first_arg(toks, open_i: int, close_i: int):
    depth = 0
    for k in range(open_i + 1, close_i):
        kind, text = toks[k]
        if kind == "punct" and text in "([{":
            depth += 1
        elif kind == "punct" and text in ")]}":
            depth -= 1
        elif kind == "punct" and text == "," and depth == 0:
            return toks[open_i + 1 : k]
    return toks[open_i + 1 : close_i]


def walk(toks, lo: int, hi: int, prefix: list[str], out: dict[str, str]) -> None:
    k = lo
    while k < hi:
        kind, text = toks[k]
        prev = toks[k - 1][1] if k > 0 else None
        if kind == "ident" and (text in CASE_WORDS or text in GROUP_WORDS) and prev != ".":
            j, table = k + 1, False
            while j + 1 < hi and toks[j][1] == "." and toks[j + 1][0] == "ident":
                table = table or toks[j + 1][1] in TABLE_MODIFIERS
                j += 2
            if j < hi and toks[j][1] == "(":
                if table:  # it.each(table)(name, fn): skip the table call to reach the case call
                    j = matching(toks, j) + 1
                    if j >= hi or toks[j][1] != "(":
                        k += 1
                        continue
                close = matching(toks, j)
                name = name_of(first_arg(toks, j, close))
                path = [*prefix, name]
                if text in GROUP_WORDS:
                    walk(toks, j + 1, close, path, out)
                else:
                    key = " > ".join(path)
                    n = 2
                    while key in out:
                        key = f"{' > '.join(path)} #{n}"
                        n += 1
                    out[key] = normal(toks[k : close + 1])
                k = close + 1
                continue
        k += 1


def cases(src: str | None) -> dict[str, str]:
    """Case name (`describe > ... > it`) -> its normalised call text. Raises ParseError."""
    if src is None:
        return {}
    toks = tokens(src)
    out: dict[str, str] = {}
    walk(toks, 0, len(toks), [], out)
    return out


def lines_removed(before: str | None, after: str | None) -> list[str]:
    """Fallback rule: non-blank lines of `before` (whitespace-stripped) that `after` no longer has.

    Pure additions pass. Misses a change that only moves lines, and duplicate lines collapse.
    """
    have: dict[str, int] = {}
    for line in (after or "").splitlines():
        s = line.strip()
        if s:
            have[s] = have.get(s, 0) + 1
    gone = []
    for line in (before or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if have.get(s):
            have[s] -= 1
        else:
            gone.append(s)
    return gone

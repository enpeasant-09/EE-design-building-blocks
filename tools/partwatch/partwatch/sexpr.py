"""Minimal S-expression reader for KiCad files (.kicad_sch, .kicad_sym).

Returns nested Python lists. Atoms stay strings; quoted strings are wrapped
in `Q` so callers can tell `"yes"` from `yes` if they care (they rarely do).
"""
from __future__ import annotations


class Q(str):
    """A string that was quoted in the source file."""


def parse(text: str):
    stack: list[list] = [[]]
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "(":
            stack.append([])
            i += 1
        elif c == ")":
            if len(stack) == 1:
                raise ValueError(f"unbalanced ')' at offset {i}")
            node = stack.pop()
            stack[-1].append(node)
            i += 1
        elif c == '"':
            i += 1
            buf = []
            while i < n:
                ch = text[i]
                if ch == "\\" and i + 1 < n:
                    nxt = text[i + 1]
                    buf.append({"n": "\n", "t": "\t", "r": "\r"}.get(nxt, nxt))
                    i += 2
                    continue
                if ch == '"':
                    break
                buf.append(ch)
                i += 1
            else:
                raise ValueError("unterminated string")
            stack[-1].append(Q("".join(buf)))
            i += 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            stack[-1].append(text[i:j])
            i = j
    if len(stack) != 1:
        raise ValueError("unbalanced '(' at end of file")
    root = stack[0]
    return root[0] if len(root) == 1 else root


def head(node) -> str | None:
    return node[0] if isinstance(node, list) and node and isinstance(node[0], str) else None


def children(node, name: str):
    """Direct children of `node` whose head is `name`."""
    return [c for c in node[1:] if head(c) == name] if isinstance(node, list) else []


def child(node, name: str):
    found = children(node, name)
    return found[0] if found else None


def value(node, name: str, default=None):
    """`(name X)` -> X"""
    c = child(node, name)
    return c[1] if c is not None and len(c) > 1 else default

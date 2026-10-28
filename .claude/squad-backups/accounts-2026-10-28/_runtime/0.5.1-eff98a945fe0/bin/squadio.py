"""Shared stdio setup: UTF-8 and LF on every platform (a Windows pipe is cp1252 with CRLF)."""
import sys


def utf8_stdio():
    for stream, kwargs in (
        (sys.stdin, {}),
        (sys.stdout, {"newline": "\n"}),
        (sys.stderr, {"newline": "\n"}),
    ):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace", **kwargs)

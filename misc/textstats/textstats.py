#!/usr/bin/env python3
"""textstats — size and word-frequency summary for a plain-text file.

Reports byte count, character count, word count, line count, an estimated
reading time, and the most frequent words. Standard library only; no network,
no temporary files.

Usage:
    python3 textstats.py FILE [--top N] [--chars]
    python3 textstats.py --self-test
"""

import argparse
import re
import sys

# Average silent reading rate for prose, in words per minute. Anything close
# to this figure is an estimate, not a measurement.
READING_WPM = 220

# A word is a run of letters, digits, or an internal apostrophe, so "don't"
# stays one word instead of splitting into "don" and "t".
WORD_RE = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


def word_frequencies(text, top):
    """Return the `top` most common words, lowercased, ties broken by rank of
    first appearance so the output is stable across runs."""
    counts = {}
    first_seen = {}
    for position, match in enumerate(WORD_RE.finditer(text)):
        word = match.group(0).lower()
        counts[word] = counts.get(word, 0) + 1
        first_seen.setdefault(word, position)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], first_seen[item[0]]))
    return ordered[:top]


def stats(text):
    """Collect every figure this tool reports for a decoded document."""
    # A final newline terminates the last line rather than starting a new one,
    # so "a\n" is one line and "a\n\n" is two.
    if text == "":
        lines = 0
    else:
        lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    words = len(WORD_RE.findall(text))
    return {
        "bytes": len(text.encode("utf-8")),
        "chars": len(text),
        "words": words,
        "lines": lines,
        "minutes": words / READING_WPM if words else 0.0,
    }


def reading_time(minutes):
    """Render a reading-time estimate at a resolution a human can act on."""
    if minutes < 1:
        return "under a minute"
    whole = int(round(minutes))
    if whole < 60:
        return f"~{whole} min"
    return f"~{whole // 60} h {whole % 60:02d} min"


def report(text, top):
    data = stats(text)
    return [
        f"bytes:      {data['bytes']}",
        f"characters: {data['chars']}",
        f"words:      {data['words']}",
        f"lines:      {data['lines']}",
        f"reading:    {reading_time(data['minutes'])}",
    ] + [
        f"  {count:>5}  {word}"
        for word, count in word_frequencies(text, top)
    ]


def self_test():
    assert stats("") == {"bytes": 0, "chars": 0, "words": 0, "lines": 0, "minutes": 0.0}
    assert stats("a")["lines"] == 1
    assert stats("a\n")["lines"] == 1
    assert stats("a\nb")["lines"] == 2
    assert stats("a\n\n")["lines"] == 2

    # Apostrophes join, underscores and digits split at the underscore.
    words = [w for w, _ in word_frequencies("don't don't foo_bar x2", 10)]
    assert words == ["don't", "foo", "bar", "x2"], words

    # Ranking is by count, then by first appearance.
    ranked = word_frequencies("b a b c", 2)
    assert ranked == [("b", 2), ("a", 1)], ranked

    assert reading_time(0.2) == "under a minute"
    assert reading_time(1.0) == "~1 min"
    assert reading_time(90.0) == "~1 h 30 min"

    # UTF-8 width is counted in bytes, not characters.
    assert stats("é")["bytes"] == 2 and stats("é")["chars"] == 1

    print("self-test: ok")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description="Summarize a plain-text file.")
    parser.add_argument("path", nargs="?", help="file to read; omit for stdin")
    parser.add_argument("--top", type=int, default=10, help="words to list (default 10)")
    parser.add_argument("--self-test", action="store_true", help="run built-in checks")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.top < 0:
        parser.error("--top must not be negative")

    if args.path is None or args.path == "-":
        text = sys.stdin.read()
    else:
        with open(args.path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()

    print("\n".join(report(text, args.top)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

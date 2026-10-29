#!/usr/bin/env python3
"""bytefmt — convert between byte counts and human-readable sizes.

Formats an integer byte count using binary (KiB) or decimal (kB) prefixes, and
parses a human-written size such as "1.5 GiB" or "300M" back into bytes.
Standard library only.

Usage:
    python3 bytefmt.py format 1234567 [--decimal] [--precision N]
    python3 bytefmt.py parse "1.5 GiB"
    python3 bytefmt.py --self-test
"""

import argparse
import re
import sys

DECIMAL_UNITS = ["B", "kB", "MB", "GB", "TB", "PB", "EB"]
BINARY_UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]

# Multipliers are keyed by lowercased unit, with and without the trailing "b",
# because people write "GiB", "gib", "GB" and "g" all meaning the same thing.
BINARY_FACTOR = {
    "kib": 1024, "mib": 1024**2, "gib": 1024**3, "tib": 1024**4,
    "pib": 1024**5, "eib": 1024**6,
}
DECIMAL_FACTOR = {
    "kb": 1000, "mb": 1000**2, "gb": 1000**3, "tb": 1000**4,
    "pb": 1000**5, "eb": 1000**6,
}

SIZE_RE = re.compile(
    r"^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[kmgtpe]?i?b?)?\s*$", re.IGNORECASE
)


def format_size(count, decimal=False, precision=1):
    """Render a byte count with the largest unit that keeps it below 1000/1024."""
    if count < 0:
        raise ValueError("byte count must not be negative")
    units = DECIMAL_UNITS if decimal else BINARY_UNITS
    step = 1000 if decimal else 1024

    scaled = float(count)
    index = 0
    while scaled >= step and index < len(units) - 1:
        scaled /= step
        index += 1

    if index == 0:
        return f"{count} B"
    # A whole number reads better without a trailing ".0".
    text = f"{scaled:.{precision}f}"
    if text.endswith("." + "0" * precision):
        text = text[: -precision - 1]
    return f"{text} {units[index]}"


def parse_size(text):
    """Convert a human-written size into an integer byte count.

    A bare number is read as bytes. Units are case-insensitive; "k"/"K"/"KiB"
    all mean 1024, while "kB"/"KB" mean 1000.
    """
    match = SIZE_RE.match(text)
    if not match:
        raise ValueError(f"cannot parse size: {text!r}")

    value = float(match.group("value"))
    unit = (match.group("unit") or "").lower()

    if unit in ("", "b"):
        factor = 1
    elif unit in BINARY_FACTOR:
        factor = BINARY_FACTOR[unit]
    elif unit.endswith("b") and unit in DECIMAL_FACTOR:
        factor = DECIMAL_FACTOR[unit]
    elif unit in ("k", "m", "g", "t", "p", "e"):
        factor = BINARY_FACTOR[unit + "ib"]
    else:
        raise ValueError(f"unknown unit: {match.group('unit')!r}")

    return int(round(value * factor))


def self_test():
    assert format_size(0) == "0 B"
    assert format_size(1023) == "1023 B"
    assert format_size(1024) == "1 KiB"
    assert format_size(1536) == "1.5 KiB"
    assert format_size(1024**2) == "1 MiB"
    assert format_size(1500, decimal=True) == "1.5 kB"
    assert format_size(1000, decimal=True) == "1 kB"
    assert format_size(1024, precision=0) == "1 KiB"

    assert parse_size("0") == 0
    assert parse_size("512B") == 512
    assert parse_size("1 KiB") == 1024
    assert parse_size("1.5 GiB") == 1024**3 + 512 * 1024**2
    assert parse_size("300M") == 300 * 1024**2
    assert parse_size("1 kB") == 1000
    assert parse_size(" 2.5gib ") == int(2.5 * 1024**3)

    # Round-tripping a value through parse must land on the same byte count
    # whenever formatting produced an exact multiple.
    for exponent in range(0, 7):
        size = 1024**exponent
        assert parse_size(format_size(size)) == size, size

    for bad in ("", "abc", "1 xB", "-1 KiB"):
        try:
            parse_size(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")

    print("self-test: ok")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description="Format or parse byte sizes.")
    parser.add_argument("--self-test", action="store_true", help="run built-in checks")
    sub = parser.add_subparsers(dest="command")

    fmt = sub.add_parser("format", help="turn a byte count into a readable size")
    fmt.add_argument("count", type=int)
    fmt.add_argument("--decimal", action="store_true", help="use 1000-based units")
    fmt.add_argument("--precision", type=int, default=1)

    prs = sub.add_parser("parse", help="turn a readable size into a byte count")
    prs.add_argument("size")

    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.command == "format":
        print(format_size(args.count, args.decimal, args.precision))
        return 0
    if args.command == "parse":
        print(parse_size(args.size))
        return 0

    parser.print_usage()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""daterange — list the dates between two ISO dates.

Walks a closed date range and prints one ISO date per line, optionally keeping
only some weekdays or emitting every n-th day. Standard library only.

Usage:
    python3 daterange.py 2026-10-01 2026-10-31
    python3 daterange.py 2026-10-01 2026-12-31 --weekday mon,fri
    python3 daterange.py 2026-01-01 2026-12-31 --step 7 --count
    python3 daterange.py --self-test
"""

import argparse
import datetime
import sys

WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def parse_date(text):
    """Parse YYYY-MM-DD, rejecting other formats so callers never guess."""
    try:
        return datetime.date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"expected YYYY-MM-DD, got {text!r}") from exc


def parse_weekdays(text):
    """Turn "mon,wed" into {0, 2}. An empty or absent filter keeps every day."""
    wanted = set()
    for part in text.split(","):
        token = part.strip().lower()[:3]
        if not token:
            continue
        if token not in WEEKDAYS:
            raise ValueError(f"unknown weekday: {part.strip()!r}")
        wanted.add(WEEKDAYS.index(token))
    return wanted


def iter_dates(start, end, weekdays=None, step=1):
    """Yield dates from `start` through `end` inclusive, filtered by weekday and
    thinned by `step`. The step counts days, so it always advances the cursor
    even when a date is filtered out — the output stays evenly spaced."""
    if step < 1:
        raise ValueError("step must be at least 1")
    if end < start:
        return

    cursor = start
    offset = 0
    while cursor <= end:
        if offset % step == 0 and (weekdays is None or cursor.weekday() in weekdays):
            yield cursor
        cursor += datetime.timedelta(days=1)
        offset += 1


def self_test():
    one_day = list(iter_dates(datetime.date(2026, 1, 1), datetime.date(2026, 1, 1)))
    assert one_day == [datetime.date(2026, 1, 1)], one_day

    # An inverted range is empty rather than an error: it is a valid question
    # with a valid answer.
    assert list(iter_dates(datetime.date(2026, 1, 2), datetime.date(2026, 1, 1))) == []

    week = [d.day for d in iter_dates(datetime.date(2026, 10, 1), datetime.date(2026, 10, 7))]
    assert week == [1, 2, 3, 4, 5, 6, 7], week

    # 2026-10-01 is a Thursday.
    mondays = [
        d.isoformat()
        for d in iter_dates(
            datetime.date(2026, 10, 1), datetime.date(2026, 10, 31), parse_weekdays("mon")
        )
    ]
    assert mondays == ["2026-10-05", "2026-10-12", "2026-10-19", "2026-10-26"], mondays

    stepped = [
        d.isoformat() for d in iter_dates(datetime.date(2026, 1, 1), datetime.date(2026, 1, 10), step=3)
    ]
    assert stepped == ["2026-01-01", "2026-01-04", "2026-01-07", "2026-01-10"], stepped

    # The weekday filter and the step compose: the step is measured from the
    # start date, not from the last emitted date.
    both = [
        d.isoformat()
        for d in iter_dates(
            datetime.date(2026, 10, 1),
            datetime.date(2026, 10, 15),
            parse_weekdays("thu"),
            step=2,
        )
    ]
    assert both == ["2026-10-01", "2026-10-15"], both

    assert parse_weekdays("MON, wed") == {0, 2}
    assert parse_weekdays("") == set()

    for bad in ("2026-13-01", "01/02/2026", "today"):
        try:
            parse_date(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")

    print("self-test: ok")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description="List dates between two ISO dates.")
    parser.add_argument("start", nargs="?", help="first date, YYYY-MM-DD")
    parser.add_argument("end", nargs="?", help="last date, YYYY-MM-DD")
    parser.add_argument("--weekday", help="keep only these weekdays, e.g. mon,fri")
    parser.add_argument("--step", type=int, default=1, help="emit every n-th day (default 1)")
    parser.add_argument("--count", action="store_true", help="print the total only")
    parser.add_argument("--self-test", action="store_true", help="run built-in checks")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.start or not args.end:
        parser.print_usage()
        return 2

    try:
        dates = list(
            iter_dates(
                parse_date(args.start),
                parse_date(args.end),
                parse_weekdays(args.weekday) if args.weekday else None,
                args.step,
            )
        )
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if args.count:
        print(len(dates))
    else:
        for day in dates:
            print(day.isoformat())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

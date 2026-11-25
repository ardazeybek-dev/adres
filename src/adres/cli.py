"""Command line: ``adres "Caferağa Mah. Moda Cad. No:12 Kadıköy/İstanbul"``."""

from __future__ import annotations

import argparse
import csv
import json
import sys

from . import __version__
from .address import Address, parse

_FIELDS = [f for f in Address().to_dict() if f != "warnings"]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="adres",
        description="Split Turkish addresses into their parts. Reads standard input "
        "(one address per line) when no address is given.",
    )
    p.add_argument("address", nargs="*", help="address text (quote it)")
    out = p.add_mutually_exclusive_group()
    out.add_argument("--line", action="store_true", help="print the cleaned one-line address")
    out.add_argument("--csv", action="store_true", help="print CSV with one column per part")
    p.add_argument("--version", action="version", version=f"adres {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    if args.address:
        lines = [" ".join(args.address)]
    elif sys.stdin.isatty():
        _build_parser().print_usage(sys.stderr)
        return 2
    else:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8-sig")
        lines = [line for line in sys.stdin.read().splitlines() if line.strip()]

    results = [parse(line) for line in lines]
    if args.csv:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["input", *_FIELDS])
        for line, a in zip(lines, results, strict=True):
            d = a.to_dict()
            writer.writerow([line, *("" if d[f] is None else d[f] for f in _FIELDS)])
    elif args.line:
        for a in results:
            print(a.format())
    elif len(results) == 1 and args.address:
        print(json.dumps(results[0].to_dict(), ensure_ascii=False, indent=2))
    else:
        for a in results:
            print(json.dumps(a.to_dict(), ensure_ascii=False))
    return 0

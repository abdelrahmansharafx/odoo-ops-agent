"""CLI: python -m odoo_agent "how many leads are in qualified stage?" """
from __future__ import annotations

import argparse
import sys

from .config import setup_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="odoo_agent", description="Ask business questions over Odoo.")
    parser.add_argument("question", nargs="+", help="the question to ask")
    parser.add_argument("-v", "--verbose", action="store_true", help="log each step (tool, args, duration)")
    args = parser.parse_args(argv)

    if args.verbose:
        setup_logging()
    from .graph import ask  # imported late so --help is instant

    result = ask(" ".join(args.question))
    print(result.answer)
    print(f"\n[tools: {', '.join(result.tools_called) or 'none'} | steps: {result.steps} | "
          f"tokens: {result.input_tokens}+{result.output_tokens} | {result.latency_s}s]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

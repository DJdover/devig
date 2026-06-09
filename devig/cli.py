"""devig — CLI. Strip the vig from a market's odds; print the fair line.

  devig 1.91 1.91                         # two-way decimal odds
  devig -110 -110 --format american
  devig 1.50 4.00 7.00 --method shin      # 3-way, Shin's method
  devig 0.55 0.50 --format prob --out american

Methods: multiplicative (default), additive, power, shin.
"""
from __future__ import annotations

import argparse
import sys

from . import core


def cmd(a):
    r = core.devig([float(x) for x in a.odds], method=a.method, fmt=a.format)
    print(f"method: {r['method']}   vig: {r['vig_pct']:+.2f}% (overround)  hold: {r['hold_pct']:.2f}%   (implied sum "
          f"{sum(r['implied']):.4f})")
    print(f"{'#':>2} {'implied':>9} {'fair_prob':>10} {'fair_dec':>9} {'fair_amer':>10}")
    for i, (imp, q, d, am) in enumerate(zip(r["implied"], r["fair_probs"],
                                            r["fair_decimal"], r["fair_american"]), 1):
        print(f"{i:>2} {imp:>9.4f} {q:>10.4f} {d:>9.3f} {(str(am) if am is not None else 'n/a'):>10}")


def build_parser():
    p = argparse.ArgumentParser(prog="devig",
        description="devig — remove the bookmaker margin and get the fair line. You bring the odds.")
    p.add_argument("odds", nargs="+", help="odds for each outcome of one market")
    p.add_argument("--format", default="decimal", choices=["decimal", "american", "prob"])
    p.add_argument("--method", default="multiplicative", choices=sorted(core.METHODS))
    p.add_argument("--out", default="all", help="(reserved) output format")
    p.set_defaults(fn=cmd)
    return p


def main(argv=None):
    try:
        a = build_parser().parse_args(argv)
        a.fn(a)
    except ValueError as e:
        print(f"devig: error — {e}"); sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""devig tests (stdlib only). Run: python3 tests.py"""
import io, os, sys, contextlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from devig import core
from devig import cli

passed = failed = 0
def check(name, cond):
    global passed, failed
    cond = bool(cond)
    print(f"  {'ok  ' if cond else 'FAIL'} {name}"); passed += cond; failed += (not cond)


def close(a, b, t=1e-6):
    return abs(a - b) < t


# 1 — odds conversions round-trip
check("decimal<->implied", close(core.implied_from_decimal(2.0), 0.5)
      and close(core.decimal_from_implied(0.5), 2.0))
check("american -110 -> decimal 1.909", close(core.decimal_from_american(-110), 1.9090909, 1e-4))
check("american +150 -> decimal 2.5", close(core.decimal_from_american(150), 2.5))
check("decimal 2.5 -> american +150", core.american_from_decimal(2.5) == 150)
check("decimal 1.5 -> american -200", core.american_from_decimal(1.5) == -200)

# 2 — overround / vig from a standard -110/-110 two-way
r = core.devig([-110, -110], method="multiplicative", fmt="american")
check("two-way -110/-110 overround ~4.76%", close(r["vig_pct"], 4.762, 1e-2))
check("two-way -110/-110 hold ~4.55%", close(r["hold_pct"], 4.545, 1e-2))
check("fair probs sum to 1", close(sum(r["fair_probs"]), 1.0))
check("symmetric market -> fair 0.5/0.5", close(r["fair_probs"][0], 0.5) and close(r["fair_probs"][1], 0.5))
check("fair decimal of 0.5 = 2.0", close(r["fair_decimal"][0], 2.0))

# 3 — every method removes the vig (fair sums to 1) and shrinks toward fair
odds = [1.50, 4.00, 7.00]   # 3-way with overround
for m in ("multiplicative", "additive", "power", "shin"):
    fr = core.devig(odds, method=m)
    check(f"{m}: fair probs sum to 1", close(sum(fr["fair_probs"]), 1.0, 1e-6))
    check(f"{m}: removed the vig (fair < implied for the favorite)",
          fr["fair_probs"][0] < fr["implied"][0] + 1e-9)

# 4 — power & shin differ from multiplicative on an asymmetric market (favorite-longshot)
mult = core.devig(odds, "multiplicative")["fair_probs"]
shn = core.devig(odds, "shin")["fair_probs"]
check("shin differs from multiplicative on a skewed market", abs(shn[0] - mult[0]) > 1e-4)

# 5 — input as implied probs directly
r = core.devig([0.55, 0.50], method="multiplicative", fmt="prob")
check("prob input: vig = 5%", close(r["vig_pct"], 5.0, 1e-9))
check("prob input de-vigs to 0.524/0.476", close(r["fair_probs"][0], 0.55 / 1.05, 1e-6))

# 6 — validation
def raises(fn):
    try: fn(); return False
    except ValueError: return True
check("decimal <= 1 rejected", raises(lambda: core.devig([0.9, 2.0])))
check("unknown method rejected", raises(lambda: core.devig([2.0, 2.0], method="nope")))

# 7 — CLI end-to-end
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    cli.main(["-110", "-110", "--format", "american", "--method", "shin"])
out = buf.getvalue()
check("CLI prints vig + fair line", "vig:" in out and "fair_prob" in out and "0.5000" in out)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)

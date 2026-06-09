"""devig.core — remove the bookmaker margin (vig/overround) from odds to get fair
probabilities and fair odds. Pure, stdlib-only, source-agnostic.

You bring a market's odds (decimal, American, or implied probabilities); this returns
the vig and the de-vigged fair line. Four methods, from simplest to most sophisticated:
  multiplicative  proportional shrink   q_i = p_i / S
  additive        equal margin per side q_i = p_i - (S-1)/n   (clip + renorm)
  power           favorite-longshot     q_i = p_i^k,  k s.t. Σ = 1
  shin            insider-trading model  Shin (1992), solves for the insider fraction z

No data of ours, no network, no venue. Just the math.
"""
from __future__ import annotations

import math

# --- odds-format conversions ------------------------------------------------
def implied_from_decimal(d: float) -> float:
    if d <= 1.0:
        raise ValueError(f"decimal odds must be > 1, got {d}")
    return 1.0 / d


def decimal_from_implied(p: float) -> float:
    if not (0.0 < p <= 1.0):
        raise ValueError(f"probability must be in (0,1], got {p}")
    return 1.0 / p


def decimal_from_american(a: float) -> float:
    return (a / 100.0 + 1.0) if a > 0 else (100.0 / (-a) + 1.0)


def american_from_decimal(d: float) -> int:
    if d <= 1.0:
        raise ValueError("decimal odds must be > 1")
    return round((d - 1) * 100) if d >= 2.0 else round(-100 / (d - 1))


def to_probs(odds, fmt="decimal"):
    if fmt == "decimal":
        return [implied_from_decimal(x) for x in odds]
    if fmt == "american":
        return [implied_from_decimal(decimal_from_american(x)) for x in odds]
    if fmt in ("prob", "implied", "probability"):
        return [float(x) for x in odds]
    raise ValueError(f"unknown odds format {fmt!r} (decimal|american|prob)")


def overround(probs) -> float:
    """Σ(implied probs) − 1 — the bookmaker's margin ('vig'/'juice')."""
    return sum(probs) - 1.0


# --- de-vig methods (input: booth implied probs summing to 1+vig) -----------
def multiplicative(p):
    s = sum(p)
    return [x / s for x in p] if s > 0 else list(p)


def additive(p):
    n = len(p)
    adj = (sum(p) - 1.0) / n
    q = [max(1e-12, x - adj) for x in p]
    s = sum(q)
    return [x / s for x in q]


def _power_exponent(p, iters=100):
    def f(k):
        return sum(x ** k for x in p) - 1.0
    a, b = 1.0, 2.0
    while f(b) > 0 and b < 64:
        b *= 1.5
    for _ in range(iters):
        m = (a + b) / 2
        if f(m) > 0:
            a = m
        else:
            b = m
    return (a + b) / 2


def power(p):
    k = _power_exponent(p)
    q = [x ** k for x in p]
    s = sum(q)
    return [x / s for x in q]


def shin(p, iters=100):
    """Shin (1992): models the vig as protection against insider traders, fraction z.
    q_i = [sqrt(z^2 + 4(1-z) p_i^2 / S) - z] / (2(1-z)); solve z so Σ q_i = 1."""
    S = sum(p)

    def qz(z):
        if z >= 1.0:
            z = 1.0 - 1e-9
        return [(math.sqrt(z * z + 4 * (1 - z) * (pi * pi) / S) - z) / (2 * (1 - z)) for pi in p]

    def g(z):
        return sum(qz(z)) - 1.0
    lo, hi = 0.0, 0.5
    if g(lo) <= 0:                 # no vig to remove
        return multiplicative(p)
    while g(hi) > 0 and hi < 0.999:
        hi = (hi + 1.0) / 2
    for _ in range(iters):
        m = (lo + hi) / 2
        if g(m) > 0:
            lo = m
        else:
            hi = m
    q = qz((lo + hi) / 2)
    s = sum(q)
    return [x / s for x in q]


METHODS = {"multiplicative": multiplicative, "additive": additive, "power": power, "shin": shin}


def devig(odds, method="multiplicative", fmt="decimal"):
    """Return the fair line. odds in `fmt`; method in METHODS. Result includes the vig,
    the de-vigged fair probabilities, and fair decimal/American odds."""
    if method not in METHODS:
        raise ValueError(f"unknown method {method!r} (one of {sorted(METHODS)})")
    probs = to_probs(odds, fmt)
    if any(p <= 0 for p in probs):
        raise ValueError("implied probabilities must be > 0")
    fair = METHODS[method](probs)
    s = sum(probs)
    return {
        "method": method,
        "implied": probs,
        "overround": overround(probs),
        "vig_pct": overround(probs) * 100.0,        # Σimplied − 1 (the 'overround')
        "hold_pct": (overround(probs) / s) * 100.0 if s else 0.0,   # margin as % of handle
        "fair_probs": fair,
        "fair_decimal": [1.0 / q if q > 0 else float("inf") for q in fair],
        "fair_american": [american_from_decimal(1.0 / q) if 0 < q < 1 else None for q in fair],
    }

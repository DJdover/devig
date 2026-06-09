# devig

Remove the bookmaker's margin (the **vig**) from a market's odds and get the **fair
line** — the de-vigged probabilities and fair odds. Tiny, dependency-free, and it works
on whatever odds you have: decimal, American, or implied probabilities.

You bring the odds; it does the math. **No network, no venue, no data of ours.**

## Install / run
```
pip install devig
devig 1.91 1.91                      # two-way decimal
devig -110 -110 --format american
devig 1.50 4.00 7.00 --method shin   # 3-way, Shin's method
devig 0.55 0.50 --format prob
```

## Methods
| method | idea |
|---|---|
| `multiplicative` (default) | proportional shrink — `q_i = p_i / Σp` |
| `additive` | equal margin per outcome — `q_i = p_i − (Σp−1)/n` |
| `power` | favorite-longshot aware — `q_i = p_i^k`, k so `Σ = 1` |
| `shin` | Shin (1992) insider-trading model — solves for the insider fraction z |

The four agree on a symmetric market and diverge on skewed ones (favorite-longshot
bias) — `power` and `shin` shade the favorite/longshot differently than a flat
proportional shrink, which is exactly when the choice of method matters.

## What you get
- **overround** (`Σ implied − 1`) and **hold** (`overround / Σ`) — both conventions.
- **fair probabilities** (sum to 1) and **fair odds** (decimal + American).

```
$ devig 1.50 4.00 7.00 --method shin
method: shin   vig: +5.95% (overround)  hold: 5.62%   (implied sum 1.0595)
 #   implied  fair_prob  fair_dec  fair_amer
 1    0.6667     0.6423     1.557       -180
 2    0.2500     0.2315     4.319        332
 3    0.1429     0.1262     7.924        692
```

## Library
```python
import devig
r = devig.devig([1.91, 1.91])          # -> {"fair_probs": [0.5, 0.5], "vig_pct": ...}
devig.shin([0.6667, 0.25, 0.1429])     # raw method on implied probs
devig.decimal_from_american(-110)      # 1.909...
```

## License
MIT. See `LICENSE`.

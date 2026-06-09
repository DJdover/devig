"""devig — remove the bookmaker margin (vig) from odds; get the fair line.

Pure, stdlib-only, source-agnostic. You bring the odds (decimal/American/implied);
it returns the vig and the de-vigged fair probabilities + fair odds. Four methods:
multiplicative, additive, power, shin. No network, no venue, no data of ours. MIT.
"""
__version__ = "0.1.0"
from .core import devig, overround, multiplicative, additive, power, shin, METHODS  # noqa: F401
from .core import (implied_from_decimal, decimal_from_implied, decimal_from_american,  # noqa: F401
                   american_from_decimal, to_probs)

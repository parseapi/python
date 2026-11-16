"""Official ParseAPI client for Python."""

from .city import CityAmbiguityCandidate
from ._client import AsyncParseAPI, ParseAPI, ParseAPIError

__version__ = "1.13.1"
__all__ = ["CityAmbiguityCandidate", "ParseAPI", "AsyncParseAPI", "ParseAPIError", "__version__"]

"""Typed Currency reference responses. Unknown provenance stays None."""

from typing import Dict, List, Literal, Optional, TypedDict


class CurrencyRateDates(TypedDict, total=False):
    base: List[str]
    quote: List[str]

class CurrencyRateUnits(TypedDict, total=False):
    base: str
    quote: str

class _CurrencyOptional(TypedDict, total=False):
    converted: Optional[float]
    stale: bool
    dates: CurrencyRateDates
    units: CurrencyRateUnits

class _CurrencyValues(_CurrencyOptional):
    rate: float
    date: str

class _CurrencyPair(_CurrencyValues):
    base: str
    quote: str

class CurrencyReferenceRate(_CurrencyPair, total=False):
    amount: float

class CurrencyQuote(_CurrencyValues):
    pass

class CurrencyObservation(_CurrencyValues):
    requested_date: str

class CurrencyQuoteObservation(CurrencyObservation):
    quote: str

class CurrencyRateMissing(TypedDict):
    quote: str
    reason: str

class _CurrencyAmountOptional(TypedDict, total=False):
    amount: float

class _CurrencyRatesOptional(_CurrencyAmountOptional, total=False):
    requested_date: str
    missing: List[CurrencyRateMissing]

class CurrencyRates(_CurrencyRatesOptional):
    base: str
    rates: Dict[str, CurrencyQuote]

_CurrencyHistoryCore = TypedDict('_CurrencyHistoryCore', {
    'base': str, 'quote': str, 'from': str, 'to': str,
    'data': List[CurrencyObservation],
})
class _CurrencyHistoryOptional(_CurrencyAmountOptional, total=False):
    interval: str

class CurrencyHistory(_CurrencyHistoryCore, _CurrencyHistoryOptional, total=False):
    missing: List[str]

class CurrencyHistoryMissing(CurrencyRateMissing):
    requested_date: str

_CurrencyRatesHistoryCore = TypedDict('_CurrencyRatesHistoryCore', {
    'base': str, 'quotes': List[str], 'from': str, 'to': str,
    'data': List[CurrencyQuoteObservation],
})
class CurrencyRatesHistory(_CurrencyRatesHistoryCore, _CurrencyHistoryOptional, total=False):
    missing: List[CurrencyHistoryMissing]

class _CurrencyResourceOptional(TypedDict, total=False):
    deep: Dict[str, object]
    unit: Literal["troy_ounce", "indexed_unit"]


class CurrencyResource(_CurrencyResourceOptional):
    currency: str
    name: str
    symbol: Optional[str]
    symbol_native: Optional[str]
    digits: Optional[int]


class CurrencyList(TypedDict):
    data: List[CurrencyResource]







_CurrencyRateSummaryCore = TypedDict('_CurrencyRateSummaryCore', {
    'quote': str, 'from': str, 'to': str, 'average': float, 'min': float, 'max': float,
    'observation_count': int, 'first_date': str, 'last_date': str, 'missing_day_count': int,
})
class CurrencyRateSummary(_CurrencyRateSummaryCore, total=False):
    stale: bool
    units: CurrencyRateUnits

CurrencySummaryMissing = TypedDict('CurrencySummaryMissing', {
    'quote': str, 'from': str, 'to': str, 'reason': str, 'missing_day_count': int,
})
_CurrencyRatesSummaryCore = TypedDict('_CurrencyRatesSummaryCore', {
    'base': str, 'quotes': List[str],
    'from': str, 'to': str, 'interval': str, 'data': List[CurrencyRateSummary],

})

class CurrencyRatesSummary(_CurrencyRatesSummaryCore, total=False):
    missing: List[CurrencySummaryMissing]

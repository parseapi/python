# parseapi

Official parseAPI client for Python.

```bash
pip install parseapi
```

```python
from parseapi import ParseAPI

parse = ParseAPI("your-api-key")
country = parse.country("US")
```

Get a key at [parseapi.com](https://parseapi.com). The client also reads `PARSEAPI_KEY` from the environment.

## Calls

One method per endpoint, named after the route.

```python
parse.ip("8.8.8.8")
parse.ip.self()
parse.email("hello@gmail.com")
parse.vat("DE136695976")
parse.iban("DE89370400440532013000")
parse.npi("1881018208")
parse.phone("+14155552671")
parse.carrier("+14155552671")
parse.caller("+14155552671")
parse.hlr("+14155552671")
parse.postal("SW1A 1AA")
parse.postal("28202", country="US")
parse.postal.nearby("28202", country="US", radius=40)
parse.postal.distance("28202", "10001", country="US")
parse.address("1600 Pennsylvania Ave NW, Washington DC", country="US")
parse.address.search("1600 Pennsylvania", country="US", postal="20500")
parse.company("51 824 753 556", country="AU")
parse.city("charlotte", country="US")
parse.city.id("city_mb8mbqrkz8zb")
parse.city.search("char", country="US", limit=10)
parse.city.nearest(35.2271, -80.8431)
parse.city.nearby("denver", radius=8, unit="mi")
parse.country("US")
parse.country.states("US")
parse.state("colorado")
parse.state("NC", country="US")
parse.state.districts("NC", country="US")
parse.district("37081")
parse.continent("NA")
parse.continent.countries("NA")
parse.bloc("EU")
parse.bloc.countries("EU")
parse.currency("USD")
parse.currency.rate("USD", "EUR")
parse.language("en")
parse.name("BILLY OSHALL")
parse.timezone("America/New_York")
parse.timezone("America/New_York", at="2026-09-05T15:00:00", to="Europe/London")
parse.timezone.at(39.77, -104.9)
parse.date("03/04/2026", format="mdy")
parse.date.today()
parse.holiday("US", year=2026)
parse.holiday.date("US", "2026-12-25")
parse.elevation(35.2271, -80.8431)
parse.point(36.0726, -79.792)
parse.weather(40.7128, -74.006)
parse.domain("example.com")
parse.asn("AS13335")
parse.mac("00:1B:63:84:45:E6")
parse.mx("example.com")
parse.useragent(ua_string)
parse.vin("1HGCM82633A004352")
parse.tariff("8471.30.01.00")
parse.tariff.search("sunglasses")
parse.emoji("rocket")
parse.emoji.search("fire")
```

Responses are plain dicts, exactly the JSON the API returns. `country.states("US")` requests states directly; it does not fetch a country first. Required inputs are positional and optional behavior uses keyword arguments, leaving room for new options without changing existing calls. Reuse a client across calls. Use `with ParseAPI(...) as parse:` or call `parse.close()` when finished.

## Async

Same lookup methods and keyword arguments, with `await`. Use a context manager to close the client when the work is done.

```python
from parseapi import AsyncParseAPI

async with AsyncParseAPI("your-api-key") as parse:
    country = await parse.country("US")
```

## Deep

Pass `deep=True` to include the nested `deep` object with richer fields.

```python
ip = parse.ip("52.94.76.10", deep=True)
ip["deep"]["datacenter"]  # True
```

## Errors

Every non-2xx response raises `ParseAPIError` with `status`, `code`, `docs`, and `request_id`. Branch on `code`.

```python
from parseapi import ParseAPIError

try:
    parse.city("atlantis")
except ParseAPIError as err:
    if err.code == "not_found":
        ...  # no such city
```

Network and decoding failures keep their native error types. Responses such as `valid: false` are successful API answers, not exceptions.

## Options

```python
parse = ParseAPI(
    "your-api-key",
    timeout=10.0,  # timeout for each connect, read, write, or pool phase
)
```

Requires Python 3.9 or later. One dependency (httpx).

Ordinary lookups retry network failures, 429, and 500/502/503/504 responses twice by default. Carrier, caller, HLR, and email or VAT with `deep=True` make one attempt by default. Address with `deep=True` also uses one attempt, reserving the same behavior for future verification.

An explicit client `retries` setting overrides those defaults; `retries=0` always makes one attempt. Another attempt can consume additional usage if the earlier response was lost. Cancelling an async task stops the call and any retry wait. Automatic redirects are disabled.

## Docs

Full field reference for every endpoint: [parseapi.com/docs](https://parseapi.com/docs)

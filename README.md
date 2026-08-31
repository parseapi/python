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
parse.phone("+14155552671")
parse.carrier("+14155552671")
parse.caller("+14155552671")
parse.hlr("+14155552671")
parse.postal("SW1A 1AA")
parse.postal("28202", country="US")
parse.postal.nearby("28202", country="US", radius=40)
parse.postal.distance("28202", "10001", country="US")
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
parse.currency("USD")
parse.currency.rate("USD", "EUR")
parse.language("en")
parse.name("BILLY OSHALL")
parse.timezone("America/New_York")
parse.holiday("US", year=2026)
parse.holiday.date("US", "2026-12-25")
parse.elevation(35.2271, -80.8431)
parse.point(36.0726, -79.792)
parse.weather(40.7128, -74.006)
parse.domain("example.com")
parse.mx("example.com")
parse.useragent(ua_string)
parse.emoji("rocket")
parse.emoji.search("fire")
```

Responses are plain dicts, exactly the JSON the API returns.

## Async

Same surface, `await` everything.

```python
from parseapi import AsyncParseAPI

parse = AsyncParseAPI("your-api-key")
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

## Options

```python
parse = ParseAPI(
    "your-api-key",
    timeout=10.0,  # per-attempt timeout in seconds
    retries=2,     # automatic retries on network errors, 429, and 5xx
)
```

Requires Python 3.9 or later. One dependency (httpx).

## Docs

Full field reference for every endpoint: [parseapi.com/docs](https://parseapi.com/docs)

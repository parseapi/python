import asyncio
import json

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI, ParseAPIError


def make_client(handler, **kwargs):
    calls = []

    def record(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    client = ParseAPI("test_key_123", transport=httpx.MockTransport(record), retries=kwargs.pop("retries", 0), **kwargs)
    return client, calls


def ok(body=None):
    return lambda request: httpx.Response(200, json=body or {})


URL_TABLE = [
    (lambda p: p.ip("8.8.8.8"), "https://api.parseapi.com/ip/8.8.8.8"),
    (lambda p: p.ip.self(), "https://api.parseapi.com/ip"),
    (lambda p: p.ip("8.8.8.8", deep=True), "https://api.parseapi.com/ip/8.8.8.8?deep=true"),
    (lambda p: p.continent("NA"), "https://api.parseapi.com/continent/NA"),
    (lambda p: p.continent.countries("NA"), "https://api.parseapi.com/continent/NA/countries"),
    (lambda p: p.bloc("EU"), "https://api.parseapi.com/bloc/EU"),
    (lambda p: p.bloc.countries("SCHENGEN"), "https://api.parseapi.com/bloc/SCHENGEN/countries"),
    (lambda p: p.country("US"), "https://api.parseapi.com/country/US"),
    (lambda p: p.country.states("US"), "https://api.parseapi.com/country/US/states"),
    (lambda p: p.state("NC", country="US"), "https://api.parseapi.com/state/NC?country=US"),
    (lambda p: p.state("colorado"), "https://api.parseapi.com/state/colorado"),
    (lambda p: p.state.districts("NC", country="US"), "https://api.parseapi.com/state/NC/districts?country=US"),
    (lambda p: p.district("37081"), "https://api.parseapi.com/district/37081"),
    (lambda p: p.city("charlotte", state="NC"), "https://api.parseapi.com/city/charlotte?state=NC"),
    (lambda p: p.city.id("city_mb8mbqrkz8zb"), "https://api.parseapi.com/city/id/city_mb8mbqrkz8zb"),
    (lambda p: p.city.search("char", country="US", limit=10), "https://api.parseapi.com/city?q=char&country=US&limit=10"),
    (lambda p: p.city.nearest(35.2271, -80.8431), "https://api.parseapi.com/city?lat=35.2271&lon=-80.8431"),
    (
        lambda p: p.city.nearby("denver", radius=8, unit="mi", limit=3),
        "https://api.parseapi.com/city/denver/nearby?radius=8&unit=mi&limit=3",
    ),
    (lambda p: p.postal("28202", country="US"), "https://api.parseapi.com/postal/28202?country=US"),
    (lambda p: p.postal("SW1A 1AA"), "https://api.parseapi.com/postal/SW1A%201AA"),
    (
        lambda p: p.postal.nearby("28202", country="US", radius=40, unit="km"),
        "https://api.parseapi.com/postal/28202/nearby?country=US&radius=40&unit=km",
    ),
    (
        lambda p: p.postal.distance("28202", "10001", country="US"),
        "https://api.parseapi.com/postal/28202/distance/10001?country=US",
    ),
    (lambda p: p.email("a@b.com"), "https://api.parseapi.com/email/a%40b.com"),
    (
        lambda p: p.vat("DE136695976", from_vat="IE6388047V", deep=True),
        "https://api.parseapi.com/vat/DE136695976?deep=true&from=IE6388047V",
    ),
    (
        lambda p: p.iban("DE89370400440532013000"),
        "https://api.parseapi.com/iban/DE89370400440532013000",
    ),
    (
        lambda p: p.iban("89370400440532013000", country="DE"),
        "https://api.parseapi.com/iban/89370400440532013000?country=DE",
    ),
    (lambda p: p.phone("+14155552671", deep=True), "https://api.parseapi.com/phone/%2B14155552671?deep=true"),
    (lambda p: p.carrier("+14155552671"), "https://api.parseapi.com/carrier/%2B14155552671"),
    (lambda p: p.caller("4155552671", country="US"), "https://api.parseapi.com/caller/4155552671?country=US"),
    (lambda p: p.hlr("+447712345678"), "https://api.parseapi.com/hlr/%2B447712345678"),
    (lambda p: p.domain("example.com"), "https://api.parseapi.com/domain/example.com"),
    (lambda p: p.mx("example.com"), "https://api.parseapi.com/mx/example.com"),
    (lambda p: p.useragent("TestUA/1.0"), "https://api.parseapi.com/useragent"),
    (lambda p: p.vin("1HGCM82633A004352"), "https://api.parseapi.com/vin/1HGCM82633A004352"),
    (
        lambda p: p.vin("1HGCM82633A004352", deep=True),
        "https://api.parseapi.com/vin/1HGCM82633A004352?deep=true",
    ),
    (lambda p: p.currency("USD"), "https://api.parseapi.com/currency/USD"),
    (lambda p: p.currency.rate("USD", "EUR"), "https://api.parseapi.com/currency/USD/EUR"),
    (
        lambda p: p.currency.rate("USD", "JPY", date="2026-08-28", amount=100),
        "https://api.parseapi.com/currency/USD/JPY?date=2026-08-28&amount=100",
    ),
    (lambda p: p.language("en"), "https://api.parseapi.com/language/en"),
    (lambda p: p.name("Smith, John"), "https://api.parseapi.com/name/Smith%2C%20John"),
    (lambda p: p.timezone("America/New_York"), "https://api.parseapi.com/timezone/America%2FNew_York"),
    (lambda p: p.holiday("US", year=1955), "https://api.parseapi.com/holiday/US?year=1955"),
    (lambda p: p.holiday.date("US", "2026-12-25"), "https://api.parseapi.com/holiday/US/2026-12-25"),
    (lambda p: p.elevation(35.2, -80.8), "https://api.parseapi.com/elevation?lat=35.2&lon=-80.8"),
    (lambda p: p.point(36.0726, -79.792, deep=True), "https://api.parseapi.com/point?lat=36.0726&lon=-79.792&deep=true"),
    (
        lambda p: p.weather(40.7128, -74.006, deep=True),
        "https://api.parseapi.com/weather?lat=40.7128&lon=-74.006&deep=true",
    ),
    (lambda p: p.emoji("rocket"), "https://api.parseapi.com/emoji/rocket"),
    (lambda p: p.emoji.search("fire", limit=20), "https://api.parseapi.com/emoji?q=fire&limit=20"),
]


@pytest.mark.parametrize("invoke,expected", URL_TABLE)
def test_url_mapping(invoke, expected):
    client, calls = make_client(ok())
    invoke(client)
    assert str(calls[0].url) == expected


def test_headers():
    client, calls = make_client(ok())
    client.country("US")
    assert calls[0].headers["X-API-Key"] == "test_key_123"
    assert calls[0].headers["User-Agent"].startswith("parseapi-python/")


def test_useragent_header_override():
    client, calls = make_client(ok())
    client.useragent("Mozilla/5.0 (Test)")
    assert calls[0].headers["User-Agent"] == "Mozilla/5.0 (Test)"


def test_missing_key(monkeypatch):
    monkeypatch.delenv("PARSEAPI_KEY", raising=False)
    with pytest.raises(ValueError, match="PARSEAPI_KEY"):
        ParseAPI()


def test_env_key(monkeypatch):
    monkeypatch.setenv("PARSEAPI_KEY", "env_key_456")
    calls = []

    def record(request):
        calls.append(request)
        return httpx.Response(200, json={})

    client = ParseAPI(transport=httpx.MockTransport(record))
    client.country("US")
    assert calls[0].headers["X-API-Key"] == "env_key_456"


def test_base_url_override():
    calls = []

    def record(request):
        calls.append(request)
        return httpx.Response(200, json={})

    client = ParseAPI("k", base_url="http://localhost:3000/", transport=httpx.MockTransport(record))
    client.country("US")
    assert str(calls[0].url) == "http://localhost:3000/country/US"


def test_error_shape():
    body = {
        "code": "not_found",
        "message": "City not found",
        "docs": "https://parseapi.com/docs#not_found",
        "request_id": "req_abc",
    }
    client, _ = make_client(lambda request: httpx.Response(404, json=body))
    with pytest.raises(ParseAPIError) as excinfo:
        client.city("notarealcityxyz")
    err = excinfo.value
    assert err.status == 404
    assert err.code == "not_found"
    assert str(err) == "City not found"
    assert err.docs == "https://parseapi.com/docs#not_found"
    assert err.request_id == "req_abc"


def test_non_json_error_body():
    client, _ = make_client(lambda request: httpx.Response(400, text="gateway timeout"))
    with pytest.raises(ParseAPIError) as excinfo:
        client.country("US")
    assert excinfo.value.code == "unknown_error"


def test_retry_then_success():
    responses = [httpx.Response(500, json={"code": "server_error", "message": "boom"}), httpx.Response(200, json={"country": "us"})]
    calls = []

    def record(request):
        calls.append(request)
        return responses[len(calls) - 1]

    client = ParseAPI("k", transport=httpx.MockTransport(record), retries=2)
    assert client.country("US")["country"] == "us"
    assert len(calls) == 2


def test_no_retry_on_404():
    calls = []

    def record(request):
        calls.append(request)
        return httpx.Response(404, json={"code": "not_found", "message": "nope"})

    client = ParseAPI("k", transport=httpx.MockTransport(record), retries=2)
    with pytest.raises(ParseAPIError):
        client.country("XX")
    assert len(calls) == 1


def test_gives_up_after_retries():
    calls = []

    def record(request):
        calls.append(request)
        return httpx.Response(429, json={"code": "rate_limited", "message": "slow down"})

    client = ParseAPI("k", transport=httpx.MockTransport(record), retries=2)
    with pytest.raises(ParseAPIError) as excinfo:
        client.country("US")
    assert excinfo.value.code == "rate_limited"
    assert len(calls) == 3


def test_async_client():
    async def run():
        calls = []

        def record(request):
            calls.append(request)
            return httpx.Response(200, json={"iso3": "USA"})

        client = AsyncParseAPI("k", transport=httpx.MockTransport(record))
        result = await client.country("US")
        assert result["iso3"] == "USA"
        ip_result = await client.ip.self(deep=True)
        assert str(calls[1].url) == "https://api.parseapi.com/ip?deep=true"
        await client.close()

    asyncio.run(run())

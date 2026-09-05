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
    (lambda p: p.address("10 rue / Paris", country="FR"),
     "https://api.parseapi.com/address/10%20rue%20%2F%20Paris?country=FR"),
    (lambda p: p.address.search("10 rue", country="FR", postal="75001"),
     "https://api.parseapi.com/address?q=10+rue&country=FR&postal=75001"),
    (lambda p: p.company("51 824 753 556"), "https://api.parseapi.com/company/51%20824%20753%20556"),
    (lambda p: p.date("03/04/2026", format="dmy", to="2026-04-05"),
     "https://api.parseapi.com/date/03%2F04%2F2026?format=dmy&to=2026-04-05"),
    (lambda p: p.date.today(to="2026-12-25"), "https://api.parseapi.com/date?to=2026-12-25"),
    (lambda p: p.timezone.at(0, -0.5, at="2026-09-05T00:00:00Z"),
     "https://api.parseapi.com/timezone?lat=0&lon=-0.5&at=2026-09-05T00%3A00%3A00Z"),
    (lambda p: p.timezone("America/New_York", at="2026-09-05T15:00:00", to="Europe/London"),
     "https://api.parseapi.com/timezone/America%2FNew_York?at=2026-09-05T15%3A00%3A00&to=Europe%2FLondon"),
    (lambda p: p.weather(0, 0, deep=True, date="2026-08-28"),
     "https://api.parseapi.com/weather?lat=0&lon=0&deep=true&date=2026-08-28"),
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
    (lambda p: p.npi("1881018208"), "https://api.parseapi.com/npi/1881018208"),
    (lambda p: p.npi("1881018208", deep=True), "https://api.parseapi.com/npi/1881018208?deep=true"),
    (lambda p: p.phone("+14155552671", deep=True), "https://api.parseapi.com/phone/%2B14155552671?deep=true"),
    (lambda p: p.carrier("+14155552671"), "https://api.parseapi.com/carrier/%2B14155552671"),
    (lambda p: p.caller("4155552671", country="US"), "https://api.parseapi.com/caller/4155552671?country=US"),
    (lambda p: p.hlr("+447712345678"), "https://api.parseapi.com/hlr/%2B447712345678"),
    (lambda p: p.domain("example.com"), "https://api.parseapi.com/domain/example.com"),
    (lambda p: p.asn("AS13335"), "https://api.parseapi.com/asn/AS13335"),
    (lambda p: p.asn("13335"), "https://api.parseapi.com/asn/13335"),
    (lambda p: p.mac("00:1B:63:84:45:E6"), "https://api.parseapi.com/mac/00%3A1B%3A63%3A84%3A45%3AE6"),
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


@pytest.mark.parametrize("invoke,expected", URL_TABLE)
def test_async_url_mapping_matches_sync(invoke, expected):
    async def run():
        calls = []
        def record(request):
            calls.append(request)
            return httpx.Response(200, json={"future_field": {"value": None}})
        async with AsyncParseAPI("test_key", transport=httpx.MockTransport(record), retries=0) as client:
            result = await invoke(client)
        assert len(calls) == 1
        assert str(calls[0].url) == expected
        assert result == {"future_field": {"value": None}}
    asyncio.run(run())


@pytest.mark.parametrize("client_type", [ParseAPI, AsyncParseAPI])
@pytest.mark.parametrize("options", [
    {"retries": -1}, {"retries": 1.5}, {"retries": float("inf")},
    {"timeout": 0}, {"timeout": -1}, {"timeout": True}, {"timeout": float("nan")}, {"timeout": float("inf")},
])
def test_invalid_config_fails_at_construction(client_type, options):
    with pytest.raises(ValueError):
        client_type("test_key", **options)


def test_retry_after_http_date(monkeypatch):
    from parseapi import _client
    monkeypatch.setattr(_client.time, "time", lambda: 1788566400.0)
    assert _client._retry_delay(0, "Sat, 05 Sep 2026 00:00:02 GMT") == 2.0
    assert _client._retry_delay(0, "Sat, 05 Sep 2026 00:01:00 GMT") == 5.0
    assert _client._retry_delay(0, "Fri, 04 Sep 2026 00:00:00 GMT") == 0.0


def test_redirect_is_an_error_not_a_second_request():
    client, calls = make_client(lambda request: httpx.Response(302, headers={"Location": "https://example.com/other"}))
    with client:
        with pytest.raises(ParseAPIError) as error:
            client.country("US")
    assert error.value.status == 302
    assert len(calls) == 1


def test_async_redirect_is_an_error_not_a_second_request():
    async def run():
        calls = []
        def redirect(request):
            calls.append(request)
            return httpx.Response(302, headers={"Location": "https://example.com/other"})
        async with AsyncParseAPI("test_key", transport=httpx.MockTransport(redirect)) as client:
            with pytest.raises(ParseAPIError) as error:
                await client.country("US")
        assert error.value.status == 302
        assert len(calls) == 1
    asyncio.run(run())


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("invoke", [
    lambda p: p.carrier("555-0100"), lambda p: p.caller("555-0100"), lambda p: p.hlr("555-0100"),
    lambda p: p.email("a@example.com", deep=True), lambda p: p.vat("junk", deep=True),
])
def test_paid_checks_default_to_one_attempt(async_mode, invoke):
    calls = []
    def fail(request):
        calls.append(request)
        return httpx.Response(503, json={"code": "unavailable"}, headers={"Retry-After": "0"})
    if async_mode:
        async def run():
            async with AsyncParseAPI("test_key", transport=httpx.MockTransport(fail)) as client:
                with pytest.raises(ParseAPIError):
                    await invoke(client)
        asyncio.run(run())
    else:
        with ParseAPI("test_key", transport=httpx.MockTransport(fail)) as client:
            with pytest.raises(ParseAPIError):
                invoke(client)
    assert len(calls) == 1


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("explicit,deep,expected", [(None, False, 3), (None, True, 1), (1, True, 2), (0, False, 1)])
def test_retry_policy_overrides(async_mode, explicit, deep, expected):
    calls = []
    def fail(request):
        calls.append(request)
        return httpx.Response(503, json={"code": "unavailable"}, headers={"Retry-After": "0"})
    if async_mode:
        async def run():
            async with AsyncParseAPI("test_key", retries=explicit, transport=httpx.MockTransport(fail)) as client:
                with pytest.raises(ParseAPIError):
                    await client.email("a@example.com", deep=deep)
        asyncio.run(run())
    else:
        with ParseAPI("test_key", retries=explicit, transport=httpx.MockTransport(fail)) as client:
            with pytest.raises(ParseAPIError):
                client.email("a@example.com", deep=deep)
    assert len(calls) == expected


def test_async_cancellation_does_not_retry():
    async def run():
        calls = []
        started = asyncio.Event()
        async def transport(request):
            calls.append(request)
            started.set()
            await asyncio.Event().wait()
        async with AsyncParseAPI("test_key", transport=httpx.MockTransport(transport)) as client:
            task = asyncio.create_task(client.country("US"))
            await started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert len(calls) == 1
    asyncio.run(run())

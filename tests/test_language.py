import asyncio
import inspect

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI


OPERATIONS = [
    ("ip", ["8.8.8.8"], {"deep": True}),
    ("ip.self", [], {"deep": True}),
    ("continent", ["EU"], {}),
    ("continent.countries", ["EU"], {}),
    ("bloc.countries", ["EU"], {}),
    ("country", ["DE"], {"deep": True}),
    ("country.states", ["DE"], {}),
    ("state", ["CA"], {"country": "US"}),
    ("state.districts", ["CA"], {"country": "US", "deep": True}),
    ("district", ["37081"], {"country": "US", "state": "NC"}),
    ("city", ["München"], {"country": "DE"}),
    ("city.id", ["city_fixture"], {"deep": True}),
    ("city.search", ["Mün"], {"limit": 2}),
    ("city.nearest", [0, 0], {}),
    ("city.nearby", ["München"], {"radius": 0, "unit": "km"}),
    ("postal", ["SW1A 1AA"], {"country": "GB"}),
    ("postal.nearby", ["28202"], {"country": "US", "radius": 0}),
    ("postal.distance", ["28202", "10001"], {"country": "US"}),
    ("company", ["732829320"], {"country": "FR", "deep": True}),
    ("provider", ["1881018208"], {"deep": True}),
    ("asn", ["AS13335"], {}),
    ("currency", ["USD"], {"deep": True}),
    ("language", ["ja"], {}),
    ("time", ["America/New_York"], {"at": "2026-01-01T12:00", "to": "UTC", "deep": True}),
    ("time.at", [0, 0], {"at": "2026-01-01T12:00Z"}),
    ("timezone", ["UTC"], {"deep": True}),
    ("timezone.at", [0, 0], {"deep": True}),
    ("date", ["03/04/2026"], {"format": "dmy", "to": "2026-05-01", "deep": True}),
    ("date.today", [], {"to": "2026-05-01"}),
    ("point", [0, 0], {"deep": True}),
    ("emoji", ["😀"], {"deep": True}),
    ("emoji.search", ["visage"], {"limit": 2}),
    ("measure.units", [], {"query": "meter", "unit": "m"}),
]


def operation(client, name):
    for part in name.split("."):
        client = getattr(client, part)
    return client


@pytest.mark.parametrize("name,args,options", OPERATIONS)
@pytest.mark.parametrize("async_client", [False, True])
def test_language_is_an_optional_per_request_query(name, args, options, async_client):
    calls = []
    body = {"name": "Nom traduit", "name_local": "Native name", "future": None}

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    if async_client:
        async def run():
            async with AsyncParseAPI("fixture", transport=transport) as client:
                method = operation(client, name)
                assert await method(*args, **options, lang="fr-CA") == body
                await method(*args, **options)
        asyncio.run(run())
    else:
        with ParseAPI("fixture", transport=transport) as client:
            method = operation(client, name)
            assert method(*args, **options, lang="fr-CA") == body
            method(*args, **options)

    assert len(calls) == 2
    assert calls[0].url.path == calls[1].url.path
    assert dict(calls[0].url.params) == {**dict(calls[1].url.params), "lang": "fr-CA"}
    assert "lang" not in calls[1].url.params


def test_language_does_not_change_input_parsing_or_unrelated_operations():
    calls = []
    transport = httpx.MockTransport(lambda request: (calls.append(request), httpx.Response(200, json={}))[1])
    with ParseAPI("fixture", transport=transport) as client:
        client.date("03/04/2026", format="dmy", lang="en-US")
        client.measure("1,5 m", locale="de-DE", to="cm")
        assert calls[0].url.params["format"] == "dmy"
        assert calls[1].url.params["locale"] == "de-DE"
        assert "lang" not in calls[1].url.params
        for name in ["bloc", "currency.rate", "measure", "holiday", "name", "email", "phone", "address"]:
            assert "lang" not in inspect.signature(operation(client, name)).parameters

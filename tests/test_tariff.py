import asyncio

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI, ParseAPIError


@pytest.mark.parametrize("async_client", [False, True])
@pytest.mark.parametrize("extra", [{}, {"lineage": None}, {"lineage": []}, {"lineage": ["Live horses", "Other horses"]}])
def test_tariff_search_preserves_parent_context_and_older_results(async_client, extra):
    body = {"q": "horses & ponies", "revision": "fixture", "lines": [{"hts": "0101.29.00.90", "description": "Other", "general": None, **extra, "future": True}]}

    def respond(request):
        assert request.url.path == "/tariff"
        assert dict(request.url.params) == {"q": "horses & ponies"}
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(respond)
    if async_client:
        async def run():
            async with AsyncParseAPI("test", transport=transport) as client:
                assert await client.tariff.search("horses & ponies") == body
        asyncio.run(run())
    else:
        with ParseAPI("test", transport=transport) as client:
            assert client.tariff.search("horses & ponies") == body

@pytest.mark.parametrize("async_client", [False, True])
def test_tariff_edition_date_roundtrip(async_client):
    edition = "a" * 64
    body = {"hts": "0101", "revision": "fixture", "edition": edition, "date": "2026-09-15", "deep": {"effective_rate": None, "reason": "future_reason", "measures": []}}
    seen = []

    def respond(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json={**body, "date": request.url.params.get("date")})

    transport = httpx.MockTransport(respond)
    if async_client:
        async def run():
            async with AsyncParseAPI("test", transport=transport) as client:
                assert await client.tariff("0101", deep=True, origin="CA", edition=edition, date="2026-09-15") == body
                assert await client.tariff.search("horses", edition=edition, date="2026-09-15") == body
                await client.tariff("0101", edition=edition)
        asyncio.run(run())
    else:
        with ParseAPI("test", transport=transport) as client:
            assert client.tariff("0101", deep=True, origin="CA", edition=edition, date="2026-09-15") == body
            assert client.tariff.search("horses", edition=edition, date="2026-09-15") == body
            client.tariff("0101", edition=edition)
    assert seen == [{"deep": "true", "origin": "CA", "edition": edition, "date": "2026-09-15"}, {"q": "horses", "edition": edition, "date": "2026-09-15"}, {"edition": edition}]

@pytest.mark.parametrize("async_client", [False, True])
def test_tariff_rejects_ignored_selection(async_client):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"revision": "old"}))
    if async_client:
        async def run():
            async with AsyncParseAPI("test", transport=transport) as client:
                with pytest.raises(Exception, match="did not confirm"):
                    await client.tariff("0101", edition="a" * 64)
                with pytest.raises(Exception, match="did not confirm"):
                    await client.tariff.search("horses", date="2026-09-15")
        asyncio.run(run())
    else:
        with ParseAPI("test", transport=transport) as client:
            with pytest.raises(Exception, match="did not confirm"):
                client.tariff("0101", edition="a" * 64)
            with pytest.raises(Exception, match="did not confirm"):
                client.tariff.search("horses", date="2026-09-15")


@pytest.mark.parametrize("async_client", [False, True])
@pytest.mark.parametrize("edition", ["legacy", "", "A" * 64, "a" * 64 + "\n"])
def test_tariff_rejects_invalid_returned_edition(async_client, edition):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"edition": edition, "date": "2026-09-15"}))
    if async_client:
        async def run():
            async with AsyncParseAPI("test", transport=transport) as client:
                for operation, value in [(client.tariff, "0101"), (client.tariff.search, "horses")]:
                    with pytest.raises(ParseAPIError) as error:
                        await operation(value, date="2026-09-15")
                    assert error.value.code == "tariff_selection_mismatch"
                    assert error.value.status == 0
        asyncio.run(run())
    else:
        with ParseAPI("test", transport=transport) as client:
            for operation, value in [(client.tariff, "0101"), (client.tariff.search, "horses")]:
                with pytest.raises(ParseAPIError) as error:
                    operation(value, date="2026-09-15")
                assert error.value.code == "tariff_selection_mismatch"
                assert error.value.status == 0

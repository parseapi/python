import asyncio

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI


@pytest.mark.parametrize("async_mode", [False, True])
def test_contract_pin_survives_retry_self_and_useragent(async_mode):
    calls = []

    def transport(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503, json={"code": "unavailable"}, headers={"Retry-After": "0"})
        return httpx.Response(200, json={})

    if async_mode:
        async def run():
            async with AsyncParseAPI("same-production-key", transport=httpx.MockTransport(transport)) as client:
                await client.country("US")
                await client.ip.self()
                await client.useragent("Custom browser")
        asyncio.run(run())
    else:
        with ParseAPI("same-production-key", transport=httpx.MockTransport(transport)) as client:
            client.country("US")
            client.ip.self()
            client.useragent("Custom browser")

    assert [request.url.path for request in calls] == ["/country/US", "/country/US", "/ip", "/useragent"]
    for request in calls:
        assert request.headers["Parse-Version"] == "2.0.0"
        assert request.headers["X-API-Key"] == "same-production-key"
        assert not request.url.query
    assert calls[-1].headers["User-Agent"] == "Custom browser"

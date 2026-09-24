import asyncio

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI


@pytest.mark.parametrize("async_client", [False, True])
@pytest.mark.parametrize("extra", [
    {}, {"localities": None}, {"localities": []},
    {"localities": [{"city": "SYDNEY", "state": "NSW", "state_name": "New South Wales", "future": True}]},
    {"localities": [{"city": "SYDNEY", "state": "NSW", "state_name": "New South Wales"}, {"city": "HAYMARKET", "state": "NSW", "state_name": "New South Wales"}]},
])
def test_postal_choices_preserve_observation_without_inferring_city(async_client, extra):
    body = {"postal": "2000", "country": "AU", "city": None, **extra}
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    if async_client:
        async def run():
            async with AsyncParseAPI("test", transport=transport) as client:
                assert await client.postal("2000", country="AU") == body
        asyncio.run(run())
    else:
        with ParseAPI("test", transport=transport) as client:
            assert client.postal("2000", country="AU") == body

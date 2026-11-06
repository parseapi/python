import asyncio
import json
from pathlib import Path

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI, __version__


@pytest.mark.parametrize("async_mode", [False, True])
def test_postal_weather_json_and_package_version_header(async_mode):
    fixtures = json.loads((Path(__file__).parent / "fixtures/postal-weather.json").read_text())
    entries = list(fixtures.items())
    calls = []

    def transport(request):
        calls.append(request)
        return httpx.Response(200, json=entries[len(calls) - 1][1])

    async def run_async():
        async with AsyncParseAPI("fixture", transport=httpx.MockTransport(transport)) as client:
            for name, expected in entries:
                actual = await client.weather(0, 0, deep=True) if name.startswith("weather") else await client.postal("10001", country="US", deep=True)
                assert actual == expected

    if async_mode:
        asyncio.run(run_async())
    else:
        with ParseAPI("fixture", transport=httpx.MockTransport(transport)) as client:
            for name, expected in entries:
                actual = client.weather(0, 0, deep=True) if name.startswith("weather") else client.postal("10001", country="US", deep=True)
                assert actual == expected

    assert len(calls) == len(entries)
    assert all(request.headers["User-Agent"] == f"parseapi-python/{__version__}" for request in calls)
    assert fixtures["postal_compact"]["property_tax"] == {"annual_median": 0}
    assert fixtures["weather_current"]["forecast"] is None
    assert fixtures["weather_current"]["alerts"] == []

import asyncio

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI


@pytest.mark.parametrize("asynchronous", [False, True])
def test_city_collections_filter_names_zero_values_cursor_and_legacy_calls(asynchronous):
    seen = []
    first = {"object": "list", "data": [], "has_more": True, "url": "/city", "next_cursor": "opaque+cursor/="}

    def respond(request):
        seen.append(request.url)
        return httpx.Response(200, json=first if len(seen) == 1 else {"object": "list", "data": [], "has_more": False, "url": "/city", "next_cursor": None})

    options = dict(country="JP", min_population=0, max_population=1000000,
                   timezone="Asia/Tokyo", bbox="170,-20,-170,20", sort="population",
                   order="desc", limit=7)

    async def run_async():
        async with AsyncParseAPI("test", transport=httpx.MockTransport(respond)) as client:
            page = await client.city.list(**options)
            assert page == first
            assert await client.city.list(**options, cursor=page["next_cursor"]) == {"object": "list", "data": [], "has_more": False, "url": "/city", "next_cursor": None}
            await client.city.nearby_coordinates(0, 0, radius=3, unit="mi", min_population=0)
            await client.city.search("Wi", page=True, cursor="cursor", sort="name")
            await client.city.nearby("Vienna", page=True, max_population=0)
            await client.city.nearest(0, 0)
            await client.city.search("Wi", page=False)

    if asynchronous:
        asyncio.run(run_async())
    else:
        with ParseAPI("test", transport=httpx.MockTransport(respond)) as client:
            page = client.city.list(**options)
            assert page == first
            assert client.city.list(**options, cursor=page["next_cursor"]) == {"object": "list", "data": [], "has_more": False, "url": "/city", "next_cursor": None}
            client.city.nearby_coordinates(0, 0, radius=3, unit="mi", min_population=0)
            client.city.search("Wi", page=True, cursor="cursor", sort="name")
            client.city.nearby("Vienna", page=True, max_population=0)
            client.city.nearest(0, 0)
            client.city.search("Wi", page=False)

    assert dict(seen[0].params) == {"format": "list", "browse": "true", "country": "JP", "min_population": "0",
                                  "max_population": "1000000", "timezone": "Asia/Tokyo",
                                  "bbox": "170,-20,-170,20", "sort": "population", "order": "desc", "limit": "7"}
    assert seen[1].params["cursor"] == "opaque+cursor/="
    assert dict(seen[2].params) == {"lat": "0", "lon": "0", "nearby": "true", "format": "list", "radius": "3", "unit": "mi", "min_population": "0"}
    assert seen[3].params["page"] == "true"
    assert seen[4].params["max_population"] == "0"
    assert dict(seen[5].params) == {"lat": "0", "lon": "0"}
    assert dict(seen[6].params) == {"q": "Wi"}

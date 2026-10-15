import asyncio

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI


@pytest.mark.parametrize("asynchronous", [False, True])
def test_city_scope_and_matching_options(asynchronous):
    seen = []
    body = {"id": "city_7aj899nvwyku", "grain": "municipality", "parent": None}

    def respond(request):
        seen.append(request.url.params)
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(respond)
    scope = dict(country="JP", state="27", type="city", grain="municipality", hierarchy=True)

    async def run_async():
        async with AsyncParseAPI("test", transport=transport) as client:
            assert await client.city("Sakai", **scope, aliases=True, ambiguity="error") == body
            await client.city.search("Sakai", **scope, aliases=True)
            await client.city.nearest(34.57, 135.48, **scope)
            await client.city.nearby("Sakai", **scope, aliases=True, ambiguity="error")
            await client.city.id("city_7aj899nvwyku", hierarchy=True)

    if asynchronous:
        asyncio.run(run_async())
    else:
        with ParseAPI("test", transport=transport) as client:
            assert client.city("Sakai", **scope, aliases=True, ambiguity="error") == body
            client.city.search("Sakai", **scope, aliases=True)
            client.city.nearest(34.57, 135.48, **scope)
            client.city.nearby("Sakai", **scope, aliases=True, ambiguity="error")
            client.city.id("city_7aj899nvwyku", hierarchy=True)

    for query in seen[:4]:
        for key, value in scope.items():
            assert query[key] == ("true" if value is True else value)
    assert seen[0]["ambiguity"] == "error"
    assert seen[0]["aliases"] == "true"
    assert seen[1]["aliases"] == "true"
    assert "aliases" not in seen[2]
    assert seen[3]["ambiguity"] == "error"
    assert seen[4]["hierarchy"] == "true"


def test_city_disabled_optional_projections_preserve_older_response():
    def respond(request):
        assert "aliases" not in request.url.params
        assert "hierarchy" not in request.url.params
        return httpx.Response(200, json={"id": "city_7aj899nvwyku", "name": "Vienna"})

    with ParseAPI("test", transport=httpx.MockTransport(respond)) as client:
        assert "parent" not in client.city("Vienna", aliases=False, hierarchy=False)

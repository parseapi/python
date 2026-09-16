import asyncio

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI


@pytest.mark.parametrize("async_client", [False, True])
@pytest.mark.parametrize("detail", [
    {"short": "R.J. Smith", "directory": "Smith, Robert James", "initials": "RJS"},
    {"short": None, "directory": None, "initials": None},
    {"gender": None, "salutation": None},
    {},
])
def test_name_formatting_locale_and_nullable_results(async_client, detail):
    calls = []
    body = {"name": "Robert James Smith", "deep": detail}

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    if async_client:
        async def run():
            async with AsyncParseAPI("fixture", transport=transport) as client:
                assert await client.name("Robert James Smith", country="US", deep=True, name_locale="en-GB") == body
                await client.name("Andrea", country="IT", deep=True)
        asyncio.run(run())
    else:
        with ParseAPI("fixture", transport=transport) as client:
            assert client.name("Robert James Smith", country="US", deep=True, name_locale="en-GB") == body
            client.name("Andrea", country="IT", deep=True)
    assert str(calls[0].url) == "https://api.parseapi.com/name/Robert%20James%20Smith?country=US&deep=true&name_locale=en-GB"
    assert str(calls[1].url) == "https://api.parseapi.com/name/Andrea?country=IT&deep=true"

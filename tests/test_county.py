import asyncio
import httpx
import pytest
from parseapi import ParseAPI, AsyncParseAPI


@pytest.mark.parametrize('asynchronous', [False, True])
def test_county_routes_aliases_and_canonical_fields(asynchronous):
    calls = []
    county = {'county': 'E09000033', 'iso_code': 'GB-WSM', 'type': 'district', 'population': 0, 'county_name_local': None}
    listing = {'state': 'ENG', 'country': 'GB', 'counties': [county]}
    def transport(request):
        calls.append(request.url.path)
        assert request.headers['X-API-Version'] == '2.2.0'
        return httpx.Response(200, json=listing if request.url.path.endswith('/counties') else county)
    async def run():
        async with AsyncParseAPI('fixture', transport=httpx.MockTransport(transport)) as client:
            assert await client.county('Westminster', country='GB') == county
            assert await client.district('Westminster', country='GB') == county
            assert await client.state.counties('ENG', country='GB') == listing
            assert await client.state.districts('ENG', country='GB') == listing
    if asynchronous:
        asyncio.run(run())
    else:
        with ParseAPI('fixture', transport=httpx.MockTransport(transport)) as client:
            assert client.county('Westminster', country='GB') == county
            assert client.district('Westminster', country='GB') == county
            assert client.state.counties('ENG', country='GB') == listing
            assert client.state.districts('ENG', country='GB') == listing
    assert calls == ['/county/Westminster', '/county/Westminster', '/state/ENG/counties', '/state/ENG/counties']

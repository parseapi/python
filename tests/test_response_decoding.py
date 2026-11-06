import asyncio
import json
from pathlib import Path
import httpx
from parseapi import ParseAPI, AsyncParseAPI

FIXTURES = Path(__file__).parent / "fixtures" / "response-fixtures"
def test_default_clean_response_and_retry():
    calls = []
    body = (FIXTURES / "clean-timezones.json").read_text()
    def transport(request):
        calls.append(request)
        return httpx.Response(503, headers={"Retry-After":"0"}, json={"code":"unavailable"}) if len(calls)==1 else httpx.Response(200,text=body)
    with ParseAPI("fixture",retries=1,transport=httpx.MockTransport(transport)) as client:
        assert client.time.zones() == json.loads(body)
    assert len(calls)==2
    for request in calls:
        assert "Parse-Response" not in request.headers
        assert request.headers["X-API-Version"]=="2.1.0"
        assert not request.url.params

def test_async_preserves_json_without_metadata():
    async def run():
        calls=[]
        async def transport(request):
            calls.append(request)
            return httpx.Response(200,json={"timezones":[],"future":None,"zero":0,"false":False})
        async with AsyncParseAPI("fixture",transport=httpx.MockTransport(transport)) as client:
            assert await client.time.zones()=={"timezones":[],"future":None,"zero":0,"false":False}
        assert "Parse-Response" not in calls[0].headers
    asyncio.run(run())


def test_seven_numeric_fields_pass_through_sync_and_async():
    country = json.loads('{"country":"US","deep":{"gdp_usd":30769700000000,"gdp_per_capita_usd":90026.5163005744,"population_growth_percent":-0.25,"urban_population_percent":0,"internet_users_percent":null}}')
    weather = json.loads('{"deep":{"minutes":[{"at":"2026-10-27T12:00:00Z","precipitation_rate":1.8,"precipitation_rate_in":0.071,"type":"rain"},{"at":"2026-10-27T12:01:00Z","precipitation_rate":0,"precipitation_rate_in":0},{"at":"2026-10-27T12:02:00Z","precipitation_rate":null,"precipitation_rate_in":null}],"history":{"precipitation":12.3,"precipitation_in":0.484}}}')
    def transport(request):
        return httpx.Response(200, json=country if request.url.path.startswith('/country/') else weather)
    with ParseAPI('fixture', transport=httpx.MockTransport(transport)) as client:
        assert client.country('US', deep=True) == country
        assert client.weather(0, 0, deep=True) == weather
    async def run():
        async with AsyncParseAPI('fixture', transport=httpx.MockTransport(transport)) as client:
            assert await client.country('US', deep=True) == country
            assert await client.weather(0, 0, deep=True) == weather
    asyncio.run(run())

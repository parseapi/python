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
        assert request.headers["Parse-Version"]=="2.0.0"
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

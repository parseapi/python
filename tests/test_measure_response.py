import asyncio
import json
from pathlib import Path

import httpx
from parseapi import AsyncParseAPI, ParseAPI

CASES = json.loads((Path(__file__).parent / 'fixtures/measure-response.json').read_text())

def test_clean_and_legacy_measure_responses_sync_and_async():
    for body in CASES:
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json=body))
        with ParseAPI('fixture', transport=transport) as client:
            assert client.measure(body['measure']) == body
        async def check():
            async with AsyncParseAPI('fixture', transport=transport) as client:
                assert await client.measure(body['measure']) == body
        asyncio.run(check())

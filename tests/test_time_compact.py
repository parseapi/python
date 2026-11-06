import asyncio
import json
from pathlib import Path
import httpx
from parseapi import ParseAPI, AsyncParseAPI

ROWS = json.loads((Path(__file__).parent / 'fixtures/time-compact.json').read_text())

def test_approved_compact_time_sync_and_async():
    def transport_for_rows():
        pending = iter(ROWS)
        def reply(request):
            assert request.headers['X-API-Version'] == '2.1.0'
            return httpx.Response(200, json=next(pending)['body'])
        return httpx.MockTransport(reply)
    with ParseAPI('fixture', retries=0, transport=transport_for_rows()) as client:
        for row in ROWS:
            assert client.time() == row['body']
    async def run():
        async with AsyncParseAPI('fixture', retries=0, transport=transport_for_rows()) as client:
            for row in ROWS:
                assert await client.time() == row['body']
    asyncio.run(run())

import asyncio
import json
from pathlib import Path

import httpx
from parseapi import ParseAPI, AsyncParseAPI

CASES = json.loads((Path(__file__).parent / "fixtures/iso-contract.json").read_text())

def options(sample):
    return {"deep": sample["deep"], **({"country": sample["country"]} if "country" in sample else {})}

def test_iso_contracts_remain_raw_through_existing_sync_transport():
    for sample in CASES:
        calls = []
        def transport(request):
            calls.append(request)
            return httpx.Response(200, json=sample["body"])
        with ParseAPI("fixture", transport=httpx.MockTransport(transport)) as client:
            operation = getattr(client, sample["operation"])
            result = operation(sample["code"], **options(sample))
        assert result == sample["body"]
        assert len(calls) == 1
        assert calls[0].url.path == f"/{sample['operation']}/{sample['code']}"
        assert calls[0].url.params.get("deep") == ("true" if sample["deep"] else None)

def test_iso_contracts_remain_raw_through_existing_async_transport():
    async def run():
        for sample in CASES:
            calls = []
            def transport(request):
                calls.append(request)
                return httpx.Response(200, json=sample["body"])
            async with AsyncParseAPI("fixture", transport=httpx.MockTransport(transport)) as client:
                operation = getattr(client, sample["operation"])
                result = await operation(sample["code"], **options(sample))
            assert result == sample["body"]
            assert len(calls) == 1
    asyncio.run(run())


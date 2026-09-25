import asyncio
import json
from pathlib import Path

import httpx
from parseapi import AsyncParseAPI, ParseAPI

FIXTURE = json.loads(Path(__file__).with_name("bank-fixtures.json").read_text())


def test_bank_checks_passthrough_and_raw_input_sync():
    for body in FIXTURE["records"]:
        calls = []
        def handle(request):
            calls.append(request)
            return httpx.Response(200, json=body)
        with ParseAPI("test_key", transport=httpx.MockTransport(handle)) as client:
            for raw in FIXTURE["inputs"]:
                assert client.bank(raw, deep=True) == body
                assert calls[-1].url.raw_path == b"/bank"
                assert calls[-1].method == "POST"
                assert json.loads(calls[-1].content) == {"iban": raw, "deep": True}
                assert calls[-1].headers["content-type"] == "application/json"
                assert calls[-1].headers["Parse-Version"] == "2.0.0"


def test_bank_checks_passthrough_and_raw_input_async():
    async def run():
        for body in FIXTURE["records"]:
            calls = []
            def handle(request):
                calls.append(request)
                return httpx.Response(200, json=body)
            async with AsyncParseAPI("test_key", transport=httpx.MockTransport(handle)) as client:
                for raw in FIXTURE["inputs"]:
                    assert await client.bank(raw, deep=True) == body
                    assert calls[-1].url.raw_path == b"/bank"
                    assert calls[-1].method == "POST"
                    assert json.loads(calls[-1].content) == {"iban": raw, "deep": True}
                    assert calls[-1].headers["content-type"] == "application/json"
    asyncio.run(run())


def test_bank_domestic_requirements_and_body_retry_sync_and_async():
    async def run(async_mode):
        calls = []
        payload = {"bank_name": None, "checks": {"account_checksum": "not_supported", "future": "future-state"}, "future": True}
        def handle(request):
            calls.append(request)
            return httpx.Response(503, json={}, headers={"Retry-After": "0"}) if len(calls) == 1 else httpx.Response(200, json=payload)
        client = (AsyncParseAPI if async_mode else ParseAPI)("test", retries=1, transport=httpx.MockTransport(handle))
        raw = {"routing": "\t011-000-015", "account": " 00aB-%20\uFEFF"}
        try:
            result = client.bank_us_ach(**raw)
            assert (await result if async_mode else result) == payload
            assert len(calls) == 2
            assert calls[0].content == calls[1].content
            assert json.loads(calls[0].content) == {"format": "us_ach", "country": "US", **raw}
            assert calls[0].url.raw_path == b"/bank"
            result = client.bank_requirements("US", format="future-format")
            assert (await result if async_mode else result) == payload
            assert calls[-1].method == "GET"
            assert not calls[-1].content
            assert dict(calls[-1].url.params) == {"country": "US", "format": "future-format"}
        finally:
            if async_mode: await client.close()
            else: client.close()
    for async_mode in (False, True):
        asyncio.run(run(async_mode))

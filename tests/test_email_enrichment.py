import asyncio

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI


@pytest.mark.parametrize("async_client", [False, True])
@pytest.mark.parametrize("extra", [
    {}, {"deep": {}},
    {"deep": {"first_name": None, "no_reply": None, "tag": None, "mail_provider": None, "status": None, "reason": None}},
    {"deep": {"first_name": "Jane", "no_reply": False, "tag": "news", "mail_provider": "future-provider", "deliverable": True, "catchall": False, "status": "future-status", "reason": "future_reason"}, "future": True},
])
def test_email_enrichment_passes_through(async_client, extra):
    body = {"email": "jane.doe+news@example.com", **extra}
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    if async_client:
        async def run():
            async with AsyncParseAPI("fixture", transport=transport) as client:
                assert await client.email(body["email"], deep=True) == body
        asyncio.run(run())
    else:
        with ParseAPI("fixture", transport=transport) as client:
            assert client.email(body["email"], deep=True) == body

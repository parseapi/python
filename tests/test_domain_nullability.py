import asyncio
import httpx
from parseapi import ParseAPI, AsyncParseAPI


def test_ordinary_domain_preserves_unknown_and_false_sync_and_async():
    for available in [None, False, True]:
        for signing in [{}, {"dnssec": None}, {"dnssec": False}, {"dnssec": True}]:
            body = {"domain": "example.com", "available": available, "deep": {} if available is None else {"registration": {"registered": False} if available else {"registered": True, **signing}}}
            calls = []
            def transport(request):
                calls.append(request)
                return httpx.Response(200, json=body)
            with ParseAPI("fixture", transport=httpx.MockTransport(transport)) as client:
                assert client.domain("example.com", deep=True) == body
            assert len(calls) == 1
            assert str(calls[0].url) == "https://api.parseapi.com/domain/example.com?deep=true"
            async def run():
                async with AsyncParseAPI("fixture", transport=httpx.MockTransport(transport)) as client:
                    assert await client.domain("example.com", deep=True) == body
            asyncio.run(run())
            assert len(calls) == 2
            assert all(request.headers["X-API-Version"] == "2.1.0" for request in calls)

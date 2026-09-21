import asyncio
import json
import httpx
from parseapi import ParseAPI, AsyncParseAPI

RECORDS = json.loads(r'''
[
  {
    "domain": "xn--bcher-kva.example",
    "url": "https://xn--bcher-kva.example/",
    "checked_at": null,
    "scope": "homepage",
    "pages": 0,
    "partial": null,
    "cms": null,
    "servers": null,
    "frameworks": null,
    "ecommerce": null,
    "analytics": null,
    "chat": null,
    "payments": null,
    "hosting": null,
    "future": true
  },
  {
    "domain": "xn--bcher-kva.example",
    "url": "https://xn--bcher-kva.example/",
    "checked_at": "2026-09-21T12:00:00Z",
    "scope": "homepage",
    "pages": 1,
    "partial": true,
    "cms": [],
    "servers": [],
    "frameworks": [],
    "ecommerce": [],
    "analytics": [],
    "chat": [],
    "payments": [],
    "hosting": [],
    "deep": {},
    "future": true
  },
  {
    "domain": "xn--bcher-kva.example",
    "url": "https://xn--bcher-kva.example/",
    "checked_at": "2026-09-21T12:00:00Z",
    "scope": "homepage",
    "pages": 1,
    "partial": true,
    "cms": [
      {
        "technology": "wordpress",
        "name": "WordPress",
        "version": "6.8.2"
      }
    ],
    "servers": [
      {
        "technology": "nginx",
        "name": "nginx",
        "version": null
      }
    ],
    "frameworks": [
      {
        "technology": "react",
        "name": "React",
        "version": null
      }
    ],
    "ecommerce": [],
    "analytics": [],
    "chat": [],
    "payments": [],
    "hosting": [],
    "future": true
  },
  {
    "domain": "xn--bcher-kva.example",
    "url": "https://xn--bcher-kva.example/",
    "checked_at": "2026-09-21T12:00:00Z",
    "scope": "site",
    "pages": 6,
    "partial": false,
    "cms": [
      {
        "technology": "wordpress",
        "name": "WordPress",
        "version": "6.8.2"
      },
      {
        "technology": "ghost",
        "name": "Ghost",
        "version": null
      }
    ],
    "servers": [
      {
        "technology": "nginx",
        "name": "nginx",
        "version": null
      },
      {
        "technology": "apache",
        "name": "Apache",
        "version": null
      }
    ],
    "frameworks": [
      {
        "technology": "nextjs",
        "name": "Next.js",
        "version": "15.0.0",
        "future": true
      },
      {
        "technology": "react",
        "name": "React",
        "version": null
      }
    ],
    "ecommerce": [
      {
        "technology": "woocommerce",
        "name": "WooCommerce",
        "version": null
      }
    ],
    "analytics": [
      {
        "technology": "google-analytics",
        "name": "Google Analytics",
        "version": null
      }
    ],
    "chat": [
      {
        "technology": "intercom",
        "name": "Intercom",
        "version": null
      }
    ],
    "payments": [
      {
        "technology": "stripe",
        "name": "Stripe",
        "version": null
      }
    ],
    "hosting": [
      {
        "technology": "vercel",
        "name": "Vercel",
        "version": null
      }
    ],
    "future": true
  },
  {
    "domain": "xn--bcher-kva.example",
    "url": "https://xn--bcher-kva.example/",
    "checked_at": "2026-09-21T12:00:00Z",
    "scope": "site",
    "pages": 3,
    "partial": true,
    "cms": [],
    "servers": [],
    "frameworks": [
      {
        "technology": "nextjs",
        "name": "Next.js",
        "version": null,
        "future": true
      }
    ],
    "ecommerce": [],
    "analytics": [],
    "chat": [],
    "payments": [],
    "hosting": [],
    "deep": {},
    "future": true
  },
  {
    "domain": "xn--bcher-kva.example",
    "url": "https://xn--bcher-kva.example/",
    "checked_at": null,
    "scope": "site",
    "pages": 0,
    "partial": null,
    "cms": null,
    "servers": null,
    "frameworks": null,
    "ecommerce": null,
    "analytics": null,
    "chat": null,
    "payments": null,
    "hosting": null,
    "deep": {},
    "future": true
  }
]
''')

def test_stack_sync_and_async_preserve_site_inventory_shapes_and_encoding():
    async def run_async(record):
        calls = []
        async def handler(request):
            calls.append(request)
            return httpx.Response(200, json=record)
        async with AsyncParseAPI("test_key", transport=httpx.MockTransport(handler)) as client:
            assert await client.stack("bücher.example", deep=True, pretty=True) == record
            assert await client.stack("example.com") == record
        check(calls)
    for record in RECORDS:
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json=record)
        with ParseAPI("test_key", transport=httpx.MockTransport(handler)) as client:
            assert client.stack("bücher.example", deep=True, pretty=True) == record
            assert client.stack("example.com") == record
        check(calls)
        asyncio.run(run_async(record))

def check(calls):
    assert str(calls[0].url) == "https://api.parseapi.com/stack/b%C3%BCcher.example?deep=true&pretty=true"
    assert str(calls[1].url) == "https://api.parseapi.com/stack/example.com"
    assert all(request.headers["Parse-Version"] == "2.0.0" for request in calls)

def test_stack_deadline_defaults_and_explicit_sync_async_settings():
    for explicit in [None, 10.0, 1.2, 45.0]:
        expected = 35.0 if explicit is None else explicit
        calls = []
        def handler(request):
            calls.append(request.extensions["timeout"])
            return httpx.Response(200, json={**RECORDS[0], "deep": {}})
        with ParseAPI("test_key", timeout=explicit, transport=httpx.MockTransport(handler)) as client:
            assert client.stack("example.com")["deep"] == {}
            client.domain("example.com")
            client.stack("example.com", deep=True)
        assert [call["read"] for call in calls] == [expected, 10.0 if explicit is None else explicit, expected]
        assert all(len(set(call.values())) == 1 for call in calls)
        async def run():
            calls.clear()
            async with AsyncParseAPI("test_key", timeout=explicit, transport=httpx.MockTransport(handler)) as client:
                assert (await client.stack("example.com"))["deep"] == {}
                await client.domain("example.com")
                await client.stack("example.com", deep=True)
            assert [call["read"] for call in calls] == [expected, 10.0 if explicit is None else explicit, expected]
        asyncio.run(run())

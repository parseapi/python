import asyncio
import json

import httpx
import pytest
from parseapi import AsyncParseAPI, ParseAPI


def test_sync_and_async_emoji_catalog_and_text_body():
    async def run(async_mode):
        calls = []
        payload = {"total": 2, "emojis": [{"emoji": "👍🏿", "name": "thumbs up", "shortcodes": [], "category": None, "occurrences": 2, "positions": [{"start": 2, "end": 6}, {"start": 7, "end": 11}], "deep": {"base": "👍", "variants": [{"emoji": "👍🏿", "tones": ["dark"]}]} }], "future": True}
        def handle(request):
            calls.append(request)
            return httpx.Response(200, json=payload)
        client_type = AsyncParseAPI if async_mode else ParseAPI
        client = client_type("test", transport=httpx.MockTransport(handle))
        async def call(method, *args, **kwargs):
            value = method(*args, **kwargs)
            return await value if async_mode else value
        assert await call(client.emoji, ":cat:", shortcode_source="github") == payload
        await call(client.emoji.search, "face", category="Smileys & Emotion", version="17.0", max_version="18.0", include_skin_tones=False, offset=0)
        await call(client.emoji.browse, category="People & Body", include_skin_tones=False, offset=2)
        await call(client.emoji.categories)
        assert await call(client.emoji.parse, "x 👍🏿 👍🏿", deep=True, lang="fr") == payload
        assert calls[0].url.path == "/emoji/:cat:"
        assert dict(calls[0].url.params) == {"shortcode_source": "github"}
        assert dict(calls[1].url.params) == {"q": "face", "category": "Smileys & Emotion", "version": "17.0", "max_version": "18.0", "include_skin_tones": "false", "offset": "0"}
        assert dict(calls[2].url.params) == {"category": "People & Body", "include_skin_tones": "false", "offset": "2"}
        assert calls[3].url.path == "/emoji/categories" and not calls[3].url.params
        assert calls[4].url.path == "/emoji/parse" and calls[4].method == "POST"
        assert json.loads(calls[4].content) == {"text": "x 👍🏿 👍🏿"}
        assert dict(calls[4].url.params) == {"deep": "true", "lang": "fr"}
        assert calls[4].headers["Parse-Version"] == "2.0.0"
        if async_mode:
            await client.close()
        else:
            client.close()
    asyncio.run(run(False))
    asyncio.run(run(True))

def test_sync_async_emoji_download_and_metadata():
    from pathlib import Path
    bundle = json.loads((Path(__file__).parent / 'fixtures/emoji-catalog.json').read_text())
    async def run(async_mode):
        calls = []
        def handle(request):
            calls.append(request)
            return httpx.Response(200, json=bundle['metadata'] if request.url.path == '/emoji/metadata' else bundle)
        client = (AsyncParseAPI if async_mode else ParseAPI)('test', transport=httpx.MockTransport(handle))
        async def call(method, **kwargs):
            value = method(**kwargs)
            return await value if async_mode else value
        result = await call(client.emoji.catalog, deep=False, include_skin_tones=False, lang='fr', max_version='17.0')
        assert result['forms']['❤'] == '❤️'
        assert result['emojis'][0]['deep']['artwork'] == {}
        assert dict(calls[0].url.params) == {'deep':'false','include_skin_tones':'false','lang':'fr','max_version':'17.0'}
        await call(client.emoji.catalog)
        assert dict(calls[1].url.params) == {'deep':'true'}
        assert (await call(client.emoji.metadata))['total'] == 1
        assert calls[2].url.path == '/emoji/metadata' and not calls[2].url.params
        if async_mode: await client.close()
        else: client.close()
    asyncio.run(run(False))
    asyncio.run(run(True))



def test_sync_async_private_conversion():
    async def run(async_mode):
        calls=[]
        def handle(request):
            calls.append(request)
            return httpx.Response(200,json={"text":"🚀","unresolved":[]})
        client=(AsyncParseAPI if async_mode else ParseAPI)('test',transport=httpx.MockTransport(handle))
        result=client.emoji.convert(':rocket:',direction='to_emoji',shortcode_source='github')
        if async_mode: result=await result
        assert result['text']=='🚀'
        assert len(calls)==1 and calls[0].method=='POST'
        assert json.loads(calls[0].content)=={'text':':rocket:'}
        assert dict(calls[0].url.params)=={'direction':'to_emoji','shortcode_source':'github'}
        if async_mode: await client.close()
        else: client.close()
    asyncio.run(run(False));asyncio.run(run(True))


def test_actual_keyed_artwork_sync_and_async():
    from pathlib import Path
    fixture = json.loads((Path(__file__).parent / 'fixtures/emoji-artwork.json').read_text())
    async def run():
        for mode in (False, True):
            cls = AsyncParseAPI if mode else ParseAPI
            client = cls('test', transport=httpx.MockTransport(lambda request: httpx.Response(200, json=fixture['emoji'])))
            result = await client.emoji('rocket', deep=True) if mode else client.emoji('rocket', deep=True)
            artwork = result['deep']['artwork']
            assert list(artwork) == ['noto', 'twemoji', 'openmoji']
            assert artwork['openmoji']['svg'] == 'https://cdn.parseapi.com/emoji/openmoji/17.0.0/1f680.svg'
            assert artwork['openmoji']['png']['72'] == 'https://cdn.parseapi.com/emoji/openmoji/17.0.0/72/1f680.png'
            if mode: await client.close()
            else: client.close()
    asyncio.run(run())

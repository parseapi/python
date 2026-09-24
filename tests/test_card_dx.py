import asyncio
from urllib.parse import quote

import httpx
import pytest

from parseapi import AsyncParseAPI, ParseAPI, ParseAPIError
from parseapi import _client


def test_prefix_guards_match_server_and_preserve_accepted_input():
    calls = []
    def transport(request):
        calls.append(request)
        return httpx.Response(200, json={})
    invalid = ['', '12345', '123456789012', '4242424242424242', '００１２３４', '00\u00a01234', '00\v1234', '00%201234', '00+1234', '00/1234', '00_1234', ' '*59+'001234', 123456, None]
    valid = ['001234', '00123456789', '00 1234-56', '00\t12\r34\n-56', ' '*58+'001234']
    with ParseAPI('fixture', transport=httpx.MockTransport(transport)) as client:
        for value in invalid:
            with pytest.raises(ValueError, match='^parseapi: Card requires a string containing 6 to 11 digits. Send a prefix only.$'):
                client.card(value)
        assert not calls
        for value in valid:
            client.card(value)
            assert str(calls[-1].url) == 'https://api.parseapi.com/card/'+quote(value, safe='')
    calls.clear()
    async def run():
        async with AsyncParseAPI('fixture', transport=httpx.MockTransport(transport)) as client:
            for value in invalid:
                with pytest.raises(ValueError):
                    await client.card(value)
            assert not calls
            for value in valid:
                await client.card(value)
                assert str(calls[-1].url) == 'https://api.parseapi.com/card/'+quote(value, safe='')
    asyncio.run(run())


@pytest.mark.parametrize('header', ['60', '9'*400, 'Sat, 05 Sep 2026 00:01:00 GMT'])
def test_long_retry_after_declines_without_sleep_sync_and_async(monkeypatch, header):
    monkeypatch.setattr(_client.time, 'time', lambda: 1788566400.0)
    def no_sleep(delay):
        pytest.fail('long Retry-After must not sleep')
    async def no_async_sleep(delay):
        pytest.fail('long Retry-After must not sleep')
    monkeypatch.setattr(_client.time, 'sleep', no_sleep)
    monkeypatch.setattr(asyncio, 'sleep', no_async_sleep)
    calls = []
    def transport(request):
        calls.append(request)
        return httpx.Response(429, headers={'Retry-After': header}, json={'code':'rate_limited','message':'Wait for reset','docs':'https://parseapi.com/docs','request_id':'req_fixture'})
    def check(error):
        assert error.status == 429 and error.code == 'rate_limited'
        assert str(error) == 'Wait for reset'
        assert error.docs == 'https://parseapi.com/docs' and error.request_id == 'req_fixture'
        assert error.retry_after == header
    with ParseAPI('fixture', transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(ParseAPIError) as error:
            client.card('001234')
        check(error.value)
    assert len(calls) == 1
    calls.clear()
    async def run():
        async with AsyncParseAPI('fixture', transport=httpx.MockTransport(transport)) as client:
            with pytest.raises(ParseAPIError) as error:
                await client.card('001234')
            check(error.value)
    asyncio.run(run())
    assert len(calls) == 1


@pytest.mark.parametrize('header,delay', [('0',0),('2',2),('Sat, 05 Sep 2026 00:00:02 GMT',2),(None,0.1),('nonsense',0.1),('-1',0.1),('NaN',0.1),('Infinity',0.1),('1e999',0.1)])
def test_short_missing_malformed_headers_and_exhausted_metadata(monkeypatch, header, delay):
    monkeypatch.setattr(_client.time, 'time', lambda:1788566400.0)
    monkeypatch.setattr(_client.random, 'random', lambda:0.4)
    waits=[];calls=[]
    monkeypatch.setattr(_client.time, 'sleep', lambda value:waits.append(value))
    async def sleep(value): waits.append(value)
    monkeypatch.setattr(asyncio, 'sleep', sleep)
    def transport(request):
        calls.append(request)
        return httpx.Response(429, headers={} if header is None else {'Retry-After':header}, json={'code':'rate_limited'})
    with ParseAPI('fixture', retries=1, transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(ParseAPIError) as error: client.card('001234')
        assert error.value.retry_after == header
    assert len(calls)==2 and waits==[delay]
    calls.clear();waits.clear()
    async def run():
        async with AsyncParseAPI('fixture', retries=1, transport=httpx.MockTransport(transport)) as client:
            with pytest.raises(ParseAPIError) as error: await client.card('001234')
            assert error.value.retry_after == header
    asyncio.run(run())
    assert len(calls)==2 and waits==[delay]


def test_error_constructor_remains_compatible_and_disabled_retry_keeps_header():
    assert ParseAPIError(400,'invalid_request','Input',None,None).retry_after is None
    with ParseAPI('fixture', retries=0, transport=httpx.MockTransport(lambda _:httpx.Response(429,headers={'Retry-After':'2'},json={'code':'rate_limited'}))) as client:
        with pytest.raises(ParseAPIError) as error:client.card('001234')
        assert error.value.retry_after == '2'


def test_large_retry_counts_keep_full_jitter_within_budget(monkeypatch):
    monkeypatch.setattr(_client.random, 'random', lambda:0.4)
    assert _client._retry_delay(100000, None) == 2.0

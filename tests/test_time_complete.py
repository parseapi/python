import asyncio
import httpx
import pytest
from parseapi import ParseAPI, AsyncParseAPI

@pytest.mark.parametrize('async_mode', [False, True])
def test_targets_validate_before_dispatch_and_preserve_observations(async_mode):
    calls = []
    payload = {'targets': None}
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=payload)
    async def run():
        client_type = AsyncParseAPI if async_mode else ParseAPI
        client = client_type('fixture', transport=httpx.MockTransport(handler), retries=0)
        async def invoke(operation, *args, **kwargs):
            result = operation(*args, **kwargs)
            return await result if async_mode else result
        try:
            for targets in [[], [''], ['  '], ['UTC,UTC'], ['UTC'] * 11, [None], 'UTC']:
                for method, args in [(client.time, ['UTC']), (client.time.at, [0, 0])]:
                    with pytest.raises(ValueError):
                        await invoke(method, *args, targets=targets)
            with pytest.raises(ValueError):
                await invoke(client.time, 'UTC', targets=['UTC'], to='UTC')
            assert calls == []
            for value in [None, [], [{'timezone': 'UTC', 'unix': 0}, {'timezone': 'UTC', 'unix': 0}]]:
                payload['targets'] = value
                assert await invoke(client.time, 'UTC', targets=['UTC', 'Asia/Tokyo', 'UTC']) == payload
                assert calls[-1].url.params['targets'] == 'UTC,Asia/Tokyo,UTC'
        finally:
            if async_mode:
                await client.close()
            else:
                client.close()
    asyncio.run(run())


@pytest.mark.parametrize('async_mode', [False, True])
def test_reserved_time_source_does_not_call_discovery(async_mode):
    calls = []
    async def run():
        cls = AsyncParseAPI if async_mode else ParseAPI
        parse = cls('fixture', transport=httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(200, json={})))
        try:
            for zone in ['zones', 'help', ' ZONES ', 'Help']:
                with pytest.raises(ValueError, match='IANA timezone ID'):
                    result = parse.time(zone)
                    if async_mode: await result
            assert calls == []
        finally:
            if async_mode: await parse.close()
            else: parse.close()
    asyncio.run(run())

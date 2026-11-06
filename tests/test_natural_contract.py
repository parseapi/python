import asyncio
import json
import httpx
import pytest
from parseapi import ParseAPI, AsyncParseAPI, ParseAPIError

@pytest.mark.parametrize('asynchronous', [False, True])
def test_explicit_verification_and_basic_email_use_21(asynchronous):
    calls = []
    result = {'email': 'a+b@example.com', 'valid': True, 'deliverable': False, 'catchall': None, 'future': 0}
    def handler(request):
        calls.append(request)
        assert request.headers['X-API-Version'] == '2.1.0'
        return httpx.Response(200, json=result)
    async def run_async():
        async with AsyncParseAPI('fixture', transport=httpx.MockTransport(handler)) as client:
            await client.email(result['email'])
            assert await client.email_verify(result['email']) == result
            assert await client.email(result['email'], deep=True) == result
    if asynchronous:
        asyncio.run(run_async())
    else:
        with ParseAPI('fixture', transport=httpx.MockTransport(handler)) as client:
            client.email(result['email'])
            assert client.email_verify(result['email']) == result
            assert client.email(result['email'], deep=True) == result
    assert calls[0].method == 'GET' and calls[0].url.path == '/email/a+b@example.com'
    for request in calls[1:]:
        assert request.method == 'POST' and request.url.path == '/email/verify'
        assert not request.url.query and json.loads(request.content) == {'email': result['email']}
    assert 'deep' not in result

@pytest.mark.parametrize('asynchronous', [False, True])
def test_verification_does_not_retry_uncertain_failure(asynchronous):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(503, json={'code': 'unavailable', 'message': 'Unavailable'}, headers={'Retry-After': '0'})
    async def run_async():
        async with AsyncParseAPI('fixture', transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(ParseAPIError):
                await client.email_verify('person@example.com')
    if asynchronous:
        asyncio.run(run_async())
    else:
        with ParseAPI('fixture', transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(ParseAPIError):
                client.email_verify('person@example.com')
    assert len(calls) == 1

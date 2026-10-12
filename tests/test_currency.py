import asyncio
import inspect
import json
from pathlib import Path

import httpx
import pytest
from parseapi import AsyncParseAPI, ParseAPI, ParseAPIError, CurrencyQuote, CurrencyRates, CurrencyReferenceRate, CurrencyResource

FIXTURE = json.loads((Path(__file__).parent / 'fixtures/currency-reference.json').read_text())


@pytest.mark.parametrize('async_mode', [False, True])
def test_currency_old_calls_and_new_json_surface(async_mode):
    async def run():
        calls = []
        def handle(request):
            calls.append(request)
            path = request.url.path
            if path == '/currency/sources': value = FIXTURE['sources']
            elif path.endswith('/rates/history'): value = FIXTURE['rates_history']
            elif path.endswith('/rates'): value = FIXTURE['batch']
            elif path.endswith('/history'): value = FIXTURE['history']
            elif path.endswith('/ROL'): value = FIXTURE['pair']
            elif path.endswith('/EUR'): value = {'base':'USD','quote':'EUR','rate':0.9,'date':'2026-10-09','converted':0, 'future': True}
            else: value = {'currency':'SLE','name':'Leone','symbol':None,'symbol_native':None,'digits':2}
            return httpx.Response(200, json=value)
        client = (AsyncParseAPI if async_mode else ParseAPI)('test', transport=httpx.MockTransport(handle), retries=0)
        async def call(method, *args, **kwargs):
            result = method(*args, **kwargs)
            return await result if async_mode else result
        try:
            old_rate = client.currency.rate
            assert (await call(client.currency, 'SLE'))['symbol'] is None
            assert (await call(old_rate, 'USD', quote_currency='EUR', date='2026-10-09', amount=0))['converted'] == 0
            assert dict(calls[1].url.params) == {'date':'2026-10-09','amount':'0'}
            result = await call(client.currency.rate, 'USD', 'ROL', date='2004-01-05', amount=1)
            assert result == FIXTURE['pair'] and result['converted'] is None
            assert result['date'] == '2004-01-05'
            quotes = ('EUR','JPY','KPW')
            assert await call(client.currency.rates, 'USD', quotes, date='2026-10-09', amount=0) == FIXTURE['batch']
            assert dict(calls[3].url.params) == {'quotes':'EUR,JPY,KPW','date':'2026-10-09','amount':'0'}
            assert await call(client.currency.history, 'USD','EUR','2026-10-09','2026-10-10', amount=-0.67) == FIXTURE['history']
            result = await call(client.currency.rates_history, 'USD', quotes,'2026-10-09','2026-10-10', amount=0)
            assert result == FIXTURE['rates_history']
            assert result['data'][2]['requested_date'] == '2026-10-10' and result['data'][2]['date'] == '2026-10-09'
            assert [row['quote'] for row in result['missing']] == ['KPW','KPW']
            assert calls[4].url.path == '/currency/USD/EUR/history'
            assert calls[5].url.path == '/currency/USD/rates/history'
            assert dict(calls[5].url.params) == {'quotes':'EUR,JPY,KPW','from':'2026-10-09','to':'2026-10-10','amount':'0'}
            for request in calls:
                assert request.method == 'GET' and request.headers['X-API-Key'] == 'test' and request.headers['Parse-Version'] == '2.0.0'
            assert not client._http.follow_redirects
        finally:
            if async_mode: await client.close()
            else: client.close()
    asyncio.run(run())




@pytest.mark.parametrize('async_mode', [False, True])
def test_currency_export_errors_and_invalid_lists_still_fail_honestly(async_mode):
    async def run():
        calls = []
        def handle(request):
            calls.append(request)
            return httpx.Response(429, json={'code':'rate_limited','message':'Wait','request_id':'req_currency'}, headers={'Retry-After':'60'})
        client = (AsyncParseAPI if async_mode else ParseAPI)('test', transport=httpx.MockTransport(handle))
        async def call(method, *args, **kwargs):
            result = method(*args, **kwargs)
            return await result if async_mode else result
        try:
            with pytest.raises(ParseAPIError) as error:
                await call(client.currency.history,'USD','JPY','2026-10-09','2026-10-10')
            assert error.value.status == 429 and error.value.code == 'rate_limited' and error.value.request_id == 'req_currency' and error.value.retry_after == '60'
            assert len(calls) == 1
            for quotes in ([], ['USD','usd'], ['US'], ['USD/JPY'], ['EUR']*51, 'EUR,JPY'):
                with pytest.raises(ValueError): await call(client.currency.rates, 'USD', quotes)
            assert len(calls) == 1
        finally:
            if async_mode: await client.close()
            else: client.close()
    asyncio.run(run())


def test_currency_new_sync_async_calling_surfaces_match_and_types_are_exported():
    sync, async_ = ParseAPI('test'), AsyncParseAPI('test')
    try:
        for name in ('list','rate','rates','history','rates_history','rates_summary'):
            assert inspect.signature(getattr(sync.currency,name)) == inspect.signature(getattr(async_.currency,name))
        assert 'converted' in CurrencyReferenceRate.__optional_keys__
        assert CurrencyRates.__required_keys__ == {'base', 'rates'}
        assert CurrencyQuote.__required_keys__ == {'rate', 'date'}
        assert 'unit' in CurrencyResource.__optional_keys__ and 'unit' not in CurrencyResource.__required_keys__
    finally:
        sync.close()
        asyncio.run(async_.close())




CATALOG_FIXTURE = json.loads((Path(__file__).parent / 'fixtures/currency-catalog.json').read_text())
@pytest.mark.parametrize('async_mode', [False, True])
def test_currency_all_quotes_catalog_(async_mode):
    async def run():
        calls = []
        def handle(request):
            calls.append(request)
            if request.url.path == '/currency': value = CATALOG_FIXTURE['currencies'] if 'country' in request.url.params else FIXTURE['currencies']
            else: value = FIXTURE['batch']
            return httpx.Response(200, json=value)
        client = (AsyncParseAPI if async_mode else ParseAPI)('test', transport=httpx.MockTransport(handle), retries=0)
        async def call(method, *args, **kwargs):
            result = method(*args, **kwargs); return await result if async_mode else result
        try:
            rates = await call(client.currency.rates, 'USD')
            assert rates['rates']['EUR']['rate'] == FIXTURE['batch']['rates']['EUR']['rate']
            assert 'quote' not in rates['rates']['EUR'] and 'quotes' not in calls[-1].url.params
            assert {'object', 'data', 'has_more', 'url'}.isdisjoint(rates)
            catalog = await call(client.currency.list, q='gold', country='UA', deep=True, pretty=True, lang='fr')
            assert catalog['data'] == []
            assert calls[-1].url.path == '/currency'
            assert dict(calls[-1].url.params) == {'q':'gold','country':'UA','deep':'true','pretty':'true','lang':'fr'}
            metal = await call(client.currency.list, q='gold', deep=True)
            assert metal['data'][0]['unit'] == 'troy_ounce' and metal['data'][0]['digits'] is None

        finally:
            if async_mode: await client.close()
            else: client.close()
    asyncio.run(run())


@pytest.mark.parametrize('async_mode', [False, True])
def test_currency_indexed_unit(async_mode):
    async def run():
        calls = []
        def handle(request):
            calls.append(request)
            return httpx.Response(200, json=FIXTURE['indexed_pair'])
        client = (AsyncParseAPI if async_mode else ParseAPI)('test', transport=httpx.MockTransport(handle), retries=0)
        async def call(method, *args, **kwargs):
            result = method(*args, **kwargs); return await result if async_mode else result
        try:
            pair = await call(client.currency.rate, 'USD', 'MXV', amount=1)
            assert pair['units']['quote'] == 'indexed_unit' and pair['converted'] == FIXTURE['indexed_pair']['converted']
            assert len(calls) == 1
        finally:
            if async_mode: await client.close()
            else: client.close()
    asyncio.run(run())

REPORTING_FIXTURE = json.loads((Path(__file__).parent / 'fixtures/currency-summary.json').read_text())
@pytest.mark.parametrize('async_mode', [False, True])
def test_currency_archive_sampling_and_complete_january_summary(async_mode):
    async def run():
        calls = []
        def handle(request):
            calls.append(request)
            return httpx.Response(200, json=REPORTING_FIXTURE['summary'] if request.url.path.endswith('/summary') else REPORTING_FIXTURE['sampled_history'])
        client = (AsyncParseAPI if async_mode else ParseAPI)('test', transport=httpx.MockTransport(handle), retries=0)
        async def call(method, *args, **kwargs):
            result = method(*args, **kwargs)
            return await result if async_mode else result
        try:
            result = await call(client.currency.history, 'USD', 'JPY', '1999-01-01', '2026-10-09', interval='month')
            assert result == REPORTING_FIXTURE['sampled_history'] and result['missing'] == ['1999-01-01']
            await call(client.currency.rates_history, 'USD', ['JPY'], '1999-01-01', '2026-10-09', interval='week')
            result = await call(client.currency.rates_summary, 'USD', ['EUR'], '1999-01-01', '1999-01-31', interval='month')
            assert result == REPORTING_FIXTURE['summary'] and result['data'][0]['observation_count'] == 20 and result['data'][0]['missing_day_count'] == 3
            assert calls[-1].url.path == '/currency/USD/rates/summary'
            assert dict(calls[-1].url.params) == {'quotes':'EUR','from':'1999-01-01','to':'1999-01-31','interval':'month'}
            assert [request.url.params['interval'] for request in calls] == ['month','week','month']
            from parseapi import CurrencyRatesSummary, CurrencyRateSummary, CurrencySummaryMissing
            assert 'observation_count' in CurrencyRateSummary.__required_keys__ and 'stale' in CurrencyRateSummary.__optional_keys__
            assert 'missing_day_count' in CurrencySummaryMissing.__required_keys__ and 'interval' in CurrencyRatesSummary.__required_keys__
        finally:
            if async_mode: await client.close()
            else: client.close()
    asyncio.run(run())

import asyncio,json
from pathlib import Path
import httpx
from parseapi import ParseAPI,AsyncParseAPI

FULL=json.loads((Path(__file__).parent/'fixtures/country-corrected.json').read_text())

def test_country_core_context_and_detail_preserved_in_sync_and_async():
    calls=[]
    def transport(request):
        calls.append(request)
        return httpx.Response(200,json=FULL)
    with ParseAPI('fixture',transport=httpx.MockTransport(transport)) as client:
        assert client.country('US',deep=True)==FULL
    async def check():
        async with AsyncParseAPI('fixture',transport=httpx.MockTransport(transport)) as client:
            assert await client.country('US',deep=True)==FULL
    asyncio.run(check())
    assert len(calls)==2
    assert FULL['name_full']=='United States of America' and 'full_name' not in FULL
    assert 'population' in FULL and 'area' in FULL
    assert FULL['demonym']=='American'
    assert FULL['flag']=='🇺🇸' and 'emoji' not in FULL
    assert FULL['capital']=={'name':'Washington, D.C.','lat':38.89,'lon':-77.05}
    assert FULL['tax']=={'name':None,'rate':None}
    assert not {'capital_lat','capital_lon'}&FULL.keys()
    assert 'deep' not in FULL
    assert FULL['region']=='Americas' and FULL['subregion']=='Northern America'
    assert FULL['elevation_average']==760
    assert FULL['gdp_per_capita_usd']==90026.52
    assert FULL['tax'] is not None

def test_actual_antarctica_nulls_stay_null():
    aq=json.loads((Path(__file__).parent/'fixtures/country-aq.json').read_text())
    with ParseAPI('fixture',transport=httpx.MockTransport(lambda _:httpx.Response(200,json=aq))) as client:
        value=client.country('AQ',deep=True)
        assert value==aq and value['languages'] is None and value['population']==0
        assert [value[k] for k in ('currency','currency_name','currency_symbol')]==[None,None,None]

def test_country_tax_reference_zeroes_and_deep_modes():
    de=json.loads((Path(__file__).parent/'fixtures/country-de.json').read_text())
    zero={**de,'capital':{'name':None,'lat':0,'lon':0},'tax':{'name':None,'rate':0}}
    core={k:v for k,v in FULL.items() if k!='deep'}
    bodies=[de,zero,core,dict(core)];calls=[]
    def transport(request):
        calls.append(request);return httpx.Response(200,json=bodies.pop(0))
    with ParseAPI('fixture',transport=httpx.MockTransport(transport)) as client:
        assert client.country('DE',deep=True)==de
        assert de['tax']=={'name':'VAT','rate':19}
        assert client.country('DE',deep=True)==zero
        assert client.country('US')==core
        assert client.country('US',deep=True)==dict(core)
    assert len(calls)==4

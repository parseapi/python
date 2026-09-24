import asyncio
import httpx
import pytest
from parseapi import ParseAPI, AsyncParseAPI
RICH = {'timezone_database_version': '2026c', 'timezones': ['UTC'], 'at': '1970-01-01T00:00:00.000Z', 'zones': [{'timezone': 'UTC', 'countries': [], 'area': None, 'abbreviation': 'UTC', 'offset': '+00:00', 'offset_seconds': 0, 'dst': False, 'observes_dst': False}]}
LOCATED = {'timezone': None, 'targets': None, 'location': {'input': {'type': 'city', 'value': 'Springfield'}, 'status': 'ambiguous', 'candidates': [{'id': 'city_a', 'name': 'Springfield', 'country': 'US', 'state': 'IL', 'timezone': 'America/Chicago', 'latitude': 0, 'longitude': 0}], 'truncated': False, 'source': 'city_reference'}, 'deep': {'standard_offset': '+01:00', 'standard_offset_seconds': 3600, 'dst_offset_seconds': -3600, 'season': {'start': {'at': '2026-10-25T01:00:00Z', 'before': {'offset_seconds': 3600, 'dst': False}, 'after': {'offset_seconds': 0, 'dst': True}, 'change_seconds': -3600}, 'end': None}}}
@pytest.mark.parametrize('async_mode', [False, True])
def test_time_explicit_locations_catalog_filters_and_observations(async_mode):
    calls=[]
    def handle(request):
        calls.append(request)
        return httpx.Response(200,json=RICH if request.url.path=='/time/zones' else LOCATED)
    async def run():
        client=(AsyncParseAPI if async_mode else ParseAPI)('fixture',transport=httpx.MockTransport(handle),retries=0)
        async def call(method,*args,**kwargs):
            result=method(*args,**kwargs)
            return await result if async_mode else result
        try:
            assert await call(client.time.zones,country='US',area='America',offset='+00:00',abbreviation='UTC',dst=False,observes_dst=False,at='1970-01-01T00:00:00Z',details=True,sort='offset') == RICH
            assert dict(calls[-1].url.params) == {'country': 'US', 'area': 'America', 'offset': '+00:00', 'abbreviation': 'UTC', 'dst': 'false', 'observes_dst': 'false', 'at': '1970-01-01T00:00:00Z', 'details': 'true', 'sort': 'offset'}
            for source in [{'ip':'2001:db8::1'},{'city':'Springfield','country':'US','state':'IL'},{'country':'US'},{'iata':'JFK'},{'icao':'KJFK'},{'unlocode':'US NYC'},{'address':'1 Main Street','country':'US','state':'NY'}]:
                assert await call(client.time,**source,targets=['UTC'],deep=True) == LOCATED
                assert calls[-1].url.path == '/time'
                for key,value in source.items(): assert calls[-1].url.params[key] == value
            count=len(calls)
            for source in [{'ip':'8.8.8.8','city':'Paris'},{'ip':'8.8.8.8','country':'US'},{'state':'NY'},{'city':'Paris','state':'IDF'},{'address':'a'},{'ip':''}]:
                with pytest.raises(ValueError): await call(client.time,**source)
            with pytest.raises(ValueError): await call(client.time,'UTC',city='Paris')
            assert len(calls)==count
        finally:
            if async_mode: await client.close()
            else: client.close()
    asyncio.run(run())

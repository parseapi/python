import asyncio
import httpx
import pytest
from parseapi import AsyncParseAPI, ParseAPI, ParseAPIError


@pytest.mark.parametrize('asynchronous', [False, True])
def test_city_canonical_projection_filters_traversal_and_classic_defaults(asynchronous):
    seen=[]
    body={'object':'list','data':[{'id':'city_7aj899nvwyku','object':'city','name':'Vienna','name_local':'Wien'}], 'has_more':False,'url':'/city','next_cursor':None,'coverage':'partial'}
    def respond(request):
        seen.append(request.url)
        return httpx.Response(200,json=body)
    options=dict(countries=['AT','CH'],exclude_countries=['JP'],timezones=['Europe/Vienna','Europe/Zurich'],min_elevation=-10,max_elevation=0,min_population=0,sort='country,-population,name',cursor='opaque+/=?&')
    operations=[
        lambda c:c.city.list(**options),
        lambda c:c.city.id('city_7aj899nvwyku',format='resource',),
        lambda c:c.city.search('Vi',format='list',),
        lambda c:c.city.nearby('Vienna',format='list',),
        lambda c:c.city.children('city_7aj899nvwyku',limit=2,cursor='opaque+/=',deep=True),
        lambda c:c.city.ancestors('city_7aj899nvwyku',),
        lambda c:c.city.siblings('city_7aj899nvwyku',hierarchy=True),
        lambda c:c.city.distance('city_7aj899nvwyku','city_7aj899nvwyku'),
        lambda c:c.city('Vienna'),lambda c:c.city.search('Vi'),lambda c:c.city.nearby('Vienna'),
    ]
    async def run():
        async with AsyncParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            for operation in operations: assert await operation(c)==body
    if asynchronous:asyncio.run(run())
    else:
        with ParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            for operation in operations:assert operation(c)==body
    assert dict(seen[0].params)=={'browse':'true','format':'list','countries':'AT,CH','exclude_countries':'JP','timezones':'Europe/Vienna,Europe/Zurich','min_elevation':'-10','max_elevation':'0','min_population':'0','sort':'country,-population,name','cursor':'opaque+/=?&'}
    assert dict(seen[1].params)=={'format':'resource',}
    assert seen[2].params['format']=='list' and seen[3].params['format']=='list'
    assert seen[4].path.endswith('/children') and dict(seen[4].params)=={'limit':'2','cursor':'opaque+/=','deep':'true'}
    assert seen[5].path.endswith('/ancestors') and dict(seen[5].params)=={}
    assert seen[6].path.endswith('/siblings') and dict(seen[6].params)=={'hierarchy':'true'}
    assert seen[7].path=='/city/id/city_7aj899nvwyku/distance/city_7aj899nvwyku' and not seen[7].params
    assert not seen[8].params and dict(seen[9].params)=={'q':'Vi'} and not seen[10].params


@pytest.mark.parametrize('asynchronous', [False,True])
@pytest.mark.parametrize('distance', [0,None])
def test_city_distance_preserves_zero_and_unknown(asynchronous,distance):
    body={'object':'city_distance','from':'city_7aj899nvwyku','to':'city_7aj899nvwyku','distance':distance,'distance_mi':distance,'method':'great_circle'}
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json=body))
    async def run():
        async with AsyncParseAPI('fixture',transport=transport) as c:assert await c.city.distance(body['from'],body['to'])==body
    if asynchronous:asyncio.run(run())
    else:
        with ParseAPI('fixture',transport=transport) as c:assert c.city.distance(body['from'],body['to'])==body


@pytest.mark.parametrize('asynchronous',[False,True])
@pytest.mark.parametrize('status,code',[(409,'ambiguous_city'),(409,'conflict'),(400,'ambiguous_city'),(429,'rate_limited')])
def test_city_ambiguity_metadata_is_bounded_and_other_errors_and_constructor_unchanged(asynchronous,status,code):
    from parseapi import ParseAPIError
    assert not hasattr(ParseAPIError(400,'invalid_request','Input',None,None),'candidates')
    safe={'id':'city_7aj899nvwyku','object':'city','name':'Vienna','name_local':'Wien','country':'AT','state':None}
    calls=[]
    def respond(request):
        calls.append(request)
        return httpx.Response(status,json={'code':code,'message':'Choose a city','docs':None,'request_id':'req_city','candidates':[dict(safe,deep={'population':99},internal_id=1),safe,safe]},headers={'Retry-After':'60'})
    async def run():
        async with AsyncParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            with pytest.raises(ParseAPIError) as caught:await c.city('Vienna',ambiguity='error')
            return caught.value
    if asynchronous:error=asyncio.run(run())
    else:
        with ParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            with pytest.raises(ParseAPIError) as caught:c.city('Vienna',ambiguity='error')
            error=caught.value
    assert error.status==status and error.code==code and error.retry_after=='60' and error.request_id=='req_city'
    if status==409 and code=='ambiguous_city':assert error.candidates==[safe,safe]
    else:assert not hasattr(error,'candidates')
    assert len(calls)==1

@pytest.mark.parametrize('asynchronous',[False,True])
def test_city_explicit_matching_and_suggestion_evidence(asynchronous):
    calls=[];body={'object':'list','data':[{'id':'city_7aj899nvwyku','object':'city','match':{'type':'fuzzy','source':'name','value':'Vienna','language':None,'edit_distance':1}}],'has_more':False,'url':'/city','next_cursor':None}
    def respond(request):calls.append(request.url);return httpx.Response(200,json=body)
    async def run():
        async with AsyncParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            assert (await c.city.search('Viena',match='fuzzy',max_distance=1,format='list'))==body
            await c.city.search('Vi')
    if asynchronous:asyncio.run(run())
    else:
        with ParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            assert c.city.search('Viena',match='fuzzy',max_distance=1,format='list')==body
            c.city.search('Vi')
    assert dict(calls[0].params)=={'q':'Viena','match':'fuzzy','max_distance':'1','format':'list'}
    assert dict(calls[1].params)=={'q':'Vi'}


@pytest.mark.parametrize('asynchronous',[False,True])
def test_city_reviewed_romanized_optin_and_null(asynchronous):
    calls=[];payload={'id':'city_7aj899nvwyku','object':'city','name_romanized':'Kitakyūshū','romanization_language':'ja-Latn'}
    def respond(request):calls.append(request.url);return httpx.Response(200,json=payload)
    async def run():
        async with AsyncParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            assert await c.city.id(payload['id'],format='resource',romanized=True)==payload
            payload['name_romanized']=None;payload['romanization_language']=None
            assert await c.city.id(payload['id'],format='resource',romanized=True)==payload
            await c.city('Vienna')
    if asynchronous:asyncio.run(run())
    else:
        with ParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            assert c.city.id(payload['id'],format='resource',romanized=True)==payload
            payload['name_romanized']=None;payload['romanization_language']=None
            assert c.city.id(payload['id'],format='resource',romanized=True)==payload
            c.city('Vienna')
    assert dict(calls[0].params)=={'format':'resource','romanized':'true'} and not calls[2].params

@pytest.mark.parametrize('asynchronous',[False,True])
def test_spelling_route_classic_adapter_and_unchanged_default(asynchronous):
    calls=[]; row={'id':'city_7aj899nvwyku','object':'city','name':'Vienna'}
    def respond(request):
        calls.append(request.url.path)
        return httpx.Response(200,json={'object':'list','data':[row],'q':'Viena','has_more':False,'url':'/city/search','next_cursor':None} if request.url.path=='/city/search' else {'q':'Vi','cities':[row]})
    async def run():
        async with AsyncParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            assert (await c.city.search('Viena',match='fuzzy',max_distance=1))['cities']==[row]
            assert (await c.city.search('Viena',match='fuzzy',format='list'))['data']==[row]
            assert (await c.city.search('Vi'))['cities']==[row]
    if asynchronous:asyncio.run(run())
    else:
        with ParseAPI('fixture',transport=httpx.MockTransport(respond)) as c:
            assert c.city.search('Viena',match='fuzzy',max_distance=1)['cities']==[row]
            assert c.city.search('Viena',match='fuzzy',format='list')['data']==[row]
            assert c.city.search('Vi')['cities']==[row]
    assert calls==['/city/search','/city/search','/city']

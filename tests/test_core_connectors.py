import json
from pathlib import Path
import httpx
from parseapi import ParseAPI
FIXTURES=json.loads((Path(__file__).parent/'fixtures/core-connectors.json').read_text())
def test_dynamic_core_fields_and_deep_are_preserved_without_new_calls():
 for body in FIXTURES.values():
  calls=[]
  def transport(request):
   calls.append(request)
   return httpx.Response(200,json=body)
  with ParseAPI('fixture',transport=httpx.MockTransport(transport)) as client:
   assert client.country('US')==body
  assert len(calls)==1
  assert 'deep' not in calls[0].url.params
 assert FIXTURES['company']['identifiers'][0]['value']=='0000320193'
 assert FIXTURES['country']['capital_lat']==0
 assert FIXTURES['emoji']['variants']==['👍🏽']
 assert FIXTURES['emoji']['deep']['variants'][0]['emoji']=='👍🏽'

 assert FIXTURES['point']['city_id']==FIXTURES['point']['deep']['city']['id']
 assert FIXTURES['postal']['country']=='US'
 assert FIXTURES['postal']['deep']['neighbors']==['00544']
 assert 'neighbors' not in FIXTURES['postal']
 assert 'currency' not in FIXTURES['postal']

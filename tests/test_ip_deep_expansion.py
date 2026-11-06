import json
from pathlib import Path
import httpx
from parseapi import ParseAPI
def test_ip_deep_preserves_new_fields_and_exact_unknown_values():
 body=json.loads((Path(__file__).parent/'fixtures/ip-deep-expansion.json').read_text());calls=[]
 def transport(request):
  calls.append(request);return httpx.Response(200,json=body)
 with ParseAPI('fixture',transport=httpx.MockTransport(transport)) as client:
  assert client.ip(body['ip'],deep=True)==body
 assert len(calls)==1 and calls[0].url.params['deep']=='true'
 assert body['deep']['latitude']==0 and body['deep']['proxy'] is False and body['deep']['postal']=='00123'

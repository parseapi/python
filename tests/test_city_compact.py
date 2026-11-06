import json
from pathlib import Path
import httpx
from parseapi import ParseAPI


def test_city_match_and_cursor_survive_without_mechanics():
    rows = [row for row in json.loads((Path(__file__).parent / 'fixtures/noise-approved.json').read_text()) if row['id'].startswith('city-')]
    pending = iter(rows)
    def reply(request):
        assert request.headers['X-API-Version'] == '2.1.0'
        return httpx.Response(200, json=next(pending)['body'])
    with ParseAPI('fixture', retries=0, transport=httpx.MockTransport(reply)) as client:
        for row in rows:
            body = row['body']
            result = client.city.search(body['q'], match=body['match'])
            assert result['cities'] == body['data']
            assert result['next_cursor'] == body['next_cursor']

import asyncio
import inspect
import json
import re
from pathlib import Path

import httpx
import pytest
from parseapi import ParseAPI, AsyncParseAPI, ParseAPIError

BASE = {"id": "co_caczn6wf36hj", "name": "GitLab", "country": "US", "website": None, "listings": [], "address": None, "future": {"unknown": None}}
RICH = {"description": None, "logo": "https://example.com/logo.svg", "socials": [], "founded": {"value": "2011", "precision": "future_precision"}, "sources": [{"type": "future_source", "url": "https://example.com/", "fields": ["logo"], "observed_at": None, "updated_at": None, "future": True}], "parent": None, "future": [None, {}]}


def exercise(async_client, operations, responses, **config):
    calls = []
    queue = list(responses)
    def handler(request):
        calls.append(request)
        status, body = queue.pop(0)
        return httpx.Response(status, json=body, headers={"Retry-After": "0"})
    async def run():
        cls = AsyncParseAPI if async_client else ParseAPI
        client = cls("test_company", transport=httpx.MockTransport(handler), **config)
        results = []
        try:
            for operation in operations:
                value = operation(client)
                results.append(await value if inspect.isawaitable(value) else value)
        finally:
            value = client.close()
            if inspect.isawaitable(value):
                await value
        return results
    return asyncio.run(run()), calls


@pytest.mark.parametrize("async_client", [False, True])
@pytest.mark.parametrize("operation,path,params", [
    (lambda p: p.company.id("co_/é?+", deep=True), "/company/id/co_%2F%C3%A9%3F%2B", {"deep": "true"}),
    (lambda p: p.company.id("co_caczn6wf36hj"), "/company/id/co_caczn6wf36hj", {}),
    (lambda p: p.company.search(query="Café & Co", country="us", limit=2, cursor="a+/=?&", deep=True), "/company", {"q": "Café & Co", "country": "us", "limit": "2", "cursor": "a+/=?&", "deep": "true"}),
    (lambda p: p.company.search(domain="WWW.Example.COM."), "/company", {"domain": "WWW.Example.COM."}),
    (lambda p: p.company.search(ticker="BRK/B", exchange="X/Y"), "/company", {"ticker": "BRK/B", "exchange": "X/Y"}),
    (lambda p: p.company.search(identifier="0000/123", authority="US/SEC", country="US"), "/company", {"identifier": "0000/123", "authority": "US/SEC", "country": "US"}),
    (lambda p: p.company.search(query="", limit=0, cursor=""), "/company", {"q": "", "limit": "0", "cursor": ""}),
    (lambda p: p.company.search(country="US"), "/company", {"country": "US"}),
    (lambda p: p.company.search(industry="0700", industry_type="sic"), "/company", {"industry": "0700", "industry_type": "sic"}),
    (lambda p: p.company.search(country="US", industry="0700", industry_type="sic", cursor="opaque+/=", limit=2, deep=True), "/company", {"country": "US", "industry": "0700", "industry_type": "sic", "cursor": "opaque+/=", "limit": "2", "deep": "true"}),
    (lambda p: p.company.search(query="Example", industry="0700", industry_type="sic", deep=False), "/company", {"q": "Example", "industry": "0700", "industry_type": "sic"}),
    (lambda p: p.company.search(registration_authority="ra000599"), "/company", {"registration_authority": "ra000599"}),
    (lambda p: p.company.search(country="US", industry="0700", industry_type="sic", registration_authority="RA000599", registration_form="DPC", registration_status=" Good Standing ", limit=2, cursor="opaque+/=", deep=True), "/company", {"country": "US", "industry": "0700", "industry_type": "sic", "registration_authority": "RA000599", "registration_form": "DPC", "registration_status": " Good Standing ", "limit": "2", "cursor": "opaque+/=", "deep": "true"}),
    (lambda p: p.company.search(identifier="00001", authority="SEC", registration_authority="RA000599", registration_form="future/Form", registration_status="future+& status", deep=False), "/company", {"identifier": "00001", "authority": "SEC", "registration_authority": "RA000599", "registration_form": "future/Form", "registration_status": "future+& status"}),
    (lambda p: p.company.coverage(), "/company/directory/coverage", {}),
])
def test_routes_encoding_and_direct_request(async_client, operation, path, params):
    body = {"companies": [], "next": None, "future": None}
    results, calls = exercise(async_client, [operation], [(200, body)], timeout=1.25)
    assert results == [body]
    assert len(calls) == 1
    assert calls[0].url.raw_path.split(b"?")[0].decode() == path
    assert dict(calls[0].url.params) == params
    assert calls[0].headers["Parse-Version"] == "2.0.0"
    assert calls[0].headers["X-API-Key"] == "test_company"
    assert calls[0].extensions["timeout"]["read"] == 1.25


@pytest.mark.parametrize("async_client", [False, True])
def test_plain_profiles_deep_triad_pagination_and_coverage(async_client):
    profiles = [BASE, {**BASE, "deep": {}}, {**BASE, "deep": RICH}, {**BASE, "deep": {"description": None, "logo": None, "socials": None, "founded": None, "sources": None}}]
    page = {"companies": [{**p, "match": {"field": "future_field", "value": None}} for p in profiles], "next": "opaque+/=", "future": None}
    empty = {"companies": [], "next": None}
    coverage = {"scope": "future_scope", "companies": 0, "countries": [], "future": None}
    operations = [lambda p: p.company.id(BASE["id"]), lambda p: p.company.id(BASE["id"], deep=True), lambda p: p.company.id(BASE["id"], deep=True), lambda p: p.company.id(BASE["id"], deep=True), lambda p: p.company.search(query="GitLab", deep=True, limit=4), lambda p: p.company.search(query="GitLab", deep=True, limit=4, cursor=page["next"]), lambda p: p.company.coverage()]
    expected = profiles + [page, empty, coverage]
    results, calls = exercise(async_client, operations, [(200, item) for item in expected])
    assert results == expected
    assert len(calls) == len(operations)
    assert dict(calls[5].url.params) == {"q": "GitLab", "limit": "4", "cursor": "opaque+/=", "deep": "true"}


@pytest.mark.parametrize("async_client", [False, True])
@pytest.mark.parametrize("status,operation", [(400, lambda p: p.company.search(query="A", domain="B")), (400, lambda p: p.company.search()), (404, lambda p: p.company.id("co_unknown"))])
def test_errors_remain_errors_with_api_validation(async_client, status, operation):
    code = "invalid_request" if status == 400 else "not_found"
    with pytest.raises(ParseAPIError) as error:
        exercise(async_client, [operation], [(status, {"code": code, "message": "source error", "docs": None, "request_id": "r1"})])
    assert (error.value.status, error.value.code, error.value.request_id) == (status, code, "r1")


@pytest.mark.parametrize("async_client", [False, True])
def test_company_number_callable_and_class_method_are_preserved(async_client):
    cls = AsyncParseAPI if async_client else ParseAPI
    body = {"valid": True, "company": "51824753556", "deep": {"activity": None}}
    results, calls = exercise(async_client, [lambda p: p.company("51 824 753 556", country="AU", deep=True, lang="fr"), lambda p: cls.company(p, "51 824 753 556", country="AU", deep=True, lang="fr")], [(200, body)] * 2)
    assert results == [body, body]
    assert str(calls[0].url) == str(calls[1].url) == "https://api.parseapi.com/company/51%20824%20753%20556?country=AU&deep=true&lang=fr"


@pytest.mark.parametrize("async_client", [False, True])
def test_directory_uses_existing_retry_controls(async_client):
    result, calls = exercise(async_client, [lambda p: p.company.id(BASE["id"], deep=True)], [(503, {}), (503, {}), (200, BASE)])
    assert result == [BASE] and len(calls) == 3
    with pytest.raises(ParseAPIError):
        exercise(async_client, [lambda p: p.company.coverage()], [(503, {})], retries=0)


def test_sync_async_signatures_and_no_directory_lang():
    with ParseAPI("fixture") as sync:
        assert sync.company is sync.company
        async_client = AsyncParseAPI("fixture")
        try:
            assert async_client.company is async_client.company
            for name in ("__call__", "id", "search", "coverage"):
                assert inspect.signature(getattr(sync.company, name)) == inspect.signature(getattr(async_client.company, name))
            for method, arguments in [(sync.company.id, (BASE["id"],)), (sync.company.search, ())]:
                with pytest.raises(TypeError):
                    method(*arguments, lang="fr")
        finally:
            asyncio.run(async_client.close())


def test_readme_recipe_uses_explicit_selection_and_returned_cursor():
    section = (Path(__file__).resolve().parents[1] / "README.md").read_text().split("## Company directory\n", 1)[1]
    code = re.search(r"```python\n(.*?)```", section, re.S).group(1)
    responses = [{"companies": [BASE], "next": "opaque+/="}, {**BASE, "deep": RICH}, {"companies": [], "next": None}, {"scope": "sample"}]
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=responses.pop(0))
    with ParseAPI("fixture", transport=httpx.MockTransport(handler)) as parse:
        exec(compile(code, "README.md", "exec"), {"parse": parse})
    assert len(calls) == 4
    assert calls[1].url.path == "/company/id/co_caczn6wf36hj"
    assert calls[2].url.params["cursor"] == "opaque+/="


@pytest.mark.parametrize("async_client", [False, True])
def test_employee_observations_preserve_zero_false_dates_scope_and_missing(async_client):
    values = [
        {}, {"employees": None},
        {"employees": {"count": 0, "as_of": "2025-12-31", "scope": "legal_entity", "method": "reported", "approximate": False}},
        {"employees": {"count": 12500, "as_of": "2026-06-30", "scope": "consolidated_group", "method": "reported", "approximate": True}},
        {"employees": {"count": 7, "as_of": "2026-01-15", "scope": "future_scope", "method": "future_method", "approximate": False, "future": None}},
    ]
    for deep in values:
        profile = {**BASE, "deep": deep}
        page = {"companies": [{**profile, "match": {"field": "name", "value": BASE["name"]}}], "next": None}
        operations = [lambda p: p.company.id(BASE["id"], deep=True), lambda p: p.company.search(query=BASE["name"], deep=True)]
        results, calls = exercise(async_client, operations, [(200, profile), (200, page)])
        assert results == [profile, page]
        assert ("employees" in results[0]["deep"]) == ("employees" in deep)
        assert len(calls) == 2


@pytest.mark.parametrize("async_client", [False, True])
def test_registrations_preserve_source_roles_nulls_and_leading_zeros(async_client):
    registration = json.loads(r'{"authority":"RA000599","number":"0001234567","jurisdiction":{"country":"US","state":"CO"},"role":"domestic","legal_form":{"code":"DNC","name":"Domestic Non-profit Corporation"},"status":"Good Standing","formation_date":"2004-02-29","address":{"kind":"principal","line1":"12 Main St.","line2":"Suite 2","city":"Example","state":"CO","postal":"00123-0001","country_raw":"US"},"future":"retained"}')
    for deep in [{}, {"registrations": None}, {"registrations": []}, {"registrations": [registration]}, {"registrations": [{**registration, "role": "future_role", "formation_date": None, "address": None}]}]:
        profile = {**BASE, "deep": deep}
        page = {"companies": [{**profile, "match": {"field": "identifier", "value": registration["number"]}}], "next": None}
        results, calls = exercise(async_client, [lambda p: p.company.id(BASE["id"], deep=True), lambda p: p.company.search(identifier=registration["number"], authority=registration["authority"], deep=True)], [(200, profile), (200, page)])
        assert results == [profile, page] and len(calls) == 2

"""Compile-only consumer for the typed callable namespace and previous methods.

pyright --pythonpath .venv/bin/python tests/typing_company_directory.py
No functions in this fixture are invoked.
"""
from parseapi import ParseAPI, AsyncParseAPI


def sync_directory(parse: ParseAPI) -> None:
    number_lookup = ParseAPI.company
    number_lookup(parse, "51 824 753 556", country="AU", deep=True, lang="fr")
    lookup = parse.company
    lookup("51 824 753 556", country="AU", deep=True, lang="fr")
    lookup.id("co_caczn6wf36hj", deep=True)
    lookup.search(query="GitLab", country="US", limit=5, cursor="opaque", deep=True)
    lookup.search(domain="about.gitlab.com")
    lookup.search(ticker="GTLB", exchange="Nasdaq")
    lookup.search(identifier="0001653482", authority="sec")
    lookup.coverage()


async def async_directory(parse: AsyncParseAPI) -> None:
    number_lookup = AsyncParseAPI.company
    await number_lookup(parse, "51 824 753 556", country="AU", deep=True, lang="fr")
    lookup = parse.company
    await lookup("51 824 753 556", country="AU", deep=True, lang="fr")
    await lookup.id("co_caczn6wf36hj", deep=True)
    await lookup.search(query="GitLab", country="US", limit=5, cursor="opaque", deep=True)
    await lookup.search(domain="about.gitlab.com")
    await lookup.search(ticker="GTLB", exchange="Nasdaq")
    await lookup.search(identifier="0001653482", authority="sec")
    await lookup.coverage()

"""Live smoke against the edge. Canary-ready: env-driven, clean exit codes.

  PARSEAPI_KEY       required
  PARSEAPI_BASE_URL  optional override

Run: python smoke/smoke.py
"""

import sys

from parseapi import ParseAPI, ParseAPIError

failures = 0
total = 0


def check(name, ok, detail=""):
    global failures, total
    total += 1
    if not ok:
        failures += 1
    print(f"{'ok  ' if ok else 'FAIL'} {name}{f' ({detail})' if detail else ''}")


def expect_ok(name, call, assert_fn=None):
    try:
        result = call()
        problem = assert_fn(result) if assert_fn else None
        check(name, not problem, problem or "")
    except ParseAPIError as err:
        check(name, False, f"{err.status} {err.code}")
    except Exception as err:  # noqa: BLE001 - smoke reports everything
        check(name, False, str(err))


def expect_error(name, call, code):
    try:
        call()
        check(name, False, "expected error, got 200")
    except ParseAPIError as err:
        check(name, err.code == code, f"got {err.code}")
    except Exception as err:  # noqa: BLE001
        check(name, False, str(err))


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

parse = ParseAPI()

expect_ok("ip", lambda: parse.ip("8.8.8.8"), lambda r: None if r["ip"] == "8.8.8.8" else "wrong ip")
expect_ok("ip.self", lambda: parse.ip.self(), lambda r: None if r.get("ip") else "no ip")
expect_ok("continent", lambda: parse.continent("NA"), lambda r: None if r["name"] == "North America" else "wrong name")
expect_ok("continent.countries", lambda: parse.continent.countries("NA"), lambda r: None if r["countries"] else "empty")
expect_ok(
    "bloc",
    lambda: parse.bloc("EU"),
    lambda r: None if r["name"] == "European Union" and r["members"] == 27 else "wrong bloc",
)
expect_ok(
    "bloc.countries",
    lambda: parse.bloc.countries("SCHENGEN"),
    lambda r: None if r["countries"] and len(r["countries"]) == 29 else "wrong members",
)
expect_ok("country", lambda: parse.country("US"), lambda r: None if r["iso3"] == "USA" else "wrong iso3")
expect_ok("country.states", lambda: parse.country.states("US"), lambda r: None if len(r["states"]) >= 50 else "too few")
expect_ok("state", lambda: parse.state("NC", country="US"), lambda r: None if r["name"] == "North Carolina" else "wrong")
expect_ok("state.districts", lambda: parse.state.districts("NC", country="US"), lambda r: None if r["districts"] else "empty")
expect_ok("district", lambda: parse.district("37081"), lambda r: None if "Guilford" in r["name"] else "wrong district")
expect_ok("city", lambda: parse.city("charlotte", country="US"), lambda r: None if r["name"] == "Charlotte" and str(r.get("id", "")).startswith("city_") else "wrong city")
expect_ok(
    "city.id",
    lambda: parse.city.id(parse.city("charlotte", country="US")["id"]),
    lambda r: None if r["name"] == "Charlotte" else "wrong city",
)
expect_ok("city.search", lambda: parse.city.search("char", country="US", limit=5), lambda r: None if r["cities"] else "empty")
expect_ok("city.nearest", lambda: parse.city.nearest(35.2271, -80.8431), lambda r: None if "distance" in r else "no distance")
expect_ok("postal", lambda: parse.postal("28202", country="US"), lambda r: None if r["city"] == "Charlotte" else "wrong city")
expect_ok("postal.nearby", lambda: parse.postal.nearby("28202", country="US", radius=40), lambda r: None if r["nearby"] else "empty")
expect_ok(
    "postal.distance",
    lambda: parse.postal.distance("28202", "10001", country="US"),
    lambda r: None if 800 < r["distance"] < 1000 else f"distance {r['distance']}",
)
expect_ok("email", lambda: parse.email("hello@gmail.com"), lambda r: None if r["valid"] is True else "not valid")
expect_ok(
    "vat",
    lambda: parse.vat("DE136695976"),
    lambda r: None if r.get("valid") is True and r.get("country") == "DE" else "not valid DE",
)
expect_ok(
    "iban",
    lambda: parse.iban("DE89370400440532013000"),
    lambda r: None if r.get("valid") is True and r.get("country") == "DE" and r.get("bank") == "37040044" else "not valid DE",
)
expect_ok("iban junk", lambda: parse.iban("hello"), lambda r: None if r.get("valid") is False else "expected invalid")
expect_ok("phone", lambda: parse.phone("+14155552671"), lambda r: None if r["phone"] == "+14155552671" else "wrong phone")
# Metered core siblings: junk numbers answer 200 valid false, free, no vendor dip.
expect_ok("carrier junk free", lambda: parse.carrier("555-0100"), lambda r: None if r["valid"] is False else "expected invalid")
expect_ok("caller junk free", lambda: parse.caller("555-0100"), lambda r: None if r["valid"] is False else "expected invalid")
expect_ok("hlr junk free", lambda: parse.hlr("555-0100"), lambda r: None if r["valid"] is False else "expected invalid")
expect_ok("domain", lambda: parse.domain("gmail.com"), lambda r: None if r["available"] is False else "gmail available?")
expect_ok("mx", lambda: parse.mx("gmail.com"), lambda r: None if r["mx"] else "no mx")
expect_ok("useragent", lambda: parse.useragent(UA), lambda r: None if r["browser"] == "Chrome" else f"browser {r['browser']}")
expect_ok(
    "vin",
    lambda: parse.vin("1HGCM82633A004352"),
    lambda r: None if r.get("valid") is True and r.get("make") == "Honda" and r.get("year") == 2003 else "wrong decode",
)
expect_ok("vin junk", lambda: parse.vin("1HGCM82613A004352"), lambda r: None if r.get("valid") is False else "expected invalid")
expect_ok("currency", lambda: parse.currency("USD"), lambda r: None if r["symbol"] == "$" else "wrong symbol")
expect_ok("currency.rate", lambda: parse.currency.rate("USD", "EUR"), lambda r: None if 0 < r["rate"] < 10 else "bad rate")
expect_ok(
    "language",
    lambda: parse.language("en"),
    lambda r: None if r.get("language") == "en" and r.get("name") == "English" else "wrong language",
)
expect_ok(
    "name",
    lambda: parse.name("BILLY O'SHALL"),
    lambda r: None if r["name"] == "Billy O'Shall" and r["valid"] is True and r["gender"] == "male" else "wrong name",
)
expect_ok(
    "timezone",
    lambda: parse.timezone("America/New_York"),
    lambda r: None if r["offset_minutes"] in (-240, -300) else f"offset {r['offset_minutes']}",
)
expect_ok("holiday", lambda: parse.holiday("US"), lambda r: None if len(r["holidays"]) > 5 else "too few")
expect_ok(
    "holiday.date",
    lambda: parse.holiday.date("US", "2026-12-25"),
    lambda r: None if r["holiday"] and r["holiday"]["name"] == "Christmas Day" else "not christmas",
)
expect_ok("holiday null", lambda: parse.holiday.date("US", "2026-08-12"), lambda r: None if r["holiday"] is None else "expected null")
expect_ok("elevation", lambda: parse.elevation(35.2271, -80.8431), lambda r: None if isinstance(r["elevation"], (int, float)) else "no elevation")
expect_ok("point", lambda: parse.point(36.0726, -79.792), lambda r: None if r["country"] == "US" else f"country {r['country']}")
expect_ok("weather", lambda: parse.weather(40.7128, -74.006), lambda r: None if (r.get("station") or {}).get("id") else "no station")
expect_ok("emoji", lambda: parse.emoji("rocket"), lambda r: None if r["emoji"] == "\U0001F680" else "wrong emoji")
expect_ok("emoji.search", lambda: parse.emoji.search("fire", limit=5), lambda r: None if r["emojis"] else "empty")
expect_ok("point deep triad", lambda: parse.point(36.0726, -79.792, deep=True), lambda r: None if isinstance(r.get("deep"), dict) else "deep missing")

expect_error("honest 404", lambda: parse.city("notarealcityxyz"), "not_found")
expect_error("bogus key 401", lambda: ParseAPI("bogus_key_123", retries=0).country("US"), "invalid_api_key")

print(f"\n{total - failures}/{total} passed")
sys.exit(0 if failures == 0 else 1)

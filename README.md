# parseapi

Official ParseAPI client for Python.

```bash
pip install parseapi
```

```python
from parseapi import ParseAPI

parse = ParseAPI("your-api-key")
country = parse.country("US")
```

Get a key at [parseapi.com](https://parseapi.com). The client also reads `PARSEAPI_KEY` from the environment.

## API versions

Version 1.3.0 explicitly selects the API contract supported by this SDK. It sends `Parse-Version: 2.0.0` on every lookup so responses match the API contract supported by the package. Your key and the team's saved default stay the same.

Upgrade the dependency in staging, review the [release notes](https://parseapi.com/docs/releases), and test the application before deploying the same code and dependency version to production. Commit your dependency lockfile so the tested package travels with your deployment. Future major SDK upgrades can select a newer API contract.

Previously published SDKs keep their existing behavior and use the team's default. Requests without `Parse-Version` also use that default, managed in [Dashboard API version](https://parseapi.com/dashboard/versions). Keep it unchanged while older applications depend on it. Rolling back to an SDK without a version header restores the team default, so rollback only restores the old contract when that default has stayed unchanged.

The package owns its supported API version. For direct HTTP integrations, an explicit `Parse-Version` header selects a supported contract. See [API versions and migration](https://parseapi.com/docs/versioning).

## Weather from a postal code

Start with the postal code, then pass its coordinates to weather. Reuse the client from the example above.

```python
place = parse.postal("28202", country="US")
lat, lon = place["latitude"], place["longitude"]
if lat is not None and lon is not None:
    weather = parse.weather(lat, lon)
    print(weather)
```

The coordinates represent the postal area. Weather is for that point. Missing coordinates skip the weather lookup. This composition performs two ordinary lookups when coordinates are available, with the retry policy below.

## Supply the context you know

Pass `country` when a postal code or national phone number needs disambiguation. A complete international phone number already carries its country context. For a numeric date such as `03/04/2026`, supply the intended `format`. Defaults resolve what the input establishes. Ambiguous input needs your context.

Results are plain data. Pass a returned code or coordinate to another operation when the task needs it. Check nullable values before composing the next call.

Use `parse.postal("28202", country="US", deep=True)` for US ZIP tax references. `deep.tax` names the levy and `deep.tax_rate` is a percentage, so `7.9` means 7.9%. The state, county, city and special components explain that combined rate. An exact address can differ. Country and state lookups provide their own geographic reference rates, which should not be added to the ZIP rate. `None` means unknown and `0` means known zero. Country `deep.tax_id_format` and `deep.tax_id_regex` describe registration-number format only. Use `vat` for a metered registration check with `deep` explicitly enabled.

## Company directory

Find candidates, then fetch the profile you selected.

```python
candidates = parse.company.search(query="GitLab", country="US", limit=5)
selected_id = "co_caczn6wf36hj"  # Explicitly chosen after reviewing candidates.
profile = parse.company.id(selected_id, deep=True)
if candidates["next"] is not None:
    next_page = parse.company.search(
        query="GitLab", country="US", limit=5, cursor=candidates["next"]
    )
coverage = parse.company.coverage()
```

Use at most one selector: `query` for a name, `domain`, `ticker`, or `identifier`; country or exact industry filters also allow discovery without a selector. The API validates selectors and filters. Use `country` to scope candidates, `exchange` with a ticker, and `authority` with an identifier. Search returns `companies` and an opaque `next` cursor. Review candidate identity and match details before choosing a stable Company ID. Pass `next` as `cursor` with the same selector, filters and limit to continue that result set.

Directory profiles are plain JSON data. `deep` belongs to each company in search results and adds legal/reference detail plus nullable `description`, `logo`, `founded`, and the `socials` and `sources` collections. A logo is a reported URL. `founded` has `value` and `precision`, distinct from incorporation. Sources identify the website, filing or business register, supported fields and observation/update timestamps. Employee observations retain count, measurement date, organization scope and approximation; null means unknown. Missing, null, empty and unknown fields retain their response values. An empty search is a successful result. Invalid inputs and unknown IDs raise the existing API error.

The recipe requests one candidate page, one explicitly chosen profile and directory coverage, plus a second page when a cursor is returned. Each operation uses the existing retry settings. The number-validation call remains unchanged. `lang` applies to national company-number lookup, while directory calls use the source labels.

`AsyncParseAPI` exposes the same `company`, `company.id`, `company.search` and `company.coverage` calls with `await`.

Discovery example: `parse.company.search(country="US", industry="0700", industry_type="sic")`

Supply `industry` and `industry_type` together. The supported namespace is `sic`, with an exact four-digit string such as `0700`; leading zeros are meaningful. Country-only discovery is also supported. Filters intersect and may narrow an existing selector. Country matches the profile country, not a headquarters or operating-presence claim. Unknown values do not match a requested filter. Filter-only candidates use `match.field: "filters"` and `match.value: null`; reuse the same filters and limit with a returned cursor. Counts describe this directory edition, not complete country coverage.

Reviewed `deep.registrations` retain the registry authority and exact number, registration jurisdiction, domestic role, legal form, administrative status and source-scoped formation date. Principal addresses keep their role and recorded text; they are not headquarters. Registration does not establish current operations or tax exemption. `[]` means no admitted registration facts; older responses may omit the field. Sources use `business_register` for these facts and preserve the original observation time; unknown record update times remain null.

## Calls

One method per endpoint, named after the route.

```python
parse.ip("8.8.8.8")
parse.ip.self()
parse.email("hello@gmail.com")
parse.vat("DE136695976")
parse.bank("DE89370400440532013000")
parse.card("424242")
parse.provider("1881018208")
parse.phone("+14155552671")
parse.carrier("+14155552671")
parse.caller("+14155552671")
parse.hlr("+14155552671")
parse.postal("SW1A 1AA")
parse.postal("28202", country="US")
parse.postal.nearby("28202", country="US", radius=40)
parse.postal.distance("28202", "10001", country="US")
parse.address("1600 Pennsylvania Ave NW, Washington DC", country="US")
parse.address.search("1600 Pennsylvania", country="US", postal="20500")
parse.company("51 824 753 556", country="AU")
parse.company.id("co_caczn6wf36hj", deep=True)
parse.company.search(domain="about.gitlab.com")
parse.company.search(ticker="GTLB", exchange="Nasdaq")
parse.company.search(identifier="0001653482", authority="sec")
parse.company.coverage()
parse.city("charlotte", country="US")
parse.city.id("city_mb8mbqrkz8zb")
parse.city.search("char", country="US", limit=10)
parse.city.nearest(35.2271, -80.8431)
parse.city.nearby("denver", radius=8, unit="mi")
parse.country("US")
parse.country.states("US")
parse.state("colorado")
parse.state("NC", country="US")
parse.state.districts("NC", country="US")
parse.district("37081")
parse.continent("NA")
parse.continent.countries("NA")
parse.bloc("EU")
parse.bloc.countries("EU")
parse.currency("USD")
parse.currency.rate("USD", "EUR")
parse.language("en")
parse.name("BILLY OSHALL")
parse.name("Andrea", country="IT", deep=True)
parse.name("Robert James Smith", deep=True, name_locale="en")
parse.time()  # UTC now
parse.time("America/New_York")
parse.time("America/New_York", at="2026-09-05T15:00:00", to="Europe/London")
parse.time.at(39.77, -104.9)
parse.date("03/04/2026", format="mdy")
parse.date.today()
parse.holiday("US", year=2026)
parse.holiday.date("US", "2026-12-25")
parse.elevation(35.2271, -80.8431)
parse.point(36.0726, -79.792)
parse.weather(40.7128, -74.006)
parse.domain("example.com")
parse.asn("AS13335")
parse.mac("00:1B:63:84:45:E6")
parse.mx("example.com")
parse.dns("example.com")
parse.dns("_dmarc.example.com", type="TXT")
parse.useragent(ua_string)
parse.vehicle("1HGCM82633A004352")
parse.industry("541511")
parse.industry.search("coffee shop", limit=5)
parse.tariff("8471.30.01.00")
parse.tariff.search("sunglasses")
parse.emoji("rocket")
parse.emoji.search("fire")
```

The existing NAICS lookup and search methods remain available as compatibility names for Industry.

Industry paid deep records include classification `deep.exclusions`, each with a description and linked codes. Generic exclusions can have no linked codes. Omitted or null exclusions in older responses remain unknown. Search results also include `match`: the matched `field` (`name`, `term` or `naics`) and `text`, plus `corrections` with `from` and `to` tokens for typo fallback. Corrections are empty for exact, plural and prefix matches. Direct code lookups omit `match`. Older responses may omit it.

Responses are plain dicts, exactly the JSON the API returns. `country.states("US")` requests states directly; it does not fetch a country first. Required inputs are positional and optional behavior uses keyword arguments, leaving room for new options without changing existing calls. Reuse a client across calls. Use `with ParseAPI(...) as parse:` or call `parse.close()` when finished.

DNS uses pooled requests on every plan. Omit `type` to check A, AAAA, CNAME, MX, NS, TXT, SOA, CAA, SRV and PTR. Records contain `name`, `type`, `ttl` in seconds and a DNS presentation `value`. TXT values retain quoting and chunk boundaries. A selected question can include its CNAME chain. Empty records mean no records. Lookup failures remain errors.

## Async

Same lookup methods and keyword arguments, with `await`. Use a context manager to close the client when the work is done.

```python
from parseapi import AsyncParseAPI

async with AsyncParseAPI("your-api-key") as parse:
    country = await parse.country("US")
```

Name paid deep includes flat `short`, `directory`, and `initials` fields beside `gender` and `salutation`. `name_locale` selects CLDR formatting rules and defaults to `en`. It changes formatting only. Country remains gender context, and unavailable formatting is null. Older responses may omit these fields.

## Display language

Choose display names for one request:

```python
parse.country("DE", lang="fr")
```

`lang` is optional on geography lookups and their lists/searches, Currency lookup, Language, Date, Time/Timezone, Emoji lookup/search, and unit discovery. IP, ASN, national Company number lookup and NPI also accept it for their geographic labels. Codes, native names, quantities and response structure retain their meanings. Source coverage determines which labels are translated; unavailable labels use the API's documented fallback.

The next call keeps its usual default unless it also supplies `lang`. Existing `deep` rules still apply. Date `format` and measurement `locale` remain explicit input-parsing controls.

## Time

`time` returns local ISO `at` with its UTC offset and integer Unix seconds in `unix`. The core `offset` preserves exact precision. Optional `deep.offset_seconds` gives the numeric offset, while `deep.offset_minutes` gives whole minutes. Historical offsets and ISO times can include offset seconds. Omitted `at` means now. With `to` or `targets`, an offsetless `at` is source wall time. Otherwise it is UTC. Include an offset for repeated local times around a clock change. Current time and conversion use pooled requests on every plan. Coordinate clock fields can be null when the timezone is unknown. Existing `timezone` methods remain supported.

For an offsetless `at` with `to` or `targets`, choose how to handle a clock change with `disambiguation`. It applies to named-zone and coordinate Time calls.

| Value | Repeated time | Skipped time |
| --- | --- | --- |
| `compatible` (default) | Earlier occurrence | Shift forward by the clock change |
| `earlier` | Earlier occurrence | Shift backward by the clock change |
| `later` | Later occurrence | Shift forward by the clock change |
| `reject` | `400 ambiguous_time` | `400 nonexistent_time` |

An explicit UTC offset selects an instant directly. For example, `2026-11-01T01:30:00-04:00` and `2026-11-01T01:30:00-05:00` identify the two New York occurrences. A valid `disambiguation` value has no effect on explicit instants, current-time requests or lookups without `to` or `targets`. For user-entered appointment times, start with `reject`. Handle `ambiguous_time` or `nonexistent_time` by collecting an explicit offset or an earlier/later choice from the user. Other malformed input still uses `invalid_request`.

```python
result = parse.time("America/New_York", at="2026-11-01T01:30:00",
                    to="UTC", disambiguation="later")
print(result["to"]["at"])  # 2026-11-01T06:30:00+00:00
```

Canonical Time `deep` includes the pinned rule edition in `deep.timezone_database_version` and source-wall resolution in `deep.resolution`. Resolution records `kind` (`unique`, `overlap` or `gap`), the selected policy, signed `adjustment_seconds`, and chronological alternatives with exact `at`, Unix seconds and UTC offset. Unique times have an empty alternatives list. Explicit instants, current time and lookups without conversion have null resolution. Destination detail stays compact.

Search serving IANA IDs by city or region, or omit the query to list all (Go and Rust use an empty string). Discovery returns `timezone_database_version` and sorted `timezones`. No search matches returns `timezones: []`.

Pass `targets` to convert one instant to 1-10 zones in a single pooled request. The native list preserves order and duplicates. Use `targets` instead of `to`. The response adds `targets`, with optional detail inside each target. Unknown source coordinates return `targets: null`. An unknown destination rejects the whole request with `not_found`. Omission keeps the original response shape.

```python
zones = parse.time.zones('New York')
result = parse.time('UTC', at='2026-09-24T12:00:00Z',
                    targets=['America/New_York', 'Asia/Tokyo'])
print(zones['timezones'], result['targets'])
```

### Location inputs and timezone filters

`parse.time(iata="JFK", deep=True)` and `parse.time.zones(country="US", dst=False, observes_dst=True, details=True)`.

Choose one explicit location input: IP, exact city name or stable city ID, country, IATA airport, ICAO airport, port UN/LOCODE, or address. Country and state can narrow a city or address. State requires country. Address lookup requires US country context and a strict address-point match. Port lookup covers the reviewed port subset, not every assigned UN/LOCODE. IP lookup always uses the supplied IP.

Location calls add `location` with `status`, `candidates`, `truncated`, `source` and the typed input. Check `status` before using the clock: ambiguous or missing locations retain null time fields. Candidate coordinates and IDs can also be null. A country with multiple timezones does not silently choose one. Named-zone and coordinate calls retain their existing signatures.

Timezone discovery accepts country, IANA area, exact signed offset, abbreviation, DST-at-instant and observes-DST-during-year filters. `at` selects the common instant, `sort` selects timezone or offset order, and `details` adds `zones` rows plus the evaluation `at`. The default `timezones` list stays compact. False DST filters are sent explicitly. An abbreviation returns candidate zones rather than choosing one. Observes-DST uses the UTC calendar year containing `at`.

Source deep adds `standard_offset`, `standard_offset_seconds`, signed `dst_offset_seconds` and `season`. Seasonal adjustments can be negative. `season` describes the current DST-flag interval, or the next within 400 days, with actual before/after transition facts and signed `change_seconds`. Unknown boundaries remain null. These fields are optional and nullable, and destination deep stays compact.

## Measurements

```python
result = parse.measure("5 ft 11 in", to="cm")
units = parse.measure.units(unit="m")
```

`amount` is a decimal string, such as `"180.34"`. Without `to`, the API returns the canonical unit for the measurement type. Pass `locale` for number formatting and `system` (`us` or `imperial`) when a customary unit needs context. Ambiguous input returns `valid: false`, a `reason`, and available `choices`. Invalid or incompatible target units use the normal API error.

Unit discovery accepts optional `query`, `type`, and `unit` filters. `unit` selects compatible targets. Omit the filters for the reviewed catalog. Both operations use pooled requests.

## Place statistics and optional detail

Australian postal lookups include core `localities` with suburb choices (`city`, `state`, `state_name`) on every plan. Null or an omitted field means unknown, while `[]` means the reviewed reference has no eligible choices. `city` stays null when the source is ambiguous, even if there is only one eligible choice. Let the user select their suburb and keep manual entry available. These are geographic choices, not mailing-address verification. [G-NAF source, adaptations and licence](https://parseapi.com/legal/attribution#postal-au).

Postal and District paid profiles include `deep.property_tax` where supported. It contains `annual_median`, `currency` and `period`: median annual property tax payable on owner-occupied homes in the statistical area. The amount is adjusted to the final year of the reporting period (`YYYY-YYYY`). This is an area statistic, not a rate or an individual property bill. Unsupported, missing and censored estimates are null.

```python
place = parse.postal("28202", country="US", deep=True)
property_tax = (place.get("deep") or {}).get("property_tax")
```

Read `population_period` alongside `population`: a reporting year (`YYYY`) or period (`YYYY-YYYY`), null when unknown or unverifiable. Keep missing or null values unknown and preserve a known zero. These fields belong to full place profiles. State district lists include each district's population and period. Postal nearby and distance detail remains metropolitan associations only. Continent population stays in core.

Country deep includes `land_area` and `water_area` in km2, `coastline` in km, and mean `elevation` in metres. `lowest_point` and `highest_point` contain a nullable `name` and an `elevation` in metres. Values below sea level are negative. Missing or null values stay unknown, and zero stays zero.

Point returns the timezone ID with the core location. Its optional deep detail adds terrain and compact nearest-city context on every plan. A nearest city is null when none is within 200 km.

Weather returns current conditions by default. Paid deep adds specialist current measurements, forecasts and related detail. A past `date` is a UTC day and requires deep: it adds `deep.history` alongside current conditions. Date alone does not request history.

```python
parse.weather(40.7128, -74.006, deep=True, date="2026-08-15")
```

Tariff starts with the general schedule line. Paid deep adds units and the special and other schedule columns. An optional origin then resolves country-specific measures. The three calls below show those successive choices. Without origin, schedule detail is still returned and origin-dependent fields are null. A null effective rate is not a zero rate.
Tariff lookup and search accept an optional `edition` fingerprint and `date` (`YYYY-MM-DD`). The edition pins exact immutable source bytes. A date is accepted only when verified source coverage exists. An edition without a date returns undated schedule context (`date: null`). Default requests use today. Paid detail exposes an open-string `reason` when `effective_rate` is null, including `incomplete_coverage`. A null rate never means zero. Explicit selections fail with `tariff_selection_mismatch` if an older server ignores the requested scope.


Origin means where the goods originate, not where they ship from. The effective rate covers matched stored schedule measures only; it is not complete duty or landed cost.

Codes contain 4, 6, 8 or 10 ASCII digits; dots and whitespace are optional. Search returns up to 20 description matches with parent `lineage` so a result named “Other” has context. Search is not product classification. In deep, `measures: null` means origin-dependent measures were not resolved; `measures: []` means the resolved lookup found none.

```python
parse.tariff("8471.30.01.00")
parse.tariff("8471.30.01.00", deep=True)
parse.tariff("8471.30.01.00", deep=True, origin="CN")
```

Address search uses context from the form: prefer postal, or city and state. An optional end-user `ip` is a locality hint for server-side calls. An empty result explains itself with `reason`: `more_input`, `missing_context` or `no_matches`. With suggestions, reason is null. Older responses may omit it, and future reasons remain strings. Catalog and lookup failures use the existing API errors.

HLR reports status at the last check. `live` means assigned and `connected` means reachable at that check. Cached results may be returned. Null means unconfirmed. Deep diagnostics stay within the same metered lookup.

Bank returns core `checks` for input, country, length, structure, checksum and national rules, plus an `issues` list. States are `passed`, `failed`, `not_checked` or `not_supported`. Unsupported national checking is not a failure. `valid` covers the implemented format and checksum rules, not account existence, ownership or payment reachability. Directory names and BICs may be null independently. Older responses may omit `checks` and `issues`, and future states and issue codes remain strings. Pass the original input unchanged so the API can report invalid characters. Deep `account` remains the BBAN remainder.

Bank inputs use `POST /bank` JSON bodies, keeping IBAN and account values out of request URLs. Pass original strings; the server owns normalization and validation. Avoid logging request bodies. IBAN deep can include `directory` with the immutable `edition`, resolved `country` and actual `match` grain (`bank`, `branch`, `prefix` or `none`); it is absent if no directory lookup ran. A match does not prove complete country coverage or payment reachability.

Use country requirements to build supported input fields. US ACH has an explicit helper with no deep option. It checks the routing format/ABA checksum and account-field syntax; `account_checksum` is `not_supported`. It preserves account characters and leading zeros. A nullable bank name is routing-directory identity, not account existence, ownership or ACH eligibility. The examples below are synthetic test inputs, not payment instructions.

```python
parse.bank_requirements("US", format="us_ach")
parse.bank_us_ach(routing="011000015", account="0001234567")
```

## Provider lookup

```python
provider = parse.provider("1881018208")
profile = parse.provider("1881018208", deep=True)
```

Pass the original NPI as a string. `valid` checks its format and checksum; `registered` means a match in the stored NPPES snapshot. `active` reflects recorded NPI deactivation, not licensure. `excluded` is an NPI-only OIG LEIE match; `false` is not a complete exclusion clearance. These directory facts do not verify credentials, current practice contact or payment eligibility.

Invalid input returns `valid: false` with unknown provider fields. A checksum-valid number missing from the snapshot returns `registered: false`; unavailable storage remains an API error. Preserve `null` as unknown.

The default pooled lookup includes provider identity, specialty and practice contact where held. Paid `deep` adds `deactivated_at`, `medicare`, `opt_out` and `enrollments` from stored source files, with no separate check meter or live verification. `enrollments: null` means unavailable; `[]` means no enrollment rows are returned. The API omits unrequested `deep` and returns `{}` when requested on Free.

Paid Deep also returns `taxonomies` in published order, with taxonomy code, specialty label, primary flag and provider-reported license number/state, plus `enumerated_at`, `updated_at` and `reactivated_at` record dates. Reported licenses are not verified licenses. Null lists mean unavailable; empty lists mean the edition contains no entries. Core `sources` is available on every plan: NPPES, LEIE, PECOS and opt-out each have nullable edition metadata (`edition`, `published_at`, `through`, `imported_at`). Provider record dates are separate from source publication and completed import dates. Older responses may omit these additions. Edition details remain null until a verified source is served.

## Deep

Choose enrichment for the question you need answered.

| Operation | What `deep` requests |
|---|---|
| NPI | All published taxonomies, reported license details, provider record dates and Medicare detail on paid plans. Primary specialty, exclusion flag and source metadata stay core. |
| IP | Richer IP fields included with a paid plan. No separate check meter. |
| Domain | Registration dates, registrar, status and DNSSEC, included with a paid plan. Use `dns` for DNS records and `mx` for mail routing. |
| Email | A metered mailbox check with deliverability, catch-all, status, reason and address hints, using included email checks or enabled on-demand usage. |
| VAT | A metered registry check where supported, using included VAT checks or enabled on-demand usage. |
| Phone, Time, Date, Currency, Language, Emoji, Bank, Point | Optional detail in the same pooled request on every plan. |
| Country, State, District, City, Postal | The place profile on paid plans, including demographic and tax facts where held. |
| Name, Industry | Name evidence or the industry definition profile on paid plans. |
| Vehicle, Tariff, Company | The complete product detail bag on paid plans. |
| Weather | Specialist current measurements and the existing forecast, alert, air and history bag on paid plans. |
| Carrier, HLR | Optional diagnostic detail within the same metered core unit, including Free allowance units. No second gate or additional check. |

Email deep includes mailbox status and the reason for the result, plus a suggested first name, no-reply flag, plus-address tag and mail service. The suggested name is not a verified identity. Unavailable details are null.

Reasons include `accepted`, `invalid_format`, `invalid_domain`, `no_mail_server`, `mailbox_not_found`, `mailbox_disabled`, `mailbox_full`, `catchall`, `disposable`, `temporary_failure`, `rejected` and `unconfirmed`.

Carrier, caller, and HLR are separate metered operations. Choose them explicitly when you need their answers. Ordinary lookups retry twice by default. Metered checks use one attempt by default. Setting retries explicitly can repeat paid usage.

Without `deep`, the response omits that key. When requested, it is an empty object if access is locked or the operation has no deep fields. Otherwise it contains the available fields. A missing or null field means unknown.

```python
ip = parse.ip("52.94.76.10", deep=True)
ip.get("deep", {}).get("datacenter")  # True, False, or None
```

## Errors

Every non-2xx response raises `ParseAPIError` with `status`, `code`, `docs`, and `request_id`. Branch on `code`.

```python
from parseapi import ParseAPIError

try:
    parse.city("atlantis")
except ParseAPIError as err:
    if err.code == "not_found":
        ...  # no such city
```

Network and decoding failures keep their native error types. Responses such as `valid: false` are successful API answers, not exceptions.

## Options

```python
parse = ParseAPI(
    "your-api-key",
    timeout=10.0,  # timeout for each connect, read, write, or pool phase
)
```

Requires Python 3.9 or later. One dependency (httpx).

Ordinary lookups retry network failures, 429, and 500/502/503/504 responses twice by default. Carrier, caller, HLR, and email or VAT with `deep=True` make one attempt by default. Address with `deep=True` also uses one attempt, reserving the same behavior for future verification.

An explicit client `retries` setting overrides those defaults; `retries=0` always makes one attempt. Another attempt can consume additional usage if the earlier response was lost. Cancelling an async task stops the call and any retry wait. Automatic redirects are disabled.

Automatic retries wait at most five seconds per attempt. A longer valid `Retry-After` returns the original API error immediately without retrying early. Read `retry_after` on the error for the original header, or null when absent.

## Docs

Full field reference for every endpoint: [parseapi.com/docs](https://parseapi.com/docs)

## Card

Send 2–11 leading digits as a string. Core returns `bin`, `brand`, `brand_name`
and a CDN SVG `logo`. Brand detection uses reviewed network rules independently
of issuer records. Unknown or ambiguous prefixes return null brand fields and a
generic logo; a known network without reviewed artwork also uses the generic logo.

Optional Deep adds `prefix`, `issuer`, `country`, `type` and `prepaid`, included
in the same pooled request on every plan. Six or more digits enable directory
matching. Fewer digits return all-null Deep fields. Compare `deep.prefix` with
`bin`: equal is an exact recorded match; shorter is broader; null is no match.
The longest row wins, including null fields. `prepaid: null` means unknown, not
false. This is partial reference data, not card validity or payment acceptance.

```python
card = parse.card("51")
print(card["brand"], card["logo"])
details = parse.card("43737400", deep=True)
print(details["deep"]["prefix"], details["deep"]["issuer"])
```

Leading zeros are preserved. Only ASCII spaces, tabs, CR, LF and hyphens are
removed; raw input is limited to 64 characters. Invalid prefixes are rejected
before dispatch, accepted input is forwarded unchanged. Never send a full card number.

## Optional detail

The default response answers the common task. Ask for `deep` when you need more detail about that same result. Core fields stay equal. City, Company directory, Industry and Emoji searches put detail inside each result. Postal nearby and distance put metropolitan detail beside the entity it describes. Time conversion keeps target detail in `to.deep` or each `targets` item; only the source has `deep.next_dst`.

```python
basic = parse.time("America/New_York")
detail = parse.time("America/New_York", deep=True)
print(basic["at"], detail.get("deep", {}).get("next_dst"))
```

## Stack API

```python
result = parse.stack("example.com")
# AsyncParseAPI exposes the same calls with await.
```

Pass a public hostname without a scheme, path, port or IP address. Stack returns the checked URL and `checked_at` time, followed by `scope`, `pages` and `partial`. `scope` is `homepage` or `site`; `pages` counts successfully checked HTML pages. `partial` is true for homepage-only or incomplete bounded site checks. False means the known in-scope candidates were completed, not that every page on a website was visited. A homepage result has `scope: "homepage"`, `pages: 1` and `partial: true`.

`cms`, `servers`, `frameworks`, `ecommerce`, `analytics`, `chat`, `payments` and `hosting` are arrays because a site can use several technologies in each category. Each entry contains `technology`, `name` and nullable `version`. Technology codes are open strings. A successful check uses empty arrays for categories with no matches. When no HTML page could be checked, `checked_at` and all categories are null, `pages` is 0 and `partial` is null. Unknown or conflicting versions are null. Missing detections do not prove absence.

Successful checks may be reused for up to 24 hours. `pretty` optionally formats the wire JSON. Stack uses your plan's request allowance and API version 2.0.0 selected by this client.

Stack defaults to a 35-second transport timeout so a first scan has time to finish. Other lookups retain their 10-second default. An explicit client timeout takes precedence.

Vehicle lookups use `vin` as the input and response field. Existing VIN methods remain available for compatibility.

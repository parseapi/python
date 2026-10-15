# Changelog

## 1.10.0 — 2026-10-15

- Add compatible City resource/list, spelling-search, geographic-filter, pagination, hierarchy, relationship and distance support.
- Keep existing City calls and response defaults compatible; expose ambiguity candidates when requested.
- Remove population observation periods from public examples; retain published typed members only for source compatibility.

## 1.9.1 — 2026-10-12

- Add Emoji search/browse, categories, catalog, metadata, parsing and conversion; keep existing lookup calls and response decoding compatible.
- Support optional SVG/PNG artwork and translated names. Preserve API 2.0.0 selection, plans and existing non-Emoji behavior.

## 1.9.0 — 2026-09-29

- Add Company stable-ID lookup, candidate search and coverage for the current public-company cohort.
- Preserve existing Company calls and all published compatibility methods.

## 1.8.0 — 2026-09-25

- Add Bank diagnostics, POST requests, requirements and explicit US ACH helpers; Card Core and optional Deep; Provider; Industry; and Vehicle.
- Preserve published IBAN, BIN, NPI, NAICS and VIN methods and response types alongside the new names.
- Respect long Retry-After responses without retrying early and expose the raw header as optional error metadata.
- Retain released Time, Tariff, Postal and Elevation behavior. Expanded Company directory changes are deferred.

## 1.7.0 - 2026-09-24

- Add exact Tariff edition/date selection, answering metadata, contextual search lineage and explanatory null reasons. Explicit selections reject unsupported or mismatched server responses.

## 1.6.0 - 2026-09-24

Adds Time location inputs and explicit ambiguity candidates, filtered timezone discovery, multiple conversion targets, wall-time disambiguation, and standard/seasonal offset detail. Existing Timezone methods and API 2.0.0 selection remain unchanged.

## 1.4.0 - 2026-09-24

Adds Australian Postal suburb choices while preserving null, empty, and ambiguous results. Existing calls, compact nearby/distance responses, and API contract `2.0.0` remain unchanged.

## 1.3.0 - Unreleased

Adds Stack site inventory lookup with eight technology category arrays, nullable versions, and explicit page coverage. Stack uses a 35-second default attempt timeout while explicit caller settings remain honored. Existing calls and API contract `2.0.0` remain unchanged.

## 1.1.0 - 2026-09-20

Email deep results now include nullable suggested first name, no-reply flag, plus-address tag, mail provider, verification status and reason. Existing lookup calls, retry defaults and API contract `2.0.0` remain unchanged. Missing details remain unknown, and suggested names do not verify identity.

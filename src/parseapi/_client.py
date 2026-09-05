from __future__ import annotations

import os
import math
import random
import time
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

VERSION = "0.3.0"
DEFAULT_BASE_URL = "https://api.parseapi.com"
DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRIES = 2
RETRY_STATUS = {429, 500, 502, 503, 504}
RETRY_AFTER_CAP = 5.0

Json = Dict[str, Any]


class ParseAPIError(Exception):
    """Every non-2xx response from the API. Branch on `code`, never on the message."""

    def __init__(self, status: int, code: str, message: str, docs: Optional[str], request_id: Optional[str]):
        super().__init__(message)
        self.status = status
        self.code = code
        self.docs = docs
        self.request_id = request_id


def _seg(value: Any) -> str:
    return quote(str(value), safe="")


def _retry_delay(attempt: int, retry_after: Optional[str]) -> float:
    if retry_after:
        try:
            seconds = float(retry_after)
            if math.isfinite(seconds) and seconds >= 0:
                return min(seconds, RETRY_AFTER_CAP)
        except ValueError:
            try:
                parsed = parsedate_to_datetime(retry_after)
                if parsed.tzinfo is not None:
                    return min(max(parsed.timestamp() - time.time(), 0), RETRY_AFTER_CAP)
            except (ValueError, TypeError, OverflowError):
                pass
    return random.random() * 0.25 * (2**attempt)


def _error_from(response: httpx.Response) -> ParseAPIError:
    try:
        body = response.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    return ParseAPIError(
        status=response.status_code,
        code=body.get("code") if isinstance(body.get("code"), str) else "unknown_error",
        message=body.get("message")
        if isinstance(body.get("message"), str)
        else f"Request failed with status {response.status_code}",
        docs=body.get("docs") if isinstance(body.get("docs"), str) else None,
        request_id=body.get("request_id") if isinstance(body.get("request_id"), str) else None,
    )


def _clean(params: Dict[str, Any]) -> Dict[str, Any]:
    return {name: value for name, value in params.items() if value is not None and value is not False}


def _default_retries(path: str, params: Optional[Dict[str, Any]]) -> int:
    product = path.split("/")[1]
    metered = product in {"carrier", "caller", "hlr", "litigator", "reassigned"}
    metered = metered or (product in {"email", "vat", "address"} and (params or {}).get("deep") is True)
    return 0 if metered else DEFAULT_RETRIES


class _Config:
    def __init__(
        self,
        api_key: Optional[str],
        base_url: Optional[str],
        timeout: Optional[float],
        retries: Optional[int],
    ):
        key = api_key or os.environ.get("PARSEAPI_KEY")
        if not key:
            raise ValueError("parseapi: missing API key. Pass one or set PARSEAPI_KEY.")
        self.api_key = key
        self.base_url = (base_url or os.environ.get("PARSEAPI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = DEFAULT_TIMEOUT if timeout is None else timeout
        self.retries = retries
        if type(self.timeout) not in (int, float) or not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("parseapi: timeout must be a finite positive number.")
        if self.retries is not None and (type(self.retries) is not int or self.retries < 0):
            raise ValueError("parseapi: retries must be a non-negative integer.")

    def headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key, "User-Agent": f"parseapi-python/{VERSION}"}


class ParseAPI:
    """Synchronous client. `parse = ParseAPI()` reads PARSEAPI_KEY from the env."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ):
        self._config = _Config(api_key, base_url, timeout, retries)
        self._http = httpx.Client(
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            headers=self._config.headers(),
            transport=transport,
        )
        self.ip = _IpSync(self)
        self.continent = _ContinentSync(self)
        self.bloc = _BlocSync(self)
        self.country = _CountrySync(self)
        self.state = _StateSync(self)
        self.city = _CitySync(self)
        self.postal = _PostalSync(self)
        self.currency = _CurrencySync(self)
        self.holiday = _HolidaySync(self)
        self.emoji = _EmojiSync(self)
        self.tariff = _TariffSync(self)
        self.date = _DateSync(self)
        self.timezone = _TimezoneSync(self)
        self.address = _AddressSync(self)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "ParseAPI":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Json:
        retries = self._config.retries if self._config.retries is not None else _default_retries(path, params)
        attempt = 0
        while True:
            try:
                response = self._http.get(path, params=_clean(params or {}), headers=headers)
            except httpx.HTTPError:
                if attempt < retries:
                    time.sleep(_retry_delay(attempt, None))
                    attempt += 1
                    continue
                raise
            if response.is_success:
                return response.json()
            if response.status_code in RETRY_STATUS and attempt < retries:
                time.sleep(_retry_delay(attempt, response.headers.get("Retry-After")))
                attempt += 1
                continue
            raise _error_from(response)

    # Plain methods (no subresources)

    def district(self, code: str, *, country: Optional[str] = None, state: Optional[str] = None) -> Json:
        return self._get(f"/district/{_seg(code)}", {"country": country, "state": state})

    def email(self, email: str, *, deep: bool = False) -> Json:
        return self._get(f"/email/{_seg(email)}", {"deep": deep})

    def vat(
        self,
        number: str,
        *,
        country: Optional[str] = None,
        deep: bool = False,
        from_vat: Optional[str] = None,
    ) -> Json:
        return self._get(f"/vat/{_seg(number)}", {"country": country, "deep": deep, "from": from_vat})

    def iban(self, iban: str, *, country: Optional[str] = None) -> Json:
        return self._get(f"/iban/{_seg(iban)}", {"country": country})

    def npi(self, npi: str, *, deep: bool = False) -> Json:
        return self._get(f"/npi/{_seg(npi)}", {"deep": deep})

    def phone(self, number: str, *, country: Optional[str] = None, deep: bool = False) -> Json:
        return self._get(f"/phone/{_seg(number)}", {"country": country, "deep": deep})

    def carrier(self, number: str, *, country: Optional[str] = None) -> Json:
        return self._get(f"/carrier/{_seg(number)}", {"country": country})

    def caller(self, number: str, *, country: Optional[str] = None) -> Json:
        return self._get(f"/caller/{_seg(number)}", {"country": country})

    def hlr(self, number: str, *, country: Optional[str] = None) -> Json:
        return self._get(f"/hlr/{_seg(number)}", {"country": country})

    def domain(self, domain: str, *, deep: bool = False) -> Json:
        return self._get(f"/domain/{_seg(domain)}", {"deep": deep})

    def asn(self, asn: str) -> Json:
        return self._get(f"/asn/{_seg(asn)}")

    def mac(self, mac: str) -> Json:
        return self._get(f"/mac/{_seg(mac)}")

    def mx(self, domain: str) -> Json:
        return self._get(f"/mx/{_seg(domain)}")

    def useragent(self, ua: str, *, deep: bool = False) -> Json:
        return self._get("/useragent", {"deep": deep}, headers={"User-Agent": ua})

    def vin(self, vin: str, *, deep: bool = False) -> Json:
        return self._get(f"/vin/{_seg(vin)}", {"deep": deep})

    def company(self, number: str, *, country: Optional[str] = None, deep: bool = False) -> Json:
        return self._get(f"/company/{_seg(number)}", {"country": country, "deep": deep})

    def language(self, code: str) -> Json:
        return self._get(f"/language/{_seg(code)}")

    def name(self, name: str) -> Json:
        return self._get(f"/name/{_seg(name)}")

    def elevation(self, lat: float, lon: float) -> Json:
        return self._get("/elevation", {"lat": lat, "lon": lon})

    def point(self, lat: float, lon: float, *, deep: bool = False) -> Json:
        return self._get("/point", {"lat": lat, "lon": lon, "deep": deep})

    def weather(self, lat: float, lon: float, *, deep: bool = False, date: Optional[str] = None) -> Json:
        return self._get("/weather", {"lat": lat, "lon": lon, "deep": deep, "date": date})


class _IpSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, ip: str, *, deep: bool = False) -> Json:
        return self._client._get(f"/ip/{_seg(ip)}", {"deep": deep})

    def self(self, *, deep: bool = False) -> Json:
        return self._client._get("/ip", {"deep": deep})


class _ContinentSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, code: str) -> Json:
        return self._client._get(f"/continent/{_seg(code)}")

    def countries(self, code: str) -> Json:
        return self._client._get(f"/continent/{_seg(code)}/countries")


class _BlocSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, code: str) -> Json:
        return self._client._get(f"/bloc/{_seg(code)}")

    def countries(self, code: str) -> Json:
        return self._client._get(f"/bloc/{_seg(code)}/countries")


class _CountrySync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, code: str) -> Json:
        return self._client._get(f"/country/{_seg(code)}")

    def states(self, code: str) -> Json:
        return self._client._get(f"/country/{_seg(code)}/states")


class _StateSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, code: str, *, country: Optional[str] = None) -> Json:
        return self._client._get(f"/state/{_seg(code)}", {"country": country})

    def districts(self, code: str, *, country: Optional[str] = None) -> Json:
        return self._client._get(f"/state/{_seg(code)}/districts", {"country": country})


class _CitySync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, name: str, *, country: Optional[str] = None, state: Optional[str] = None) -> Json:
        return self._client._get(f"/city/{_seg(name)}", {"country": country, "state": state})

    def id(self, id: str) -> Json:
        return self._client._get(f"/city/id/{_seg(id)}")

    def search(
        self,
        query: str,
        *,
        country: Optional[str] = None,
        state: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Json:
        return self._client._get("/city", {"q": query, "country": country, "state": state, "limit": limit})

    def nearest(self, lat: float, lon: float) -> Json:
        return self._client._get("/city", {"lat": lat, "lon": lon})

    def nearby(
        self,
        name: str,
        *,
        radius: Optional[float] = None,
        unit: Optional[str] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Json:
        return self._client._get(
            f"/city/{_seg(name)}/nearby",
            {"radius": radius, "unit": unit, "country": country, "state": state, "limit": limit},
        )


class _PostalSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, code: str, *, country: Optional[str] = None) -> Json:
        return self._client._get(f"/postal/{_seg(code)}", {"country": country})

    def nearby(
        self,
        code: str,
        *,
        country: Optional[str] = None,
        radius: Optional[float] = None,
        unit: Optional[str] = None,
    ) -> Json:
        return self._client._get(f"/postal/{_seg(code)}/nearby", {"country": country, "radius": radius, "unit": unit})

    def distance(self, from_postal: str, to_postal: str, *, country: Optional[str] = None) -> Json:
        return self._client._get(f"/postal/{_seg(from_postal)}/distance/{_seg(to_postal)}", {"country": country})


class _CurrencySync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, code: str) -> Json:
        return self._client._get(f"/currency/{_seg(code)}")

    def rate(
        self, base: str, quote_currency: str, *, date: Optional[str] = None, amount: Optional[float] = None
    ) -> Json:
        return self._client._get(
            f"/currency/{_seg(base)}/{_seg(quote_currency)}", {"date": date, "amount": amount}
        )


class _HolidaySync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, country: str, *, year: Optional[int] = None) -> Json:
        return self._client._get(f"/holiday/{_seg(country)}", {"year": year})

    def date(self, country: str, date: str) -> Json:
        return self._client._get(f"/holiday/{_seg(country)}/{_seg(date)}")


class _EmojiSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, emoji: str) -> Json:
        return self._client._get(f"/emoji/{_seg(emoji)}")

    def search(self, query: str, *, limit: Optional[int] = None) -> Json:
        return self._client._get("/emoji", {"q": query, "limit": limit})


class _TariffSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, code: str, *, deep: bool = False, origin: Optional[str] = None) -> Json:
        return self._client._get(f"/tariff/{_seg(code)}", {"deep": deep, "origin": origin})

    def search(self, query: str) -> Json:
        return self._client._get("/tariff", {"q": query})


class AsyncParseAPI:
    """Async client. `parse = AsyncParseAPI()` reads PARSEAPI_KEY from the env."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self._config = _Config(api_key, base_url, timeout, retries)
        self._http = httpx.AsyncClient(
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            headers=self._config.headers(),
            transport=transport,
        )
        self.ip = _IpAsync(self)
        self.continent = _ContinentAsync(self)
        self.bloc = _BlocAsync(self)
        self.country = _CountryAsync(self)
        self.state = _StateAsync(self)
        self.city = _CityAsync(self)
        self.postal = _PostalAsync(self)
        self.currency = _CurrencyAsync(self)
        self.holiday = _HolidayAsync(self)
        self.emoji = _EmojiAsync(self)
        self.tariff = _TariffAsync(self)
        self.date = _DateAsync(self)
        self.timezone = _TimezoneAsync(self)
        self.address = _AddressAsync(self)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncParseAPI":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> Json:
        import asyncio

        retries = self._config.retries if self._config.retries is not None else _default_retries(path, params)
        attempt = 0
        while True:
            try:
                response = await self._http.get(path, params=_clean(params or {}), headers=headers)
            except httpx.HTTPError:
                if attempt < retries:
                    await asyncio.sleep(_retry_delay(attempt, None))
                    attempt += 1
                    continue
                raise
            if response.is_success:
                return response.json()
            if response.status_code in RETRY_STATUS and attempt < retries:
                await asyncio.sleep(_retry_delay(attempt, response.headers.get("Retry-After")))
                attempt += 1
                continue
            raise _error_from(response)

    async def district(self, code: str, *, country: Optional[str] = None, state: Optional[str] = None) -> Json:
        return await self._get(f"/district/{_seg(code)}", {"country": country, "state": state})

    async def email(self, email: str, *, deep: bool = False) -> Json:
        return await self._get(f"/email/{_seg(email)}", {"deep": deep})

    async def vat(
        self,
        number: str,
        *,
        country: Optional[str] = None,
        deep: bool = False,
        from_vat: Optional[str] = None,
    ) -> Json:
        return await self._get(f"/vat/{_seg(number)}", {"country": country, "deep": deep, "from": from_vat})

    async def iban(self, iban: str, *, country: Optional[str] = None) -> Json:
        return await self._get(f"/iban/{_seg(iban)}", {"country": country})

    async def npi(self, npi: str, *, deep: bool = False) -> Json:
        return await self._get(f"/npi/{_seg(npi)}", {"deep": deep})

    async def phone(self, number: str, *, country: Optional[str] = None, deep: bool = False) -> Json:
        return await self._get(f"/phone/{_seg(number)}", {"country": country, "deep": deep})

    async def carrier(self, number: str, *, country: Optional[str] = None) -> Json:
        return await self._get(f"/carrier/{_seg(number)}", {"country": country})

    async def caller(self, number: str, *, country: Optional[str] = None) -> Json:
        return await self._get(f"/caller/{_seg(number)}", {"country": country})

    async def hlr(self, number: str, *, country: Optional[str] = None) -> Json:
        return await self._get(f"/hlr/{_seg(number)}", {"country": country})

    async def domain(self, domain: str, *, deep: bool = False) -> Json:
        return await self._get(f"/domain/{_seg(domain)}", {"deep": deep})

    async def asn(self, asn: str) -> Json:
        return await self._get(f"/asn/{_seg(asn)}")

    async def mac(self, mac: str) -> Json:
        return await self._get(f"/mac/{_seg(mac)}")

    async def mx(self, domain: str) -> Json:
        return await self._get(f"/mx/{_seg(domain)}")

    async def useragent(self, ua: str, *, deep: bool = False) -> Json:
        return await self._get("/useragent", {"deep": deep}, headers={"User-Agent": ua})

    async def vin(self, vin: str, *, deep: bool = False) -> Json:
        return await self._get(f"/vin/{_seg(vin)}", {"deep": deep})

    async def company(self, number: str, *, country: Optional[str] = None, deep: bool = False) -> Json:
        return await self._get(f"/company/{_seg(number)}", {"country": country, "deep": deep})

    async def language(self, code: str) -> Json:
        return await self._get(f"/language/{_seg(code)}")

    async def name(self, name: str) -> Json:
        return await self._get(f"/name/{_seg(name)}")

    async def elevation(self, lat: float, lon: float) -> Json:
        return await self._get("/elevation", {"lat": lat, "lon": lon})

    async def point(self, lat: float, lon: float, *, deep: bool = False) -> Json:
        return await self._get("/point", {"lat": lat, "lon": lon, "deep": deep})

    async def weather(self, lat: float, lon: float, *, deep: bool = False, date: Optional[str] = None) -> Json:
        return await self._get("/weather", {"lat": lat, "lon": lon, "deep": deep, "date": date})


class _IpAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, ip: str, *, deep: bool = False) -> Json:
        return await self._client._get(f"/ip/{_seg(ip)}", {"deep": deep})

    async def self(self, *, deep: bool = False) -> Json:
        return await self._client._get("/ip", {"deep": deep})


class _ContinentAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, code: str) -> Json:
        return await self._client._get(f"/continent/{_seg(code)}")

    async def countries(self, code: str) -> Json:
        return await self._client._get(f"/continent/{_seg(code)}/countries")


class _BlocAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, code: str) -> Json:
        return await self._client._get(f"/bloc/{_seg(code)}")

    async def countries(self, code: str) -> Json:
        return await self._client._get(f"/bloc/{_seg(code)}/countries")


class _CountryAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, code: str) -> Json:
        return await self._client._get(f"/country/{_seg(code)}")

    async def states(self, code: str) -> Json:
        return await self._client._get(f"/country/{_seg(code)}/states")


class _StateAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, code: str, *, country: Optional[str] = None) -> Json:
        return await self._client._get(f"/state/{_seg(code)}", {"country": country})

    async def districts(self, code: str, *, country: Optional[str] = None) -> Json:
        return await self._client._get(f"/state/{_seg(code)}/districts", {"country": country})


class _CityAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, name: str, *, country: Optional[str] = None, state: Optional[str] = None) -> Json:
        return await self._client._get(f"/city/{_seg(name)}", {"country": country, "state": state})

    async def id(self, id: str) -> Json:
        return await self._client._get(f"/city/id/{_seg(id)}")

    async def search(
        self,
        query: str,
        *,
        country: Optional[str] = None,
        state: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Json:
        return await self._client._get("/city", {"q": query, "country": country, "state": state, "limit": limit})

    async def nearest(self, lat: float, lon: float) -> Json:
        return await self._client._get("/city", {"lat": lat, "lon": lon})

    async def nearby(
        self,
        name: str,
        *,
        radius: Optional[float] = None,
        unit: Optional[str] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Json:
        return await self._client._get(
            f"/city/{_seg(name)}/nearby",
            {"radius": radius, "unit": unit, "country": country, "state": state, "limit": limit},
        )


class _PostalAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, code: str, *, country: Optional[str] = None) -> Json:
        return await self._client._get(f"/postal/{_seg(code)}", {"country": country})

    async def nearby(
        self,
        code: str,
        *,
        country: Optional[str] = None,
        radius: Optional[float] = None,
        unit: Optional[str] = None,
    ) -> Json:
        return await self._client._get(
            f"/postal/{_seg(code)}/nearby", {"country": country, "radius": radius, "unit": unit}
        )

    async def distance(self, from_postal: str, to_postal: str, *, country: Optional[str] = None) -> Json:
        return await self._client._get(f"/postal/{_seg(from_postal)}/distance/{_seg(to_postal)}", {"country": country})


class _CurrencyAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, code: str) -> Json:
        return await self._client._get(f"/currency/{_seg(code)}")

    async def rate(
        self, base: str, quote_currency: str, *, date: Optional[str] = None, amount: Optional[float] = None
    ) -> Json:
        return await self._client._get(
            f"/currency/{_seg(base)}/{_seg(quote_currency)}", {"date": date, "amount": amount}
        )


class _HolidayAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, country: str, *, year: Optional[int] = None) -> Json:
        return await self._client._get(f"/holiday/{_seg(country)}", {"year": year})

    async def date(self, country: str, date: str) -> Json:
        return await self._client._get(f"/holiday/{_seg(country)}/{_seg(date)}")


class _EmojiAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, emoji: str) -> Json:
        return await self._client._get(f"/emoji/{_seg(emoji)}")

    async def search(self, query: str, *, limit: Optional[int] = None) -> Json:
        return await self._client._get("/emoji", {"q": query, "limit": limit})


class _TariffAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, code: str, *, deep: bool = False, origin: Optional[str] = None) -> Json:
        return await self._client._get(f"/tariff/{_seg(code)}", {"deep": deep, "origin": origin})

    async def search(self, query: str) -> Json:
        return await self._client._get("/tariff", {"q": query})


class _DateSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, date: str, *, format: Optional[str] = None, to: Optional[str] = None) -> Json:
        return self._client._get(f"/date/{_seg(date)}", {"format": format, "to": to})

    def today(self, *, to: Optional[str] = None) -> Json:
        return self._client._get("/date", {"to": to})


class _DateAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, date: str, *, format: Optional[str] = None, to: Optional[str] = None) -> Json:
        return await self._client._get(f"/date/{_seg(date)}", {"format": format, "to": to})

    async def today(self, *, to: Optional[str] = None) -> Json:
        return await self._client._get("/date", {"to": to})


class _TimezoneSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, id: str, *, at: Optional[str] = None, to: Optional[str] = None) -> Json:
        return self._client._get(f"/timezone/{_seg(id)}", {"at": at, "to": to})

    def at(self, lat: float, lon: float, *, at: Optional[str] = None) -> Json:
        return self._client._get("/timezone", {"lat": lat, "lon": lon, "at": at})


class _AddressSync:
    def __init__(self, client: ParseAPI):
        self._client = client

    def __call__(self, address: str, *, country: Optional[str] = None, deep: bool = False) -> Json:
        return self._client._get(f"/address/{_seg(address)}", {"country": country, "deep": deep})

    def search(self, query: str, *, country: Optional[str] = None, postal: Optional[str] = None,
        city: Optional[str] = None, state: Optional[str] = None, ip: Optional[str] = None) -> Json:
        return self._client._get("/address", {"q": query, "country": country, "postal": postal, "city": city, "state": state, "ip": ip})


class _TimezoneAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, id: str, *, at: Optional[str] = None, to: Optional[str] = None) -> Json:
        return await self._client._get(f"/timezone/{_seg(id)}", {"at": at, "to": to})

    async def at(self, lat: float, lon: float, *, at: Optional[str] = None) -> Json:
        return await self._client._get("/timezone", {"lat": lat, "lon": lon, "at": at})


class _AddressAsync:
    def __init__(self, client: AsyncParseAPI):
        self._client = client

    async def __call__(self, address: str, *, country: Optional[str] = None, deep: bool = False) -> Json:
        return await self._client._get(f"/address/{_seg(address)}", {"country": country, "deep": deep})

    async def search(self, query: str, *, country: Optional[str] = None, postal: Optional[str] = None,
        city: Optional[str] = None, state: Optional[str] = None, ip: Optional[str] = None) -> Json:
        return await self._client._get("/address", {"q": query, "country": country, "postal": postal, "city": city, "state": state, "ip": ip})

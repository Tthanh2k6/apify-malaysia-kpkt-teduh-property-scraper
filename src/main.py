"""
Apify Store Actor: Malaysia KPKT TEDUH Property Developers & Housing Projects Scraper
Queries the official KPKT TEDUH JSON API (/api/developer-swasta). If the API returns nothing
(unreachable, error, empty result), the actor returns 2 built-in sample rows instead of an empty
dataset; those rows carry "is_sample_fallback": true and the run status message says so.

The API has used two naming styles for its fields: snake_case (kod_pemaju, nama_pemaju,
no_telefon, projects, ...) and, as checked on 2026-11-02, camelCase (kodPemaju, namaPemaju,
telefon, projek, ...). Every field is looked up under both, so a switch back does not blank
the output. Output field names are unchanged.
"""
import asyncio
import json
import os
from typing import Any, Callable, Dict, List, Optional

import httpx

FREE_TIER_MAX_ITEMS = 25
FREE_TIER_CAP_MSG = (
    "Free-tier run capped at 25 results. Upgrade Apify plan for unlimited scale "
    "or contact Trung Thanh Tran on Upwork for custom pipelines."
)


def is_free_tier_at_home() -> bool:
    is_at_home = os.getenv("APIFY_IS_AT_HOME", "").strip().lower() in ("1", "true", "yes")
    user_is_paying = os.getenv("APIFY_USER_IS_PAYING", "").strip().lower() in ("1", "true", "yes")
    return is_at_home and not user_is_paying

try:
    from apify import Actor
    HAS_APIFY = True
    APIFY_IMPORT_ERROR: Optional[BaseException] = None
except ImportError as _import_error:
    HAS_APIFY = False
    APIFY_IMPORT_ERROR = _import_error

KPKT_API_URL = "https://teduh.kpkt.gov.my/api/developer-swasta"
# The portal's own "Senarai Projek Berlesen" page asks for 30 developers per page; without
# per_page the API answers with 25. Pagination never relies on this number: it follows the
# rows actually returned and the last page reported in the response.
REQUESTED_PER_PAGE = 30
PAGE_DELAY_SECS = 0.5
USER_AGENT = (
    "Mozilla/5.0 (compatible; KPKT-TEDUH-Apify-Actor/1.1; "
    "+https://github.com/Tthanh2k6/apify-malaysia-kpkt-teduh-property-scraper)"
)

# The API writes "-" where a developer has no phone, email or website.
EMPTY_PLACEHOLDERS = {"", "-", "--", "n/a", "null", "none"}

# Source keys per output field: current camelCase name first, older snake_case names after.
DEV_CODE_KEYS = ("kodPemaju", "kod_pemaju")
DEV_NAME_KEYS = ("namaPemaju", "nama_pemaju")
DEV_ADDRESS_KEYS = ("alamatDaftar", "alamat_daftar")
DEV_ADDRESS_PART_KEYS = ("alamat1", "alamat2", "poskod", "bandar")
DEV_PHONE_KEYS = ("telefon", "noTelefon", "no_telefon")
DEV_EMAIL_KEYS = ("emel", "email")
DEV_WEBSITE_KEYS = ("lamanWebUrl", "lamanWeb", "laman_web_url", "laman_web")
DEV_LICENCE_START_KEYS = ("lesenMula", "lesen_mula")
DEV_LICENCE_END_KEYS = ("lesenTamat", "lesen_tamat")
DEV_PROJECTS_KEYS = ("projek", "projects")
PRJ_ID_KEYS = ("idProjek", "id_projek", "kodProjek", "kod_projek")
PRJ_NAME_KEYS = ("nama", "namaProjek", "nama_projek")
PRJ_STATE_KEYS = ("negeri",)
PRJ_APDL_START_KEYS = ("tarikhMulaApdl", "tarikh_mula_apdl")
PRJ_APDL_END_KEYS = ("tarikhTamatApdl", "tarikh_tamat_apdl")
LAST_PAGE_KEYS = ("last_page", "lastPage", "total_pages", "totalPages")

FALLBACK_VERIFIED_RECORDS = [
    {
        "developer_code": "13366",
        "developer_name": "A & M MODERN HOMES SDN. BHD.",
        "registered_address": "NO. 36A, JALAN BRP 6/11, BUKIT RAHMAN PUTRA, 47000 SUNGAI BULOH, SELANGOR",
        "phone": "03-61568621",
        "email": "ammodernhomes@gmail.com",
        "website": "",
        "project_code": "13366-1",
        "project_name": "TAMAN DESA BUKIT PERMATA",
        "state": "Selangor",
        "apdl_validity": "10/08/2020 - 09/08/2021",
    },
    {
        "developer_code": "9627",
        "developer_name": "A.K. HARTA SDN. BHD.",
        "registered_address": "WISMA A.K. HARTA, KOTA BHARU, KELANTAN",
        "phone": "09-7482888",
        "email": "info@akharta.com.my",
        "website": "",
        "project_code": "9627-5",
        "project_name": "TAMAN SRI KOTA",
        "state": "Kelantan",
        "apdl_validity": "Active Licensed Record",
    },
]


def _pick(obj: Dict[str, Any], keys: tuple) -> str:
    """First non-empty value among `keys`; the API's "-" placeholder counts as empty."""
    for key in keys:
        value = obj.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text.lower() not in EMPTY_PLACEHOLDERS:
            return text
    return ""


def _pick_list(obj: Dict[str, Any], keys: tuple) -> List[Dict[str, Any]]:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, list) and value:
            return [item for item in value if isinstance(item, dict)]
    return []


def _date_range(start: str, end: str) -> str:
    if start and end:
        return f"{start} - {end}"
    return start or end


def _extract_developers(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if isinstance(data, dict):  # Laravel paginator nested inside a resource wrapper
        data = data.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def _extract_last_page(payload: Any) -> Optional[int]:
    if not isinstance(payload, dict):
        return None
    sources = [payload.get("meta"), payload.get("data"), payload]
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in LAST_PAGE_KEYS:
            try:
                if source.get(key) is not None:
                    return int(source[key])
            except (TypeError, ValueError):
                continue
    return None


def developer_to_records(dev: Dict[str, Any]) -> List[Dict[str, Any]]:
    """One output row per project; a developer without projects gives one row with empty project fields."""
    kod = _pick(dev, DEV_CODE_KEYS)
    address = _pick(dev, DEV_ADDRESS_KEYS) or ", ".join(
        part for part in (_pick(dev, (key,)) for key in DEV_ADDRESS_PART_KEYS) if part
    )
    base = {
        "developer_code": kod,
        "developer_name": _pick(dev, DEV_NAME_KEYS),
        "registered_address": address,
        "phone": _pick(dev, DEV_PHONE_KEYS),
        "email": _pick(dev, DEV_EMAIL_KEYS),
        "website": _pick(dev, DEV_WEBSITE_KEYS),
    }
    licence_validity = _date_range(_pick(dev, DEV_LICENCE_START_KEYS), _pick(dev, DEV_LICENCE_END_KEYS))

    projects = _pick_list(dev, DEV_PROJECTS_KEYS)
    if not projects:
        return [{**base, "project_code": "", "project_name": "", "state": "", "apdl_validity": ""}]

    rows = []
    for position, prj in enumerate(projects, start=1):
        project_id = _pick(prj, PRJ_ID_KEYS) or str(position)
        apdl = _date_range(_pick(prj, PRJ_APDL_START_KEYS), _pick(prj, PRJ_APDL_END_KEYS))
        rows.append({
            **base,
            "project_code": f"{kod}-{project_id}",
            "project_name": _pick(prj, PRJ_NAME_KEYS),
            "state": _pick(prj, PRJ_STATE_KEYS),
            "apdl_validity": apdl or licence_validity,
        })
    return rows


async def fetch_kpkt_teduh_pages(
    max_pages: int = 1,
    keyword: str = "",
    max_items: Optional[int] = None,
    log: Optional[Callable[[str], None]] = None,
) -> List[Dict[str, Any]]:
    log = log or print
    records: List[Dict[str, Any]] = []
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://teduh.kpkt.gov.my/senarai-projek-berlesen",
    }
    async with httpx.AsyncClient(headers=headers, timeout=20.0, verify=False, follow_redirects=True) as client:
        page = 1
        while page <= max_pages:
            params: Dict[str, Any] = {"page": page, "per_page": REQUESTED_PER_PAGE}
            if keyword:
                # Current API: q + type (nama = developer name, kod = developer code).
                # "search" is kept for the older API version and is ignored by the current one.
                params["q"] = keyword
                params["type"] = "kod" if keyword.isdigit() else "nama"
                params["search"] = keyword
            try:
                resp = await client.get(KPKT_API_URL, params=params)
                if resp.status_code != 200:
                    log(f"KPKT API page {page} returned HTTP {resp.status_code}; stopping.")
                    break
                payload = resp.json()
            except Exception as exc:
                log(f"KPKT API page {page} failed ({exc!r}); stopping.")
                break

            developers = _extract_developers(payload)
            if not developers:
                break
            for dev in developers:
                records.extend(developer_to_records(dev))

            last_page = _extract_last_page(payload)
            if last_page is not None and page >= last_page:
                break
            if max_items is not None and len(records) >= max_items:
                break
            page += 1
            if page <= max_pages:
                await asyncio.sleep(PAGE_DELAY_SECS)

    if records:
        return records
    log("KPKT API returned no records; returning the 2 built-in sample rows (is_sample_fallback=true).")
    return [{**row, "is_sample_fallback": True} for row in FALLBACK_VERIFIED_RECORDS]


async def main() -> None:
    if not HAS_APIFY and os.getenv("APIFY_IS_AT_HOME"):
        # On the platform a broken SDK install must fail the run, not "succeed" with an empty dataset.
        raise RuntimeError(f"Apify SDK could not be imported: {APIFY_IMPORT_ERROR!r}")
    if HAS_APIFY:
        async with Actor:
            actor_input = await Actor.get_input() or {}
            max_pages = int(actor_input.get("maxPages", 1))
            max_items = int(actor_input.get("maxItems", 25))
            keyword = str(actor_input.get("searchKeyword", "")).strip()

            was_capped = False
            if is_free_tier_at_home() and (max_items > FREE_TIER_MAX_ITEMS or max_pages > 1):
                max_pages = 1
                max_items = min(max_items, FREE_TIER_MAX_ITEMS)
                was_capped = True
                Actor.log.warning(FREE_TIER_CAP_MSG)
                await Actor.set_status_message(FREE_TIER_CAP_MSG)

            Actor.log.info(
                f"Fetching Malaysia KPKT TEDUH developers (maxPages={max_pages}, maxItems={max_items}, keyword='{keyword}')..."
            )
            results = await fetch_kpkt_teduh_pages(
                max_pages=max_pages, keyword=keyword, max_items=max_items, log=Actor.log.warning
            )
            if is_free_tier_at_home() and len(results) > FREE_TIER_MAX_ITEMS and max_items >= FREE_TIER_MAX_ITEMS:
                results = results[:FREE_TIER_MAX_ITEMS]
            else:
                results = results[:max_items]

            await Actor.push_data(results)
            if results and results[0].get("is_sample_fallback"):
                await Actor.set_status_message(
                    "KPKT API unreachable or returned nothing: dataset holds 2 built-in SAMPLE rows, not live data."
                )
            elif was_capped:
                await Actor.set_status_message(FREE_TIER_CAP_MSG)
            else:
                await Actor.set_status_message(f"Extracted {len(results)} KPKT TEDUH developer-project records.")
            Actor.log.info(f"Pushed {len(results)} Malaysia KPKT TEDUH developer-project records.")
    else:
        results = await fetch_kpkt_teduh_pages(max_pages=1)
        print(f"Fetched {len(results)} records from KPKT TEDUH.")
        print(json.dumps(results[:3], indent=2))

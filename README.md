# Malaysia KPKT TEDUH property developer and housing project scraper

On Apify Store: https://apify.com/thanh81646/malaysia-kpkt-teduh-property-developer-scraper

An Apify actor that reads Malaysia's KPKT TEDUH registry (`teduh.kpkt.gov.my`) of licensed private housing developers (Pemaju Perumahan Swasta) and their licensed projects, through the portal's public JSON endpoint `/api/developer-swasta`, and returns one row per developer and project.

## Status on 16 Nov 2026: the source API is down

A run on 16 Nov 2026 got HTTP 500 from `https://teduh.kpkt.gov.my/api/developer-swasta`. The error page comes from the portal's own database, which reports `No space left on device`; the portal homepage still answers 200. Until KPKT fixes it, every run returns only the two built-in sample rows described below. On 2 Nov 2026 the same endpoint worked and reported 6,548 developers and 27,280 projects (219 pages of 30).

## Output

One row per developer-project pair. A developer with no projects gives one row with empty project fields. Source names from the API (as of 2 Nov 2026) in brackets:

| Field | Source |
| --- | --- |
| `developer_code`, `developer_name` | `kodPemaju`, `namaPemaju` |
| `registered_address`, `phone`, `email`, `website` | `alamatDaftar`, `telefon`, `emel`, `lamanWebUrl` or `lamanWeb` |
| `project_name`, `state` | `projek[].nama`, `projek[].negeri` |
| `project_code` | `<developer_code>-<n>`, where `n` is the project's position in the developer's list. The API sends no project ID, so this is not an official KPKT code and can shift when the list changes. |
| `apdl_validity` | developer licence period `lesenMula - lesenTamat`; per-project APDL dates when the API sends them |

The API writes `-` when a developer has no phone, email or website; the actor outputs an empty string. Many developers have no phone or email in the registry. Older API versions used snake_case names (`kod_pemaju`, `nama_pemaju`, `projects`...); the actor reads both.

## Input

`maxPages` (default 1), `maxItems` (default 25) and an optional `searchKeyword` (developer name, or digits for a developer code). It requests 30 developers per page and stops at the last page the API reports. Apify free-tier runs are limited to 1 page and 25 rows. A full run through all pages has not been tested.

## Sample rows when the API fails

If the actor ends with zero records (first request non-200, timeout, invalid JSON, or an empty list, including a `searchKeyword` that matches nothing), it returns two hard-coded sample rows (`FALLBACK_VERIFIED_RECORDS` in `src/main.py`) instead of failing. Each has `"is_sample_fallback": true`, and the run's status message says so; the run still ends as succeeded. If later pages fail after some rows were fetched, the real rows are returned without samples.

Builds older than that field can be recognised by the two rows themselves: `13366` / `A & M MODERN HOMES SDN. BHD.` and `9627` / `A.K. HARTA SDN. BHD.`. Check the names, not just the codes: in the live API, code `13366` belongs to `128 ARA DAMANSARA SDN. BHD.`.

The HTTP client runs with TLS certificate verification turned off (`verify=False`).

## Use it

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")
run = client.actor("thanh81646/malaysia-kpkt-teduh-property-developer-scraper").call(run_input={})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    if not item.get("is_sample_fallback"):
        print(item)
```

In n8n or Make, use the Apify "Run an Actor" node with the same actor ID. Locally, `python -m src` runs one page and prints the first rows. `pytest` runs 4 offline tests.

For extra fields, scheduled runs into Google Sheets or a webhook, or another registry, email ttrungthanh90@gmail.com or message me on [Apify](https://apify.com/thanh81646).

## Legal note

The actor reads public, non-authenticated registry data published on `teduh.kpkt.gov.my`. It is not affiliated with or endorsed by KPKT. You are responsible for how you use the data, including Malaysia's Personal Data Protection Act.

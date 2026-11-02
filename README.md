# Malaysia KPKT TEDUH Property Developers & Housing Projects Scraper (`teduh.kpkt.gov.my`)

Extracts licensed private property developers (**Pemaju Perumahan Swasta**) and their registered housing projects (**Senarai Projek Berlesen**) directly from Malaysia's Ministry of Housing and Local Government (**KPKT TEDUH**) public JSON endpoint.

## Extracted fields

One row per developer-project pair (a developer with no projects gives one row with empty project fields). Source field names as returned by the API on 2 Nov 2026 are in brackets:

- `developer_code` (`kodPemaju`) and `developer_name` (`namaPemaju`)
- `registered_address` (`alamatDaftar`), `phone` (`telefon`), `email` (`emel`), `website` (`lamanWebUrl`, else `lamanWeb`)
- `project_name` (`projek[].nama`) and `state` (`projek[].negeri`)
- `project_code`: `<developer_code>-<n>`. The API currently sends no project ID, so `n` is the project's position (1, 2, 3...) in that developer's list; it is not an official KPKT code and can shift if the list changes.
- `apdl_validity`: the developer licence period (`lesenMula` - `lesenTamat`), the same for every project of a developer. If the API sends per-project APDL dates (older versions did), those are used instead.

The API writes `-` when a developer has no phone, email or website; the actor outputs an empty string instead. Many developers have no phone or email in the registry, so empty `phone`/`email` values are normal. `website` is also empty when the developer lists none (versions before 2 Nov 2026 filled in a `teduh.kpkt.gov.my/developer-swasta/<code>` link, which is not a page on the portal).

Earlier versions of the API used snake_case names (`kod_pemaju`, `nama_pemaju`, `no_telefon`, `laman_web`, `projects`, `nama_projek`, `tarikh_mula_apdl` / `tarikh_tamat_apdl`). The actor reads both styles, so output field names stay the same either way.

Input: `maxPages` (default 1), `maxItems` (default 25) and an optional `searchKeyword` (developer name; digits only searches by developer code). The actor asks the API for 30 developers per page and stops at the last page the API reports. Runs on the Apify free tier are limited to 1 page and 25 rows. The API reports its own totals: on 2 Nov 2026 that was 6,548 developers and 27,280 projects (219 pages of 30). A full run through every page has not been tested.

## Important: built-in sample rows when the API fails

The actor currently returns **2 hard-coded sample rows** (named `FALLBACK_VERIFIED_RECORDS` in `src/main.py`) instead of an error whenever it ends up with zero records. That happens if the first request to `https://teduh.kpkt.gov.my/api/developer-swasta` returns a non-200 status, times out, returns invalid JSON, or returns an empty list (including a `searchKeyword` that matches nothing). If later pages fail after some rows were fetched, the rows fetched so far are returned and no sample rows are added.

The sample rows are not live data: one has an APDL validity of `10/08/2020 - 09/08/2021`, the other `Active Licensed Record`. Each sample row has an extra field `"is_sample_fallback": true` (real rows do not have this field) and the run's status message says the dataset holds sample rows; the run itself still finishes as succeeded. Older builds did not add that field; to spot them there, check whether your dataset is exactly these two rows: `13366` / `A & M MODERN HOMES SDN. BHD.` / `13366-1` and `9627` / `A.K. HARTA SDN. BHD.` / `9627-5`. Check the names too, not just the codes: in the live API, code `13366` belongs to a different developer (`128 ARA DAMANSARA SDN. BHD.`) whose single project also gets `13366-1`. Treat such a result as "the API was unreachable", not as real results. Failed requests are logged as warnings in the run log.

The HTTP client also runs with TLS certificate verification turned off (`verify=False`).

---

## Calling it from Python and n8n / Make.com

### Python (`apify-client`)

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")
run = client.actor("thanh81646/malaysia-kpkt-teduh-property-developer-scraper").call(run_input={})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
```

### n8n / Make.com

Use the Apify "Run an Actor" node/module with the actor ID `thanh81646/malaysia-kpkt-teduh-property-developer-scraper` and map the dataset items to Google Sheets, a CRM or a database.

---

## Author

Trung Thanh Tran: [Upwork](https://www.upwork.com/freelancers/trungthanhtrandev) · [GitHub](https://github.com/Tthanh2k6) · [Apify](https://apify.com/thanh81646)

---

## Legal note

**Nominative Fair Use — Public Non-Authenticated Factual Data Only:** This Actor is an independent data-formatting utility accessing publicly available, non-authenticated government registry records published on `teduh.kpkt.gov.my`. It is not affiliated with, endorsed by, or officially connected to Malaysia's Ministry of Housing and Local Government (KPKT). All agency and portal names are used strictly for descriptive identification (*nominative fair use*). Users act as independent Data Controllers responsible for complying with Malaysia's PDPA and applicable local laws.

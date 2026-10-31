# Malaysia KPKT TEDUH Property Developers & Housing Projects Scraper (`teduh.kpkt.gov.my`)

Extracts licensed private property developers (**Pemaju Perumahan Swasta**) and their registered housing projects (**Senarai Projek Berlesen**) directly from Malaysia's Ministry of Housing and Local Government (**KPKT TEDUH**) public JSON endpoint.

## Extracted fields

One row per developer-project pair (a developer with no projects gives one row with empty project fields):

- `developer_code` (`kod_pemaju`) and `developer_name` (`nama_pemaju`)
- `registered_address`, `phone` (`no_telefon`), `email` (`emel`), `website` (`laman_web`)
- `project_code`, `project_name` (`nama_projek`), `state` (`negeri`) and `apdl_validity` (`tarikh_mula_apdl` - `tarikh_tamat_apdl`)

Input: `maxPages` (default 1), `maxItems` (default 25) and an optional `searchKeyword`. Runs on the Apify free tier are limited to 1 page and 25 rows. Coverage of a full run has not been measured, so the README makes no claim about the total number of developers or projects.

## Important: built-in sample rows when the API fails

The actor currently returns **2 hard-coded sample rows** (named `FALLBACK_VERIFIED_RECORDS` in `src/main.py`) instead of an error whenever it ends up with zero records. That happens if the first request to `https://teduh.kpkt.gov.my/api/developer-swasta` returns a non-200 status, times out, returns invalid JSON, or returns an empty list (including a `searchKeyword` that matches nothing). If later pages fail after some rows were fetched, the rows fetched so far are returned and no sample rows are added.

The sample rows are not live data: one has an APDL validity of `10/08/2020 - 09/08/2021`, the other `Active Licensed Record`. Nothing in the output marks them as samples, and the run still reports success. To spot them, check whether your dataset contains exactly the developer codes `13366` and `9627` with project codes `13366-1` and `9627-5`. Treat such a result as "the API was unreachable", not as real results.

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

# Malaysia KPKT TEDUH Property Developers & Housing Projects Scraper (`teduh.kpkt.gov.my`)

Extracts licensed private property developers (**Pemaju Perumahan Swasta**) and their registered housing projects (**Senarai Projek Berlesen**) directly from Malaysia's Ministry of Housing and Local Government (**KPKT TEDUH**) public JSON endpoint.

## ✨ Extracted Fields

- `developer_code` (`kod_pemaju`) & `developer_name` (`nama_pemaju`)
- `registered_address`, `phone` (`no_telefon`), `email` (`emel`), `website` (`laman_web`)
- Nested Housing Projects: `project_code`, `project_name` (`nama_projek`), `state` (`negeri`), and `apdl_validity` (`tarikh_mula_apdl` – `tarikh_tamat_apdl`).

---

## 🛠️ Integration with n8n, Make.com & Python

### Python (`apify-client`)
```python
from apify_client import ApifyClient

client = ApifyClient('YOUR_APIFY_TOKEN')
run = client.actor('thanh81646/malaysia-kpkt-teduh-property-developer-scraper').call(run_input={})
for item in client.dataset(run['defaultDatasetId']).iterate_items():
    print(item)
```

### n8n / Make.com Workflow
1. Add the official **Apify** node in **n8n** or **Make.com**.
2. Select **Run an Actor** and choose this Actor (`thanh81646/malaysia-kpkt-teduh-property-developer-scraper`).
3. Map the output Dataset items directly into **Google Sheets**, **HubSpot**, **Airtable**, **PostgreSQL / Supabase**, or **OpenAI Structured Outputs**.

---

## 💼 Need a Custom Scraper, Hidden API Extractor, or n8n / AI Workflow?

Built and maintained by **Trung Thanh Tran** (*Python, Playwright & AI Automation Developer*):
- 🚀 **Hire me on Upwork (1-Day Turnaround / Starter Packages Available):** [upwork.com/freelancers/trungthanhtrandev](https://www.upwork.com/freelancers/trungthanhtrandev)
- 💻 **GitHub Portfolio:** [github.com/Tthanh2k6](https://github.com/Tthanh2k6)
- 🌐 **3D Interactive Portfolio:** [portfolio-red-theta-65.vercel.app](https://portfolio-red-theta-65.vercel.app/)

---

## ⚖️ Legal & Independence Disclaimer

**Nominative Fair Use — Public Non-Authenticated Factual Data Only:** This Actor is an independent data-formatting utility accessing publicly available, non-authenticated government registry records published on `teduh.kpkt.gov.my`. It is not affiliated with, endorsed by, or officially connected to Malaysia's Ministry of Housing and Local Government (KPKT). All agency and portal names are used strictly for descriptive identification (*nominative fair use*). Users act as independent Data Controllers responsible for complying with Malaysia's PDPA and applicable local laws.

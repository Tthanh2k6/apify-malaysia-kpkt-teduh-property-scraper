import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import main as actor_main


def test_coerce_positive_int_handles_none_empty_and_bounds():
    assert actor_main._coerce_positive_int(None, 1) == 1
    assert actor_main._coerce_positive_int("", 25) == 25
    assert actor_main._coerce_positive_int("  ", 25) == 25
    assert actor_main._coerce_positive_int(0, 1) == 1
    assert actor_main._coerce_positive_int(-5, 25) == 25
    assert actor_main._coerce_positive_int(True, 1) == 1
    assert actor_main._coerce_positive_int("bad", 25) == 25
    assert actor_main._coerce_positive_int("3", 1) == 3
    assert actor_main._coerce_positive_int(10, 25) == 10


def test_extract_developers_and_last_page():
    payload = {
        "data": {"data": [{"kodPemaju": "1001", "namaPemaju": "DEV A"}], "last_page": "7"},
    }
    devs = actor_main._extract_developers(payload)
    assert len(devs) == 1
    assert devs[0]["kodPemaju"] == "1001"
    assert actor_main._extract_last_page(payload) == 7
    assert actor_main._extract_developers({"data": "invalid"}) == []
    assert actor_main._extract_last_page([]) is None


def test_developer_to_records_camel_snake_and_empty_projects():
    camel = {
        "kodPemaju": "1234",
        "namaPemaju": "ALPHA SDN BHD",
        "alamatDaftar": "1 JALAN ABC",
        "telefon": "-",
        "emel": "a@example.com",
        "lamanWebUrl": "https://alpha.example",
        "lesenMula": "01/01/2026",
        "lesenTamat": "31/12/2026",
        "projek": [{"nama": "TAMAN ONE", "negeri": "Selangor"}],
    }
    rows = actor_main.developer_to_records(camel)
    assert len(rows) == 1
    assert rows[0]["phone"] == ""
    assert rows[0]["project_code"] == "1234-1"
    assert rows[0]["apdl_validity"] == "01/01/2026 - 31/12/2026"

    snake_no_prj = {
        "kod_pemaju": "5678",
        "nama_pemaju": "BETA SDN BHD",
        "alamat1": "NO 2",
        "bandar": "KL",
        "no_telefon": "03-11112222",
        "projects": [],
    }
    rows2 = actor_main.developer_to_records(snake_no_prj)
    assert rows2 == [
        {
            "developer_code": "5678",
            "developer_name": "BETA SDN BHD",
            "registered_address": "NO 2, KL",
            "phone": "03-11112222",
            "email": "",
            "website": "",
            "project_code": "",
            "project_name": "",
            "state": "",
            "apdl_validity": "",
        }
    ]


def test_main_handles_none_inputs(monkeypatch):
    pushed = []
    statuses = []
    captured_calls = []

    class DummyActor:
        class log:
            @staticmethod
            def info(msg):
                pass

            @staticmethod
            def warning(msg):
                pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        @staticmethod
        async def get_input():
            return {"maxPages": None, "maxItems": None, "searchKeyword": None}

        @staticmethod
        async def push_data(data):
            pushed.extend(data)

        @staticmethod
        async def set_status_message(msg):
            statuses.append(msg)

    async def fake_fetch(max_pages=1, keyword="", max_items=None, log=None):
        captured_calls.append({"max_pages": max_pages, "keyword": keyword, "max_items": max_items})
        return [dict(actor_main.FALLBACK_VERIFIED_RECORDS[0], is_sample_fallback=True)]

    monkeypatch.setattr(actor_main, "HAS_APIFY", True)
    monkeypatch.setattr(actor_main, "Actor", DummyActor(), raising=False)
    monkeypatch.setattr(actor_main, "fetch_kpkt_teduh_pages", fake_fetch)

    asyncio.run(actor_main.main())

    assert captured_calls == [{"max_pages": 1, "keyword": "", "max_items": 25}]
    assert len(pushed) == 1
    assert any("SAMPLE rows" in s for s in statuses)

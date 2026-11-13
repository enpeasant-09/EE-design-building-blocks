from __future__ import annotations

import json
from pathlib import Path

import pytest

from partwatch import cli, extract, http
from partwatch.models import Lifecycle, normalize_lifecycle
from partwatch.normalize import base, group, same_manufacturer
from partwatch.providers import digikey, mouser, nexar
from partwatch.providers.mock import FileProvider
from partwatch.score import rate, rate_units


# ---------------------------------------------------------------- extraction
def test_extract_bricks(library):
    refs = extract.extract([library])
    units = {r.unit for r in refs}
    assert units == {"Power/BUCK_12V-5V_3A", "Power/LDO_ADJ", "Interface/USB_UART_CP2104"}
    buck = [r for r in refs if r.unit == "Power/BUCK_12V-5V_3A"]
    assert sorted(r.reference for r in buck) == ["C1", "D1", "L1", "R1", "U1"]   # no #PWR
    u1 = next(r for r in buck if r.reference == "U1")
    assert (u1.mpn, u1.manufacturer, u1.alternates) == ("TPS54331DR", "Texas Instruments",
                                                        ["TPS54332DDA"])
    cp = [r for r in refs if r.unit == "Interface/USB_UART_CP2104"]
    assert [r.reference for r in cp].count("U1") == 1                           # multi-unit once
    assert not any(r.reference == "R9" for r in cp)                              # DNP skipped
    ldo = [r for r in refs if r.unit == "Power/LDO_ADJ"]
    assert len(ldo) == 2                                                         # "U?" "C?" by uuid


def test_group_dedupes_across_bricks(library):
    groups, missing = group(extract.extract([library]))
    murata = next(g for g in groups if g.key == "GRM188R61A106KE69D")
    assert set(murata.used_in) == {"Power/LDO_ADJ", "Interface/USB_UART_CP2104"}
    assert {m.reference for m in missing} == {"C1", "R1", "D1"}


def test_real_carrier_project_parses():
    proj = Path("/mnt/user-data/outputs/UCM_iMX95_Carrier")
    if not proj.exists():
        pytest.skip("carrier project not present")
    refs = extract.extract([proj])
    assert len(refs) > 100 and all(r.reference for r in refs)


# --------------------------------------------------------------- normalizing
@pytest.mark.parametrize("raw,exp", [
    ("Active", Lifecycle.ACTIVE), ("Obsolete", Lifecycle.OBSOLETE),
    ("Not For New Designs", Lifecycle.NRND), ("Not Recommended for New Designs", Lifecycle.NRND),
    ("Last Time Buy", Lifecycle.LTB), ("End of Life", Lifecycle.LTB), ("EOL", Lifecycle.LTB),
    ("New Product", Lifecycle.ACTIVE), ("Preliminary", Lifecycle.PRELIMINARY),
    ("Discontinued at Digi-Key", Lifecycle.NRND), ("Production", Lifecycle.ACTIVE),
    ("", Lifecycle.UNKNOWN), (None, Lifecycle.UNKNOWN), ("Whatever", Lifecycle.UNKNOWN),
])
def test_lifecycle_vocab(raw, exp):
    assert normalize_lifecycle(raw) is exp


def test_mpn_base_and_mfr():
    assert base("LM1117IMPX-ADJ/NOPB") == "LM1117IMPX-ADJ"
    assert base("LT1763CS8#PBF") == "LT1763CS8"
    assert base(" tps54331dr ") == "TPS54331DR"
    assert same_manufacturer("Texas Instruments", "Texas Instruments Inc.")
    assert same_manufacturer("Murata", "Murata Electronics")
    assert not same_manufacturer("Murata", "Yageo")


# ----------------------------------------------------------------- providers
class FakeHTTP:
    def __init__(self, handler):
        self.handler, self.calls = handler, []

    def __call__(self, method, url, **kw):
        self.calls.append((method, url, kw))
        return self.handler(method, url, kw)


@pytest.fixture
def keys(monkeypatch):
    for k in ("DIGIKEY_CLIENT_ID", "DIGIKEY_CLIENT_SECRET", "MOUSER_API_KEY",
              "NEXAR_CLIENT_ID", "NEXAR_CLIENT_SECRET"):
        monkeypatch.setenv(k, "x")
    monkeypatch.setattr("partwatch.providers.base.request",
                        lambda *a, **k: {"access_token": "tok", "expires_in": 3600})


def test_digikey_details_then_keyword_fallback(keys, monkeypatch):
    def h(method, url, kw):
        if url.endswith("/productdetails"):
            if "BAD" in url:
                raise http.HttpError(404, "not found", url)
            return {"Product": {"ManufacturerProductNumber": "TPS54331DR",
                                "Manufacturer": {"Name": "Texas Instruments"},
                                "QuantityAvailable": 12000, "ManufacturerLeadWeeks": "6",
                                "ProductStatus": {"Id": 0, "Status": "Active"}}}
        return {"Products": [{"ManufacturerProductNumber": "BAD-PART",
                              "Manufacturer": {"Name": "Acme"}, "QuantityAvailable": 0,
                              "ProductStatus": {"Status": "Obsolete"}}]}
    fake = FakeHTTP(h)
    monkeypatch.setattr(digikey, "request", fake)
    p = digikey.DigiKeyProvider({})
    ok = p.lookup("TPS54331DR", "TI")
    assert ok.found and ok.lifecycle is Lifecycle.ACTIVE and ok.offers[0].stock == 12000
    assert ok.offers[0].lead_weeks == 6
    bad = p.lookup("BAD-PART", "")
    assert bad.found and bad.lifecycle is Lifecycle.OBSOLETE
    assert fake.calls[-1][0] == "POST" and fake.calls[-1][1].endswith("/search/keyword")
    hdrs = fake.calls[0][2]["headers"]
    assert hdrs["X-DIGIKEY-Client-Id"] == "x" and hdrs["Authorization"] == "Bearer tok"


def test_mouser_batch(keys, monkeypatch):
    def h(method, url, kw):
        assert kw["params"] == {"apiKey": "x"}
        assert kw["json_body"]["SearchByPartRequest"]["mouserPartNumber"] == "SRP7028A-100M|NOPE-1"
        return {"Errors": [], "SearchResults": {"Parts": [
            {"ManufacturerPartNumber": "SRP7028A-100M", "Manufacturer": "Bourns",
             "AvailabilityInStock": "3,456", "LeadTime": "84 Days", "LifecycleStatus": None},
        ]}}
    monkeypatch.setattr(mouser, "request", FakeHTTP(h))
    out = mouser.MouserProvider({}).lookup_many([("SRP7028A-100M", "Bourns"), ("NOPE-1", "")])
    a = out["SRP7028A-100M"]
    assert a.found and a.lifecycle is Lifecycle.ACTIVE and a.offers[0].stock == 3456
    assert a.offers[0].lead_weeks == 12
    assert not out["NOPE-1"].found


def test_nexar_multimatch(keys, monkeypatch):
    def h(method, url, kw):
        qs = kw["json_body"]["variables"]["queries"]
        assert [q["mpn"] for q in qs] == ["CP2104-F03-GMR", "TPS54331DR"]
        return {"data": {"supMultiMatch": [
            {"reference": "1", "hits": 1, "parts": [{
                "mpn": "TPS54331DR", "manufacturer": {"name": "Texas Instruments"},
                "specs": [{"attribute": {"shortname": "lifecyclestatus"},
                           "displayValue": "Production (Last Updated: 1 month ago)"}],
                "sellers": [
                    {"company": {"name": "Digi-Key"}, "isAuthorized": True,
                     "offers": [{"inventoryLevel": 9000, "factoryLeadDays": 42}]},
                    {"company": {"name": "Mouser"}, "isAuthorized": True,
                     "offers": [{"inventoryLevel": 4000}]},
                    {"company": {"name": "SomeBroker"}, "isAuthorized": False,
                     "offers": [{"inventoryLevel": 99999}]}]}]},
            {"reference": "0", "hits": 1, "parts": [{
                "mpn": "CP2104-F03-GMR", "manufacturer": {"name": "Silicon Labs"},
                "specs": [{"attribute": {"shortname": "lifecyclestatus"},
                           "displayValue": "Obsolete"}],
                "sellers": []}]},
        ]}}
    monkeypatch.setattr(nexar, "request", FakeHTTP(h))
    out = nexar.NexarProvider({}).lookup_many([("CP2104-F03-GMR", "Silicon Labs"),
                                              ("TPS54331DR", "Texas Instruments")])
    t = out["TPS54331DR"]
    assert t.lifecycle is Lifecycle.ACTIVE
    assert {o.distributor: o.stock for o in t.offers} == {"Digi-Key": 9000, "Mouser": 4000}
    assert out["CP2104-F03-GMR"].lifecycle is Lifecycle.OBSOLETE


def test_provider_error_becomes_gray(keys, monkeypatch):
    def boom(*a, **k):
        raise http.HttpError(401, "bad key", "u")
    monkeypatch.setattr(mouser, "request", boom)
    res = mouser.MouserProvider({}).lookup_many([("X1", "")])
    groups, _ = group([extract.PartRef("B", "f", "U1", "x", "", "", "X1", "")])
    st = rate(groups[0], [res["X1"]], {})
    assert st.rating == "gray" and "lookup failed" in st.reasons[0]


# ------------------------------------------------------------------- scoring
def _offers(**stock):
    return [{"distributor": d, "stock": s} for d, s in stock.items()]


@pytest.fixture
def overrides(tmp_path):
    db = {
        "TPS54331DR": {"lifecycle": "Not Recommended for New Designs",
                       "offers": _offers(DigiKey=20000, Mouser=8000)},
        "TPS54332DDA": {"lifecycle": "Active", "offers": _offers(DigiKey=5000, Mouser=7000)},
        "SRP7028A-100M": {"lifecycle": "Active", "offers": _offers(Mouser=900)},
        "LM1117IMPX-ADJ": {"lifecycle": "Active", "offers": _offers(DigiKey=50000, Mouser=30000)},
        "GRM188R61A106KE69D": {"lifecycle": "Active", "offers": _offers(DigiKey=10**6, LCSC=10**6)},
        "CP2104-F03-GMR": {"lifecycle": "Obsolete", "offers": _offers(DigiKey=0)},
    }
    p = tmp_path / "over.json"
    p.write_text(json.dumps(db))
    return p


def test_rules(library, overrides):
    groups, missing = group(extract.extract([library]))
    prov = FileProvider({"path": str(overrides)})
    st = {g.key: rate(g, [prov.lookup(g.mpn, g.manufacturer)], {}) for g in groups}
    assert st["CP2104-F03-GMR"].rating == "red"            # obsolete + no stock
    assert st["TPS54331DR"].rating == "amber"              # NRND
    assert st["SRP7028A-100M"].rating == "amber"           # single source + low stock
    assert any("single source" in r for r in st["SRP7028A-100M"].reasons)
    assert st["LM1117IMPX-ADJ/NOPB"].rating == "green"     # matched via base MPN
    assert st["GRM188R61A106KE69D"].rating == "green"
    units = rate_units(list(st.values()), missing, {})
    assert units["Interface/USB_UART_CP2104"]["rating"] == "red"
    assert units["Power/BUCK_12V-5V_3A"]["rating"] == "amber"   # NRND + D1 without MPN
    assert units["Power/LDO_ADJ"]["rating"] == "green"


def test_not_found_is_red(library, tmp_path):
    (tmp_path / "empty.json").write_text("{}")
    groups, _ = group(extract.extract([library]))
    prov = FileProvider({"path": str(tmp_path / "empty.json")})
    st = rate(groups[0], [prov.lookup(groups[0].mpn, "")], {})
    assert st.rating == "red" and "not found" in st.reasons[0]


# ---------------------------------------------------------------- end to end
def test_cli_end_to_end(library, overrides, tmp_path, monkeypatch, capsys):
    cfg = tmp_path / "partwatch.toml"
    cfg.write_text(f"""
[paths]
include = ["blocks"]
[providers.overrides]
type = "file"
path = "{overrides.as_posix()}"
[cache]
path = ".pw/cache.sqlite"
[report]
dir = "reports"
""")
    assert cli.main(["scan", "-c", str(cfg)]) == 0
    assert "TPS54331DR" in capsys.readouterr().out

    rc = cli.main(["check", "-c", str(cfg), "--fail-on", "red"])
    assert rc == 1                                             # CP2104 brick is red
    md = (tmp_path / "reports" / "STATUS.md").read_text(encoding="utf-8")
    assert "Interface/USB_UART_CP2104" in md and "🔴" in md
    assert "drop-in alternate available: TPS54332DDA" in md
    assert "D1" in md                                          # missing-MPN section
    js = json.loads((tmp_path / "reports" / "status.json").read_text())
    assert {p["mpn"] for p in js["parts"]} >= {"TPS54331DR", "CP2104-F03-GMR"}
    assert (tmp_path / "reports" / "parts.csv").exists()

    # Second run: everything served from cache, no provider calls.
    calls = []
    orig = FileProvider.lookup
    monkeypatch.setattr(FileProvider, "lookup", lambda s, m, f: calls.append(m) or orig(s, m, f))
    assert cli.main(["check", "-c", str(cfg)]) == 0            # no --fail-on
    assert calls == []


@pytest.mark.parametrize("raw,mfr,exp", [
    ("TDK TCE1210U-900-4P (90 Ohm, ESD)", "", ("TCE1210U-900-4P", "TDK", "")),
    ("TE 2227302-1 class SFP+ cage + 20p connector", "", ("2227302-1", "TE", "")),
    ("Texas Instruments TPS54331DR", "", ("TPS54331DR", "Texas Instruments", "")),
    ("Amphenol 12401610E4#2A", "", ("12401610E4#2A", "Amphenol", "")),
    ("TPS54331DR", "TI", ("TPS54331DR", "TI", "")),
    ("GRM155R71A104KA01D", "", ("GRM155R71A104KA01D", "", "")),
])
def test_tidy_field(raw, mfr, exp):
    from partwatch.normalize import tidy_field
    assert tidy_field(raw, mfr) == exp


def test_tidy_field_placeholder():
    from partwatch.normalize import tidy_field
    mpn, mfr, problem = tidy_field("SiTime SiT9102AI-xx-33E156.250000 (HCSL)", "")
    assert mpn == "" and mfr == "SiTime" and problem.startswith("incomplete MPN")


def test_auth_failure_stops_provider(keys, monkeypatch):
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise http.HttpError(401, "invalid client", "u")
    monkeypatch.setattr(digikey, "request", boom)
    out = digikey.DigiKeyProvider({}).lookup_many([("A1", ""), ("B2", ""), ("C3", "")])
    assert len(calls) == 1
    assert all(not r.found and r.error for r in out.values())

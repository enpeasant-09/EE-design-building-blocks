"""Builds a small design-block library on disk for the tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _sym(lib_id, ref, value, fields=None, dnp=False, unit=1, uuid="u"):
    props = {"Reference": ref, "Value": value, "Footprint": "", **(fields or {})}
    p = "".join(f'\n    (property "{k}" "{v}" (at 0 0 0))' for k, v in props.items())
    return (f'  (symbol (lib_id "{lib_id}") (at 0 0 0) (unit {unit}) (in_bom yes) (on_board yes)'
            f' (dnp {"yes" if dnp else "no"}) (uuid "{uuid}"){p}\n  )\n')


def write_sch(path: Path, symbols: list[str], libdefs: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('(kicad_sch (version 20250114) (generator "eeschema")\n'
                    f'  (lib_symbols{libdefs})\n' + "".join(symbols) + ")\n", encoding="utf-8")


@pytest.fixture
def library(tmp_path: Path) -> Path:
    blocks = tmp_path / "blocks"
    pwr = blocks / "Power.kicad_blocks"
    write_sch(pwr / "BUCK_12V-5V_3A.kicad_block" / "BUCK_12V-5V_3A.kicad_sch", [
        _sym("Regulator_Switching:TPS54331D", "U1", "TPS54331",
             {"MPN": "TPS54331DR", "Manufacturer": "Texas Instruments", "MPN_ALT": "TPS54332DDA"}),
        _sym("Device:L", "L1", "10uH", {"MPN": "SRP7028A-100M", "Manufacturer": "Bourns"}),
        _sym("Device:C", "C1", "22uF"),                       # generic, no MPN: fine
        _sym("Device:R", "R1", "10k"),
        _sym("Diode:B340", "D1", "B340"),                     # non-generic, no MPN: flagged
        _sym("power:GND", "#PWR01", "GND"),                   # power symbol: skipped
    ], libdefs='\n    (symbol "power:GND" (power) (property "Reference" "#PWR" (at 0 0 0)))')
    write_sch(pwr / "LDO_ADJ.kicad_block" / "LDO_ADJ.kicad_sch", [
        _sym("Regulator_Linear:LM317", "U?", "LM1117", {"MPN": "LM1117IMPX-ADJ/NOPB",
                                                        "Manufacturer": "TI"}, uuid="a1"),
        _sym("Device:C", "C?", "10uF", {"MPN": "GRM188R61A106KE69D", "Manufacturer": "Murata"},
             uuid="a2"),
    ])
    iface = blocks / "Interface.kicad_blocks"
    write_sch(iface / "USB_UART_CP2104.kicad_block" / "USB_UART_CP2104.kicad_sch", [
        _sym("Interface_USB:CP2104", "U1", "CP2104", {"MPN": "CP2104-F03-GMR",
                                                      "Manufacturer": "Silicon Labs"}),
        _sym("Interface_USB:CP2104", "U1", "CP2104", {"MPN": "CP2104-F03-GMR"}, unit=2),  # 2nd unit
        _sym("Device:C", "C1", "100nF", {"MPN": "GRM188R61A106KE69D", "Manufacturer": "Murata"}),
        _sym("Device:R", "R9", "DNP", {"MPN": "RC0402FR-0710KL"}, dnp=True),           # DNP skipped
    ])
    return blocks

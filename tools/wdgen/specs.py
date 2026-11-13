"""One entry per supervisor IC. Pin roles drive the sheet generator.

roles:
  VDD   top pin -> +3V3            GND   bottom pin -> GND
  P3V3  side pin tied to +3V3      PGND  side pin tied to GND
  NC    no-connect                 WDI   hierarchical input WDI
  MR    manual-reset net (button + ESD)
  RST   supervisor reset/watchdog output -> ~{RST_SUP} -> OR gate
  CAP:<value>  timing capacitor to GND
"""

TI = "Texas Instruments"
ST = "STMicroelectronics"
MC = "Microchip"
ADI = "Analog Devices"

# (num, name, electrical type, side, role)
def sot23_mr(reset_type):
    return [("4", "WDI", "input", "L", "WDI"), ("3", "~{MR}", "input", "L", "MR"),
            ("1", "~{RESET}", reset_type, "R", "RST"),
            ("5", "VDD", "power_in", "T", "VDD"), ("2", "GND", "power_in", "B", "GND")]


def sot23_dual(nreset_type):
    return [("4", "WDI", "input", "L", "WDI"),
            ("1", "~{RESET}", nreset_type, "R", "RST"), ("3", "RESET", "output", "R", "NC"),
            ("5", "VDD", "power_in", "T", "VDD"), ("2", "GND", "power_in", "B", "GND")]


SOT235 = "Package_TO_SOT_SMD:SOT-23-5"

ICS = [
    dict(key="TPS3823", value="TPS3823-33DBVR", mpn="TPS3823-33DBVR", mfr=TI, alt="STM6823TWY6F, MCP1316T-29LE/OT",
         lib="Power_Supervisor:TPS3823-xxDBV", fp=SOT235, od=False, has_mr=True,
         ds="https://www.ti.com/lit/ds/symlink/tps3823.pdf",
         desc="TPS3823 supervisor, 2.93 V threshold, 1.6 s watchdog, push-pull ~{RESET}, manual reset",
         note="Group 1 SOT-23-5 (MAX823 pinout). Drop-in: STM6823, MCP1316."),
    dict(key="TPS3828", value="TPS3828-33DBVR", mpn="TPS3828-33DBVR", mfr=TI, alt="STM6822TWY6F, MCP1320T-29LE/OT",
         pins=sot23_mr("open_collector"), fp=SOT235, od=True, has_mr=True,
         ds="https://www.ti.com/lit/ds/symlink/tps3828.pdf",
         desc="TPS3828 supervisor, 2.93 V threshold, 1.6 s watchdog, open-drain ~{RESET}, manual reset",
         note="Group 1 SOT-23-5, open-drain output: R pull-up fitted."),
    dict(key="TPS3824", value="TPS3824-33DBVR", mpn="TPS3824-33DBVR", mfr=TI, alt="STM6824TWY6F, MCP1318T-29LE/OT",
         pins=sot23_dual("output"), fp=SOT235, od=False, has_mr=False,
         ds="https://www.ti.com/lit/ds/symlink/tps3824.pdf",
         desc="TPS3824 supervisor, 2.93 V threshold, 1.6 s watchdog, push-pull ~{RESET} + RESET, no MR",
         note="Group 2 SOT-23-5 (MAX824 pinout): no MR pin, button resets nRST directly."),
    dict(key="STM6822", value="STM6822TWY6F", mpn="STM6822TWY6F", mfr=ST, alt="TPS3828-33DBVR",
         pins=sot23_mr("open_collector"), fp=SOT235, od=True, has_mr=True,
         ds="https://www.st.com/resource/en/datasheet/stm6822.pdf",
         desc="STM6822 supervisor, 3.08 V threshold, 1.6 s watchdog, open-drain ~{RST}, manual reset",
         note="Group 1 SOT-23-5, open-drain output: R pull-up fitted."),
    dict(key="STM6823", value="STM6823TWY6F", mpn="STM6823TWY6F", mfr=ST, alt="TPS3823-33DBVR, MCP1316T-29LE/OT",
         pins=sot23_mr("output"), fp=SOT235, od=False, has_mr=True,
         ds="https://www.st.com/resource/en/datasheet/stm6823.pdf",
         desc="STM6823 supervisor, 3.08 V threshold, 1.6 s watchdog, push-pull ~{RST}, manual reset",
         note="Group 1 SOT-23-5 (MAX823 pinout). Drop-in: TPS3823, MCP1316."),
    dict(key="STM6824", value="STM6824TWY6F", mpn="STM6824TWY6F", mfr=ST, alt="TPS3824-33DBVR, MCP1318T-29LE/OT",
         pins=sot23_dual("output"), fp=SOT235, od=False, has_mr=False,
         ds="https://www.st.com/resource/en/datasheet/stm6824.pdf",
         desc="STM6824 supervisor, 3.08 V threshold, 1.6 s watchdog, push-pull ~{RST} + RST, no MR",
         note="Group 2 SOT-23-5 (MAX824 pinout): no MR pin, button resets nRST directly."),
    dict(key="MCP1316", value="MCP1316T-29LE/OT", mpn="MCP1316T-29LE/OT", mfr=MC, alt="TPS3823-33DBVR, STM6823TWY6F",
         pins=sot23_mr("output"), fp=SOT235, od=False, has_mr=True,
         ds="https://ww1.microchip.com/downloads/en/DeviceDoc/21985D.pdf",
         desc="MCP1316 supervisor, 2.9 V threshold, watchdog, push-pull ~{RST}, manual reset",
         note="Group 1 SOT-23-5. Check reset-delay / WDT codes in the order number."),
    dict(key="MCP1316M", value="MCP1316MT-29LE/OT", mpn="MCP1316MT-29LE/OT", mfr=MC, alt="",
         pins=sot23_mr("output"), fp=SOT235, od=False, has_mr=True,
         ds="https://ww1.microchip.com/downloads/en/DeviceDoc/21985D.pdf",
         desc="MCP1316M supervisor, 2.9 V threshold, watchdog, open-drain ~{RST} with internal pull-up, manual reset",
         note="Group 1 SOT-23-5. Internal pull-up on ~{RST}: no external resistor."),
    dict(key="MCP1318", value="MCP1318T-29LE/OT", mpn="MCP1318T-29LE/OT", mfr=MC, alt="TPS3824-33DBVR, STM6824TWY6F",
         pins=sot23_dual("output"), fp=SOT235, od=False, has_mr=False,
         ds="https://ww1.microchip.com/downloads/en/DeviceDoc/21985D.pdf",
         desc="MCP1318 supervisor, 2.9 V threshold, watchdog, push-pull ~{RST} + RST, no MR",
         note="Group 2 SOT-23-5: no MR pin, button resets nRST directly."),
    dict(key="MCP1320", value="MCP1320T-29LE/OT", mpn="MCP1320T-29LE/OT", mfr=MC, alt="TPS3828-33DBVR",
         pins=sot23_mr("open_collector"), fp=SOT235, od=True, has_mr=True,
         ds="https://ww1.microchip.com/downloads/en/DeviceDoc/21985D.pdf",
         desc="MCP1320 supervisor, 2.9 V threshold, watchdog, open-drain ~{RST} (external pull-up), manual reset",
         note="Group 1 SOT-23-5, open-drain output: R pull-up fitted."),
    dict(key="MCP1321", value="MCP1321T-29LE/OT", mpn="MCP1321T-29LE/OT", mfr=MC, alt="",
         pins=sot23_dual("open_collector"), fp=SOT235, od=True, has_mr=False,
         ds="https://ww1.microchip.com/downloads/en/DeviceDoc/21985D.pdf",
         desc="MCP1321 supervisor, 2.9 V threshold, watchdog, open-drain ~{RST} + push-pull RST, no MR",
         note="Group 2 SOT-23-5, open-drain ~{RST}: R pull-up fitted; button resets nRST directly."),
    dict(key="TPS35", value="TPS35CA40KAGDDFR", mpn="TPS35CA40KAGDDFR", mfr=TI, alt="",
         pins=[("1", "SET0", "input", "L", "PGND"), ("2", "~{MR}", "input", "L", "MR"),
               ("3", "WDI", "input", "L", "WDI"), ("5", "SET1", "input", "L", "PGND"),
               ("6", "WD-EN", "input", "L", "P3V3"), ("7", "~{RESET}", "open_collector", "R", "RST"),
               ("8", "VDD", "power_in", "T", "VDD"), ("4", "GND", "power_in", "B", "GND")],
         fp="Package_TO_SOT_SMD:Texas_DDF0008A_SOT-8_1.6x2.9mm_P0.65mm", od=True, has_mr=True,
         ds="https://www.ti.com/lit/ds/symlink/tps35.pdf",
         desc="TPS35 pinout C, 3.00 V threshold, 1.6 s watchdog, 200 ms reset, open-drain ~{RESET}, 250 nA",
         note="Pinout option C (fixed timing). Order code built from the datasheet decoder: confirm it is released."),
    dict(key="TPS3851", value="TPS3851G33SDRBR", mpn="TPS3851G33SDRBR", mfr=TI, alt="",
         pins=[("2", "CWD", "input", "L", "NC"), ("3", "~{MR}", "input", "L", "MR"),
               ("6", "WDI", "input", "L", "WDI"), ("5", "SET1", "input", "L", "PGND"),
               ("8", "~{RESET}", "open_collector", "R", "RST"), ("7", "~{WDO}", "open_collector", "R", "RST"),
               ("1", "VDD", "power_in", "T", "VDD"), ("4", "GND", "power_in", "B", "GND"),
               ("9", "EP", "passive", "B", "GND")],
         fp="Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm", od=True, has_mr=True,
         ds="https://www.ti.com/lit/ds/symlink/tps3851.pdf",
         desc="TPS3851 precision supervisor (0.8%), 3.3 V -4% threshold, watchdog, open-drain ~{RESET} + ~{WDO}",
         note="~{RESET} and ~{WDO} wired-OR. CWD open = factory timing; check SET1 setting in datasheet."),
    dict(key="TPS3850", value="TPS3850G33DRCR", mpn="TPS3850G33DRCR", mfr=TI, alt="",
         pins=[("10", "SENSE", "input", "L", "P3V3"), ("2", "CWD", "input", "L", "NC"),
               ("4", "CRST", "input", "L", "NC"), ("3", "SET0", "input", "L", "P3V3"),
               ("6", "SET1", "input", "L", "P3V3"), ("7", "WDI", "input", "L", "WDI"),
               ("9", "~{RESET}", "open_collector", "R", "RST"), ("8", "~{WDO}", "open_collector", "R", "RST"),
               ("1", "VDD", "power_in", "T", "VDD"), ("5", "GND", "power_in", "B", "GND"),
               ("11", "EP", "passive", "B", "GND")],
         fp="Package_SON:VSON-10-1EP_3x3mm_P0.5mm_EP1.65x2.4mm", od=True, has_mr=False,
         ds="https://www.ti.com/lit/ds/symlink/tps3850.pdf",
         desc="TPS3850 window-watchdog supervisor, 3.3 V -4%, SET0=SET1=1: 800-1600 ms window, open-drain outputs",
         note="WINDOW watchdog: WDI edges must arrive between 800 ms and 1600 ms. No MR: button resets nRST."),
    dict(key="MAX16056", value="MAX16056ATA31+T", mpn="MAX16056ATA31+T", mfr=ADI, alt="",
         pins=[("4", "~{MR}", "input", "L", "MR"), ("6", "WDI", "input", "L", "WDI"),
               ("7", "WDS", "input", "L", "PGND"),
               ("1", "~{RESET}", "output", "R", "RST"), ("5", "SRT", "passive", "R", "CAP:39n"),
               ("3", "SWT", "passive", "R", "CAP:330n"),
               ("8", "VCC", "power_in", "T", "VDD"), ("2", "GND", "power_in", "B", "GND"),
               ("9", "EP", "passive", "B", "GND")],
         fp="Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm", od=False, has_mr=True, mr_pullup=True,
         ds="https://www.analog.com/media/en/technical-documentation/data-sheets/max16056-max16059.pdf",
         desc="MAX16056 125 nA supervisor, 3.075 V threshold, 39 nF = 200 ms reset, 330 nF = 1.7 s watchdog",
         note="MR has no internal pull-up: R fitted. Footprint: check against Maxim land pattern 90-0059."),
    dict(key="ADM8613", value="ADM8613Y232ACBZ-R7", mpn="ADM8613Y232ACBZ-R7", mfr=ADI, alt="",
         pins=[("B1", "WDI", "input", "L", "WDI"), ("C1", "~{MR}", "input", "L", "MR"),
               ("B2", "WD_DIS", "input", "L", "PGND"), ("C2", "~{RESET}", "open_collector", "R", "RST"),
               ("A1", "VCC", "power_in", "T", "VDD"), ("A2", "GND", "power_in", "B", "GND")],
         fp="Chinmay_Supervisor:ADI_WLCSP-6_0.96x1.46mm_P0.5mm", od=True, has_mr=True,
         ds="https://www.analog.com/media/en/technical-documentation/data-sheets/adm8611_8612_8613_8614_8615.pdf",
         desc="ADM8613 92 nA supervisor, WLCSP-6, 1.6 s watchdog, open-drain ~{RESET}",
         note="Standard part has a 2.32 V threshold; 2.93/3.08 V are non-standard orders."),
    dict(key="MAX6369", value="MAX6369KA+T", mpn="MAX6369KA+T", mfr=ADI, alt="",
         pins=[("1", "WDI", "input", "L", "WDI"), ("4", "SET0", "input", "L", "P3V3"),
               ("5", "SET1", "input", "L", "PGND"), ("6", "SET2", "input", "L", "P3V3"),
               ("3", "NC", "no_connect", "L", "NC"), ("7", "~{WDO}", "open_collector", "R", "RST"),
               ("8", "VCC", "power_in", "T", "VDD"), ("2", "GND", "power_in", "B", "GND")],
         fp="Package_TO_SOT_SMD:SOT-23-8", od=True, has_mr=False,
         ds="https://www.analog.com/media/en/technical-documentation/data-sheets/MAX6369-MAX6374.pdf",
         desc="MAX6369 pin-selectable watchdog (SET2..0 = 101: 1-3 s), open-drain ~{WDO}, NO voltage monitor",
         note="Watchdog only: pair with a voltage supervisor. No MR: button resets nRST."),
]

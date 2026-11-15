import json
S=json.load(open('/home/claude/fpreview/fpsumm.json'))
K='KiCad 10 library model ✓'
CH='Chinmay_3D (Fusion) – pending'
def L(fp): return S.get(fp,'')
rows=[]
def r(status,lib,part,qty,fp,ds_pkg,ds_geo,model,find,src):
    rows.append([status,lib,part,qty,fp,ds_pkg,ds_geo,L(fp),model,find,src])
CF='Chinmay_Footprints:'
# BUCK
r('Added','BUCK','LT8640SEV#PBF (U701)',1,CF+'ADI_LQFN-24_4x4mm_P0.5mm_4xEP1.125mm_LT8640S','LQFN-24 4×4×0.94 (LTC 05-08-1511 Rev C)','e 0.50, b 0.25, L 0.40; 4× EP 1.125 sq, 0.20 gaps; land 0.25×0.70 on 4.50 outline',CH,'Symbol had NO footprint. Built from datasheet "Suggested PCB layout" incl. 4 EP segments (pins 25–28) and corner support pads.','LT8640S datasheet Rev D p30')
r('Added','BUCK','LT8645SEV#PBF (U801)',1,CF+'ADI_LQFN-32_4x6mm_P0.5mm_6xEP_LT8645S','LQFN-32 6×4×0.94 (LTC 05-08-1512 Rev C)','e 0.50; 10+6 pins/side; 6 EP segs (1.355/1.34 × 1.125); land 0.25×0.70 on 6.50×4.50',CH,'Symbol had NO footprint. Built from datasheet suggested layout; EPs = pins 33–38.','LT8645S datasheet Rev E p28')
r('Added','BUCK','LT8648SEV#PBF (U901)',1,CF+'ADI_LQFN-36_4x7mm_P0.5mm_6xEP_LT8648S','LQFN-36 7×4×0.94 (LTC 05-08-1604 Rev A)','e 0.50; 12+6 pins/side; 6 EP 1.73×1.20; land 0.25×0.70 on 7.50×4.50',CH,'Symbol had NO footprint. Built from datasheet suggested layout; EPs = pins 37–42.','LT8648S datasheet Rev E p26')
r('Added','BUCK','MP8795HGLE-Z (U1001)',1,CF+'MPS_QFN-21_3x4mm_P0.4mm','QFN-21 3×4×0.90 (MO-220)','e 0.40; pins 1/9/19 0.30 wide; VIN/SW bars 0.30×2.0; PGND comb 11–18',CH,'Symbol had NO footprint. Built from MPS "Recommended land pattern" (VIN 10/21, SW 20 bars, PGND comb backbone 0.35).','MP8795H datasheet Rev1.0 p17')
r('Fixed','BUCK','MAX17503ATP+ (U301)',1,CF+'Maxim_T2044-4C_TQFN-20-1EP_4x4mm_P0.5mm_EP2.85x2.85mm_ThermalVias','20-TQFN-EP 4×4×0.75, code T2044+4C (21-100172)','e 0.50; land 90-0409: 0.30×0.60 pads on 3.85 rows, EP land 2.85',CH,'WRONG PACKAGE: was TQFN-20 5×5 P0.65 (EP3.1). MAX17503 is the 4×4 P0.5 TQFN. Replaced with land 90-0409.','MAX17503 datasheet p2/p26; ADI land pattern 90-0409')
r('OK','BUCK','MAX17506ATP+ (U501)',1,CF+'TQFN-20-1EP_5x5mm_P0.65mm_EP3.25x3.25mm_ThermalVias','20-TQFN 5×5×0.75, code T2055+4 (21-0140)','e 0.65; EP 3.25 nom',CH,'Land matches T2055-4. KiCad 3D file missing from install → copied into Chinmay_Footprints with new model.','MAX17506 datasheet p2')
r('OK','BUCK','MAX17761ATC+ (U201)',1,CF+'Maxim_TDFN-12-1EP_3x3mm_P0.5mm_EP1.7x2.5mm','12-TDFN-EP 3×3×0.75, code TD1233+1C (21-0664, land 90-0397)','e 0.50; EP 1.7×2.5',CH,'Land OK. KiCad references DFN-12 EP2.05×2.86 STEP which is not installed → re-pointed to Chinmay model.','MAX17761 datasheet p2')
r('OK','BUCK','RAA211450GSP#HA0 / RAA211630GSP#HA0 (U601, U401)',2,CF+'HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm','16-HTSSOP-EP 4.4×5.0×1.0, span 6.4 (GSP)','e 0.65; EP 3×3',"Chinmay_3D (Fusion) ✓",'Land OK. KiCad model for EP3×3 variant not installed → new STEP exported from Fusion.','Renesas RAA2114x0 datasheets')
r('OK','BUCK','SIS468DN-T1-GE3 (Q501)',1,CF+'Vishay_PowerPAK_1212-8_Single','PowerPAK 1212-8S 3.3×3.3×0.97 (1.07 max)','4 S/G pins e 0.65 + drain pad',CH,'Land OK. KiCad STEP not installed → Chinmay model.','Vishay SiS468DN datasheet')
for m,fp,ds in [('XEL6030-222MEC (L701)','Inductor_SMD:L_Coilcraft_XAL6030-XXX','XEL6030 6.56×6.36×3.1'),('XAL7070-332MEC (L801, L501, L601)','Inductor_SMD:L_Coilcraft_XAL7070-XXX','XAL7070 7.5×7.2×7.0'),('XAL8080-222MEC (L901)','Inductor_SMD:L_Coilcraft_XAL8080-XXX','XAL8080 8.8×8.0×8.0'),('XAL6060-682MEC (L301, L401)','Inductor_SMD:L_Coilcraft_XAL6060-XXX','XAL6060 6.56×6.36×6.1'),('XAL5050-223MEC (L201)','Inductor_SMD:L_Coilcraft_XAL5050-XXX','XAL5050 5.48×5.28×5.1'),('XAL1010-681MEC (L1001)','Inductor_SMD:L_Coilcraft_XAL1010-XXX','XAL1010 11.3×10.0×10.0')]:
    r('OK','BUCK',m,1,fp,ds,'2-terminal, Coilcraft land pattern',K,'Coilcraft recommended land used by KiCad generator.','Coilcraft XAL/XEL datasheets')
r('OK','BUCK','Polymer/tantalum C (EIA 3528-21, 6032-28, 7343-31)',5,'Capacitor_Tantalum_SMD:CP_EIA-6032-28_Kemet-C','EIA case B/C/D','IPC-7351 nominal',K,'Footprints match EIA cases used (B: 1, C: 3, D: 1).','KEMET case codes')
# LDO
r('OK','LDO','AZ1117C / LT3080 / NCP1117 / TLV1117 (SOT-223)',4,'Package_TO_SOT_SMD:SOT-223-3_TabPin2','SOT-223 6.5×3.5×1.6, tab = pin 2 (VOUT)','e 2.30; tab 3.0 wide',K,'Tab = pin 2 matches all four (adjustable, tab = OUT).','Vendor datasheets')
r('OK','LDO','LM1084/85/86 ISX-ADJ (DDPAK/TO-263-3)',3,'Package_TO_SOT_SMD:TO-263-3_TabPin2','TO-263-3 (KTT) 10.2×9.0, tab = pin 2','e 2.54',K,'Tab = VOUT = pin 2 OK.','TI LM1084/5/6 datasheets')
r('OK','LDO','S1B (D201)',1,'Diode_SMD:D_SMA','SMA / DO-214AC 4.3×2.6','',K,'OK.','DO-214AC')
# XTAL
r('OK','XTAL','ECS-2520MV-xxx-BN-TR XO (12–125 MHz, 9 blocks)',9,CF+'Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm','2.5×2.0×0.8 nom ceramic, 4 pads','pads per ECS land 0.8×0.9 (KiCad = ECS recommended)',CH,'Land matches ECS. KiCad has no STEP for this footprint → Chinmay model. Blocks + A3 sheets re-pointed.','ECS-2520MV datasheet')
r('OK','XTAL','ECX-2236 / 2236B / 2236B2 crystals (12–48 MHz, 13 blocks + CH340G)',14,'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm','2.5×2.0×0.55, 4 pads (1/3 = crystal, 2/4 = GND)','',K,'OK.','ECS ECX-2236 datasheets')
r('OK','XTAL','ECX-33Q 8 MHz',1,'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm','3.2×2.5×0.8, 4 pads','',K,'OK.','ECS ECX-33Q')
r('OK','XTAL','ECX-31B 32.768 kHz',1,'Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm','3.2×1.5×0.9, 2 pads','',K,'OK.','ECS ECX-31B')
# WD
r('OK','WD_RST','ADM8613Y232ACBZ-R7 (U1701)',1,CF+'ADI_WLCSP-6_0.96x1.46mm_P0.5mm','WLCSP-6 (CB-6-17) 0.96×1.46×0.56 max, 0.5 pitch','ball 0.25',CH,'Custom footprint had NO 3D model → moved to Chinmay_Footprints + model.','ADM8611–8615 datasheet p17')
r('OK','WD_RST','MAX16056ATA31+T (U1601)',1,'Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.5x2.25mm','8-TDFN-EP 3×3×0.75, T833-2 (21-0137, land 90-0059)','e 0.65; EP 1.50×2.30',K,'Footprint EP 2.25 vs 2.30 package nominal – within tolerance, OK.','MAX16056 datasheet p16')
r('OK','WD_RST','MAX6369KA+T (U1801)',1,'Package_TO_SOT_SMD:SOT-23-8','SOT-23-8 2.9×1.6, e 0.65','',K,'OK.','MAX6369 datasheet')
r('OK','WD_RST','TPS35CA40KAGDDFR (U1301)',1,CF+'Texas_DDF0008A_SOT-8_1.6x2.9mm_P0.65mm','DDF0008A SOT-23-THIN 2.9×1.6×0.85, span 2.8','e 0.65',CH,'Land OK. KiCad STEP not installed → Chinmay model.','TI TPS35 datasheet')
r('OK','WD_RST','TPS3851G33SDRBR (U1401)',1,CF+'VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm','DRB0008A VSON-8 3×3×0.9, EP 1.65×2.4','e 0.65',CH,'Land OK. KiCad STEP not installed → Chinmay model.','TI TPS3851 datasheet')
r('OK','WD_RST','TPS3850G33DRCR (U1501)',1,'Package_SON:VSON-10-1EP_3x3mm_P0.5mm_EP1.65x2.4mm','DRC0010J VSON-10 3×3×1.0, EP 1.65×2.4','e 0.50',K,'OK.','TI TPS3850 datasheet')
r('OK','WD_RST','TPS382x / MCP131x / STM682x supervisors (SOT-23-5)',11,'Package_TO_SOT_SMD:SOT-23-5','SOT-23-5 (DBV / OT / WY) 2.9×1.6, e 0.95','',K,'OK.','Vendor datasheets')
r('OK','WD_RST','SN74LVC1G32DBVR / SN74LVC1G07DBVR',34,'Package_TO_SOT_SMD:SOT-23-5','DBV SOT-23-5','',K,'OK.','TI datasheets')
r('OK','WD_RST','ESD9B3.3ST5G',17,'Diode_SMD:D_SOD-923','SOD-923 0.8×0.6×0.4','',K,'OK.','onsemi ESD9B')
r('OK','WD_RST','PTS810SJK250SMTR LFS',17,'Button_Switch_SMD:SW_SPST_PTS810','PTS810 4.2×3.2×2.5','',K,'OK.','C&K PTS810')
r('Note','WD_RST','Solder jumper SJ_Open',17,'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm','PCB copper only','',"Not needed (no part)",'Copper-only footprint – no 3D body by design.','')
# USB
r('OK','USB2UART','CH340C / CH340G',2,'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm','SOIC-16 150 mil','e 1.27',K,'OK.','WCH datasheets')
r('OK','USB2UART','CH343P (U801)',1,CF+'WCH_QFN-16-1EP_3x3mm_P0.5mm_EP1.8x1.8mm','QFN-16 3×3×0.75, EP 1.8','e 0.50',CH,'Land OK. KiCad STEP not installed → Chinmay model.','WCH CH343 datasheet')
r('OK','USB2UART','CP2102N-A02-GQFN28R',1,'Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm','QFN-28 5×5×0.85, EP 3.35','e 0.50',K,'OK.','Silabs CP2102N')
r('OK','USB2UART','CP2108-B03-GMR',1,'Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP4.1x4.1mm','QFN-64 9×9×0.85, EP 4.1','e 0.50',K,'OK.','Silabs CP2108')
r('OK','USB2UART','FT230XS-R',1,'Package_SO:SSOP-16_3.9x4.9mm_P0.635mm','SSOP-16 150 mil, e 0.635','',K,'OK.','FTDI DS_FT230X')
r('OK','USB2UART','FT231XS-R',1,'Package_SO:SSOP-20_3.9x8.7mm_P0.635mm','SSOP-20 150 mil, e 0.635','',K,'OK.','FTDI DS_FT231X')
r('OK','USB2UART','FT232RNL-REEL',1,'Package_SO:SSOP-28_5.3x10.2mm_P0.65mm','SSOP-28 5.3×10.2, e 0.65','',K,'OK.','FTDI DS_FT232R')
r('OK','USB2UART','MCP2221AT-I/ST',1,'Package_SO:TSSOP-14_4.4x5mm_P0.65mm','TSSOP-14 4.4×5.0','',K,'OK.','Microchip MCP2221A')
r('OK','USB2UART','USBLC6-2SC6',9,'Package_TO_SOT_SMD:SOT-23-6','SOT-23-6','',K,'OK.','ST USBLC6-2')
# memory
r('OK','EEPROM','24LC256T-I/SN, M24C64-RMN6TP, AT25256B-SSHL-T',3,'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','SOIC-8 150 mil (SN / SO8N / SSHL)','e 1.27',K,'OK.','Microchip / ST datasheets')
r('OK','EEPROM','24AA02E48T-I/OT',1,'Package_TO_SOT_SMD:SOT-23-5','SOT-23-5 (OT)','',K,'OK.','Microchip 24AA02E48')
r('OK','NOR','W25Q128JVSIQ, MX25L12833FM2I-10G, IS25LP128F-JBLE',3,'Package_SO:SOIC-8_5.3x5.3mm_P1.27mm','SOIC-8 208 mil (5.28×5.23), span 7.9','e 1.27',K,'OK – all three are the 208 mil body.','Winbond / Macronix / ISSI')
r('OK','NAND','MX35LF1GE4AB-Z4I, GD5F1GQ5UEYIGR',2,CF+'WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm','8-WSON 8×6×0.75, EP 3.4×4.3','e 1.27',CH,'Land OK. KiCad STEP not installed → Chinmay model.','Macronix / GigaDevice')
r('OK','NAND','W29N01HVSINA',1,'Package_SO:TSOP-I-48_18.4x12mm_P0.5mm','TSOP-I-48 18.4×12×1.0, span 20.0, b 0.22','e 0.50',K,'OK – matches datasheet §13.1.','Winbond W29N01HV p49')
# passives
r('OK','All','Resistors 0603 (house 1 %)',156,'Resistor_SMD:R_0603_1608Metric','0603 / 1608M','',K,'OK – all resistors on 0603 house parts.','Yageo RC0603')
r('OK','All','Capacitors 0603 (C0G ≤1 nF, X7R)',161,'Capacitor_SMD:C_0603_1608Metric','0603 / 1608M','',K,'OK.','Murata / Samsung')
r('OK','All','Capacitors 0805',2,'Capacitor_SMD:C_0805_2012Metric','0805','',K,'OK.','')
r('OK','All','Capacitors 1206',12,'Capacitor_SMD:C_1206_3216Metric','1206','',K,'OK.','')
r('OK','All','Capacitors 1210 (bulk MLCC)',39,'Capacitor_SMD:C_1210_3225Metric','1210','',K,'OK.','')
json.dump(rows,open('/home/claude/review/rows.json','w'))
print(len(rows))

"""Schematic / symbol / BOM specification for each Chinmay_BUCK block."""

# symbol pins: (side, name, [numbers], type)   type: pi=power_in po=power_out in out oc pas nc
SYM = {
 'MAX17761': dict(fp='Package_DFN_QFN:Maxim_TDFN-12-1EP_3x3mm_P0.5mm_EP1.7x2.5mm', desc='4.5-76V 1A synchronous buck, TDFN-12 3x3',
   ds='https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17761.pdf',
   L=[('VIN',[1],'pi'),('EN/UVLO',[4],'in'),('RT/SYNC',[6],'in'),('MODE/ILIM',[10],'in'),('SS',[9],'pas'),('EXTVCC',[7],'pi'),('VCC',[3],'po')],
   R=[('LX',[12],'out'),('FB',[8],'in'),('~{RESET}',[5],'oc'),('PGND',[2],'pi'),('SGND',[11,13],'pi')]),
 'MAX17503': dict(fp='Package_DFN_QFN:TQFN-20-1EP_5x5mm_P0.65mm_EP3.1x3.1mm_ThermalVias', desc='4.5-60V 2.5A synchronous buck, TQFN-20 5x5',
   ds='https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17503.pdf',
   L=[('VIN',[1,2,3],'pi'),('EN/UVLO',[4],'in'),('SYNC',[6],'in'),('MODE',[11],'in'),('RT',[10],'in'),('SS',[7],'pas'),('CF',[8],'pas'),('VCC',[12],'po')],
   R=[('BST',[20],'pas'),('LX',[17,18,19],'out'),('FB',[9],'in'),('~{RESET}',[5],'oc'),('PGND',[14,15,16],'pi'),('SGND',[13,21],'pi')]),
 'MAX17506': dict(fp='Package_DFN_QFN:TQFN-20-1EP_5x5mm_P0.65mm_EP3.25x3.25mm_ThermalVias', desc='4.5-60V 5A synchronous buck (ext. LS FET), TQFN-20 5x5',
   ds='https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17506.pdf',
   L=[('VIN',[1,2,14,15],'pi'),('EN/UVLO',[13],'in'),('MODE/SYNC',[5],'in'),('RT',[7],'in'),('SS',[12],'pas'),('CF',[9],'pas'),('EXTVCC',[11],'pi'),('VCC',[4],'po')],
   R=[('BST',[16],'pas'),('LX',[17,18,19],'out'),('DL',[20],'out'),('FB',[10],'in'),('~{RESET}',[6],'oc'),('PGND',[3],'pi'),('SGND',[8,21],'pi')]),
 'RAA211630': dict(fp='Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm', desc='4.5-60V 3A synchronous buck, HTSSOP-16',
   ds='https://www.renesas.com/en/document/dst/raa211630-datasheet',
   L=[('VIN',[4],'pi'),('EN',[5],'in'),('FS',[7],'in'),('SS',[11],'pas'),('EBIAS',[12],'pi'),('VCC',[6],'po')],
   R=[('BST',[13],'pas'),('SW',[14,15,16],'out'),('FB',[10],'in'),('PG',[8],'oc'),('AGND',[9],'pi'),('PGND',[1,2,3,17],'pi')]),
 'LT8640S': dict(fp='', desc='42V 6A Silent Switcher 2 synchronous buck, LQFN-24 4x4',
   ds='https://www.analog.com/media/en/technical-documentation/data-sheets/lt8640s-lt8643s-lt8640sa-lt8643sa.pdf',
   L=[('VIN',[5,6,13,14],'pi'),('EN/UV',[17],'in'),('SYNC/MODE',[20],'in'),('RT',[18],'pas'),('TR/SS',[21],'pas'),('INTVCC',[2],'po'),('BIAS',[1],'pi'),('CLKOUT',[19],'out')],
   R=[('BST',[7],'pas'),('SW',[8,9,10,11,12],'out'),('FB',[24],'in'),('PG',[23],'oc'),('GND',[3,16,22,25,26,27,28],'pi'),('NC',[4,15],'nc')]),
 'LT8645S': dict(fp='', desc='65V 8A Silent Switcher 2 synchronous buck, LQFN-32 6x4',
   ds='https://www.analog.com/media/en/technical-documentation/data-sheets/lt8645s-8646s.pdf',
   L=[('VIN',[4,5,6,21,22,23],'pi'),('EN/UV',[25],'in'),('SYNC/MODE',[28],'in'),('RT',[26],'pas'),('TR/SS',[29],'pas'),('INTVCC',[2],'po'),('BIAS',[1],'pi'),('CLKOUT',[27],'out')],
   R=[('BST',[11],'pas'),('SW',[12,13,14,15,16],'out'),('FB',[32],'in'),('PG',[31],'oc'),('GND',[8,9,10,17,18,19,30,33,34,35,36,37,38],'pi'),('NC',[3,7,20,24],'nc')]),
 'LT8648S': dict(fp='', desc='42V 15A Silent Switcher 2 synchronous buck, LQFN-36 7x4',
   ds='https://www.analog.com/media/en/technical-documentation/data-sheets/lt8648s.pdf',
   L=[('VIN',[19,20,21,26,27,28],'pi'),('EN/UV',[29],'in'),('SYNC/MODE',[32],'in'),('RT',[30],'pas'),('SS',[35],'pas'),('VC',[34],'pas'),('INTVCC',[2],'po'),('BIAS',[1],'pi')],
   R=[('BST',[3],'pas'),('SW',[4,5,6,7,8,9,10,11,12],'out'),('FB',[36],'in'),('PG',[33],'oc'),('CLKOUT',[31],'out'),('GND',[13,14,15,16,17,18,23,24,37,38,39,40,41,42],'pi'),('NC',[22,25],'nc')]),
 'MP8795H': dict(fp='', desc='4-16V 20A synchronous buck, QFN-21 3x4',
   ds='https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MP8795H/document_id/9123',
   L=[('VIN',[10,21],'pi'),('EN',[8],'in'),('MODE',[4],'in'),('CS',[3],'pas'),('REF/TRK',[5],'pas'),('VCC',[19],'po')],
   R=[('BST',[1],'pas'),('SW',[20],'out'),('FB',[7],'in'),('VSNS-',[6],'pas'),('PGOOD',[9],'oc'),('AGND',[2],'pi'),('PGND',[11,12,13,14,15,16,17,18],'pi')]),
}
SYM['RAA211450'] = dict(SYM['RAA211630'], desc='4.5-42V 5A synchronous buck, HTSSOP-16',
                        ds='https://www.renesas.com/en/document/dst/raa211450-datasheet')

# IC pin -> net  ('GND' = ground symbol, 'NC' = no-connect flag)
PINNET = {
 'MAX17761': {'VIN':'VIN','EN/UVLO':'EN','RT/SYNC':'RT','MODE/ILIM':'NC','SS':'SS','EXTVCC':'GND','VCC':'VCC',
              'LX':'SW','FB':'FB','~{RESET}':'PG','PGND':'GND','SGND':'GND'},
 'MAX17503': {'VIN':'VIN','EN/UVLO':'EN','SYNC':'GND','MODE':'NC','RT':'NC','SS':'SS','CF':'NC','VCC':'VCC',
              'BST':'BST','LX':'SW','FB':'FB','~{RESET}':'PG','PGND':'GND','SGND':'GND'},
 'MAX17506': {'VIN':'VIN','EN/UVLO':'EN','MODE/SYNC':'NC','RT':'NC','SS':'SS','CF':'NC','EXTVCC':'GND','VCC':'VCC',
              'BST':'BST','LX':'SW','DL':'DL','FB':'FB','~{RESET}':'PG','PGND':'GND','SGND':'GND'},
 'RAA211630': {'VIN':'VIN','EN':'EN','FS':'FS','SS':'SS','EBIAS':'VOUT','VCC':'VCC','BST':'BST','SW':'SW','FB':'FB',
               'PG':'PG','AGND':'GND','PGND':'GND'},
 'LT8640S': {'VIN':'VIN','EN/UV':'EN','SYNC/MODE':'GND','RT':'RT','TR/SS':'SS','INTVCC':'NC','BIAS':'VOUT','CLKOUT':'NC',
             'BST':'NC','SW':'SW','FB':'FB','PG':'PG','GND':'GND','NC':'NC'},
 'LT8648S': {'VIN':'VIN','EN/UV':'EN','SYNC/MODE':'GND','RT':'RT','SS':'SS','VC':'VC','INTVCC':'INTVCC','BIAS':'VOUT',
             'BST':'NC','SW':'SW','FB':'FB','PG':'PG','CLKOUT':'NC','GND':'GND','NC':'NC'},
 'MP8795H': {'VIN':'VIN','EN':'EN','MODE':'GND','CS':'CS','REF/TRK':'REF','VCC':'VCC','BST':'BST','SW':'SW','FB':'FB',
             'VSNS-':'GND','PGOOD':'PG','AGND':'GND','PGND':'GND'},
}
PINNET['RAA211450'] = PINNET['RAA211630']
PINNET['LT8645S'] = PINNET['LT8640S']

# passives: (kind, value, net1(pin1/top), net2(pin2/bottom), spec)  spec = package / mpn key
def P(kind, value, n1, n2, spec, role=''):
    return dict(kind=kind, value=value, n1=n1, n2=n2, spec=spec, role=role)

def passives(name, parts):
    rt, rb = parts['R_top'][1], parts['R_bot'][1]
    if name == 'MAX17761':
        return [P('C','2.2uF','VIN','GND','2.2u100v1210','CIN'), P('C','0.1uF','VIN','GND','0.1u100v0603','CIN HF'),
                P('R','3.32M','VIN','EN','0603','UVLO top'), P('R',parts['R2'],'EN','GND','0603','UVLO bot'),
                P('R','105k','RT','GND','0603','RT 400kHz'), P('C','22nF','SS','GND','22n0603','CSS'),
                P('C','1uF','VCC','GND','1u16v0603','CVCC'), P('L','22uH','SW','VOUT','XAL5050-223ME','L'),
                P('C','47uF','VOUT','GND','47u10v1210','COUT'), P('R',rt,'VOUT','FB','0603','R4 FB top'),
                P('R',rb,'FB','GND','0603','R5 FB bot'), P('R',parts['R6'],'FB','COMP','0603','R6 comp'),
                P('C','6.8nF','COMP','GND','6n8_0603','C6 comp'), P('R','10k','VOUT','PG','0603','RESET pull-up')]
    if name == 'MAX17503':
        return [P('C','2.2uF','VIN','GND','2.2u100v1210','CIN'), P('C','0.1uF','VIN','GND','0.1u100v0603','CIN HF'),
                P('R','3.32M','VIN','EN','0603','UVLO top'), P('R',parts['R2'],'EN','GND','0603','UVLO bot'),
                P('C','10nF','SS','GND','10n0603','CSS'), P('C','2.2uF','VCC','GND','2.2u10v0603','CVCC'),
                P('C','0.1uF','BST','SW','0.1u50v0603','CBST'), P('L','6.8uH','SW','VOUT','XAL6060-682ME','L'),
                P('C','47uF','VOUT','GND','47u10v1210','COUT'), P('R',rt,'VOUT','FB','0603','R3 FB top'),
                P('R',rb,'FB','GND','0603','R4 FB bot'), P('R','10k','VOUT','PG','0603','RESET pull-up')]
    if name == 'MAX17506':
        return [P('C','2.2uF','VIN','GND','2.2u100v1210','CIN'), P('C','2.2uF','VIN','GND','2.2u100v1210','CIN'),
                P('C','0.1uF','VIN','GND','0.1u100v0603','CIN HF'),
                P('R','3.32M','VIN','EN','0603','UVLO top'), P('R',parts['R2'],'EN','GND','0603','UVLO bot'),
                P('C','22nF','SS','GND','22n0603','CSS'), P('C','2.2uF','VCC','GND','2.2u10v0603','CVCC'),
                P('C','0.1uF','BST','SW','0.1u50v0603','CBST'), P('L','3.3uH','SW','VOUT','XAL7070-332ME','L'),
                P('R','4.7R','DL','DLG','0603','DL gate R'), P('Q','SiS468DN','SW','GND','SiS468DN','LS FET'),
                P('C','47uF','VOUT','GND','47u10v1210','COUT'), P('C','47uF','VOUT','GND','47u10v1210','COUT'),
                P('C','22uF','VOUT','GND','22u25v1210','COUT'), P('R',rt,'VOUT','FB','0603','R3 FB top'),
                P('R',rb,'FB','GND','0603','R4 FB bot'), P('R','10k','VOUT','PG','0603','RESET pull-up')]
    if name in ('RAA211630', 'RAA211450'):
        big = name == 'RAA211450'
        cin = ('4.7uF','4.7u50v1210') if big else ('2.2uF','2.2u100v1210')
        Lp = ('3.3uH','XAL7070-332ME') if big else ('6.8uH','XAL6060-682ME')
        co = ('47uF','47u10v1210') if big else ('22uF','22u25v1210')
        return [P('C',cin[0],'VIN','GND',cin[1],'CIN'), P('C',cin[0],'VIN','GND',cin[1],'CIN'),
                P('C','0.1uF','VIN','GND','0.1u100v0603','CIN HF'),
                P('R',parts['RIN1'],'VIN','EN','0603','RIN1 UVLO'), P('R','100k','EN','GND','0603','RIN2 UVLO'),
                P('R','261k','FS','GND','0603','RFS 400kHz'), P('C','10nF','SS','GND','10n0603','CSS'),
                P('C','2.2uF','VCC','GND','2.2u10v0603','CVCC'), P('C','0.1uF','BST','SW','0.1u50v0603','CBOOT'),
                P('L',Lp[0],'SW','VOUT',Lp[1],'L'),
                P('C',co[0],'VOUT','GND',co[1],'COUT'), P('C',co[0],'VOUT','GND',co[1],'COUT'), P('C',co[0],'VOUT','GND',co[1],'COUT'),
                P('R',rt,'VOUT','FB','0603','RFB1'), P('R',rb,'FB','GND','0603','RFB2'), P('R','10k','VOUT','PG','0603','PG pull-up')]
    if name == 'LT8640S':
        return [P('C','4.7uF','VIN','GND','4.7u50v1210','CIN side A'), P('C','4.7uF','VIN','GND','4.7u50v1210','CIN side B'),
                P('R',parts['R3'],'VIN','EN','0603','EN/UV top'), P('R','100k','EN','GND','0603','EN/UV bot'),
                P('R',parts['RT'],'RT','GND','0603','RT 1MHz'), P('C','10nF','SS','GND','10n0603','CSS'),
                P('L','2.2uH','SW','VOUT','XEL6030-222ME','L'), P('C','100uF','VOUT','GND','100u6v1210','COUT'),
                P('R',rt,'VOUT','FB','0603','R1 FB top'), P('C','10pF','VOUT','FB','10p0603','CFF'),
                P('R',rb,'FB','GND','0603','R2 FB bot'), P('R','10k','VOUT','PG','0603','PG pull-up')]
    if name == 'LT8645S':
        return [P('C','2.2uF','VIN','GND','2.2u100v1210','CIN side A'), P('C','2.2uF','VIN','GND','2.2u100v1210','CIN side B'),
                P('R',parts['R3'],'VIN','EN','0603','EN/UV top'), P('R','100k','EN','GND','0603','EN/UV bot'),
                P('R',parts['RT'],'RT','GND','0603','RT 500kHz'), P('C','10nF','SS','GND','10n0603','CSS'),
                P('L','3.3uH','SW','VOUT','XAL7070-332ME','L'), P('C','47uF','VOUT','GND','47u10v1210','COUT'),
                P('C','47uF','VOUT','GND','47u10v1210','COUT'),
                P('R',rt,'VOUT','FB','0603','R1 FB top'), P('C','2.2pF','VOUT','FB','2p2_0603','CFF'),
                P('R',rb,'FB','GND','0603','R2 FB bot'), P('R','10k','VOUT','PG','0603','PG pull-up')]
    if name == 'LT8648S':
        return [P('C','10uF','VIN','GND','10u50v1210','CIN side A'), P('C','10uF','VIN','GND','10u50v1210','CIN side B'),
                P('R',parts['R3'],'VIN','EN','0603','EN/UV top'), P('R','100k','EN','GND','0603','EN/UV bot'),
                P('R',parts['RT'],'RT','GND','0603','RT 400kHz'), P('C','10nF','SS','GND','10n0603','CSS'),
                P('C','1uF','INTVCC','GND','1u16v0603','CINTVCC'), P('R','6.65k','VC','VCRC','0603','RC'),
                P('C','820pF','VCRC','GND','820p0603','CC'),
                P('L','2.2uH','SW','VOUT','XAL8080-222ME','L'), P('C','47uF','VOUT','GND','47u10v1210','COUT'),
                P('C','47uF','VOUT','GND','47u10v1210','COUT'), P('C','47uF','VOUT','GND','47u10v1210','COUT'),
                P('R',rt,'VOUT','FB','0603','R1 FB top'), P('C','33pF','VOUT','FB','33p0603','CFF'),
                P('R',rb,'FB','GND','0603','R2 FB bot'), P('R','10k','VOUT','PG','0603','PG pull-up')]
    if name == 'MP8795H':
        return [P('C','22uF','VIN','GND','22u25v1210','CIN1'), P('C','22uF','VIN','GND','22u25v1210','CIN2'),
                P('C','22uF','VIN','GND','22u25v1210','CIN3'), P('C','0.1uF','VIN','GND','0.1u50v0603','CIN HF'),
                P('R',parts['RUP'],'VIN','EN','0603','EN RUP'), P('R','100k','EN','GND','0603','EN RDOWN'),
                P('R',parts['RCS'],'CS','GND','0603','RCS ILIM'), P('C','22nF','REF','GND','22n0603','CSS1'),
                P('C','100nF','REF','GND','100n0603','CSS2'), P('C','2.2uF','VCC','GND','2.2u10v0603','CVCC'),
                P('C','0.1uF','BST','SW','0.1u50v0603','CBST'), P('L','0.68uH','SW','VOUT','XAL1010-681ME','L'),
                P('C','100uF','VOUT','GND','100u6v1210','COUT'), P('C','100uF','VOUT','GND','100u6v1210','COUT'),
                P('C','100uF','VOUT','GND','100u6v1210','COUT'), P('C','100uF','VOUT','GND','100u6v1210','COUT'),
                P('R',rt,'VOUT','FB','0603','RFB1'), P('C','220pF','VOUT','FB','220p0603','CFF'),
                P('R',rb,'FB','GND','0603','RFB2'), P('R','10k','VOUT','PG','0603','PG pull-up')]

# capacitor / inductor / FET catalogue: key -> (footprint, Manufacturer, MPN1, MFR2, MPN2, description)
CAT = {
 '2.2u100v1210': ('Capacitor_SMD:C_1210_3225Metric','Murata','GRM32ER72A225KA35L','TDK','C3225X7R2A225K230AB','2.2uF 100V X7R 1210'),
 '0.1u100v0603': ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R72A104KA35D','TDK','C1608X7S2A104K080AB','0.1uF 100V X7R 0603'),
 '0.1u50v0603':  ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71H104KA93D','Samsung','CL10B104KB8NNNC','0.1uF 50V X7R 0603'),
 '1u16v0603':    ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71C105KA12D','Samsung','CL10B105KO8NNNC','1uF 16V X7R 0603'),
 '2.2u10v0603':  ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71A225KE15D','Samsung','CL10B225KP8NNNC','2.2uF 10V X7R 0603'),
 '4.7u50v1210':  ('Capacitor_SMD:C_1210_3225Metric','Murata','GRM32ER71H475KA88L','TDK','C3225X7R1H475K250AB','4.7uF 50V X7R 1210'),
 '10u50v1210':   ('Capacitor_SMD:C_1210_3225Metric','Murata','GRM32ER71H106KA12L','TDK','C3225X7R1H106K250AC','10uF 50V X7R 1210'),
 '22u25v1210':   ('Capacitor_SMD:C_1210_3225Metric','Murata','GRM32ER71E226KE15L','TDK','C3225X7R1E226M250AC','22uF 25V X7R 1210'),
 '47u10v1210':   ('Capacitor_SMD:C_1210_3225Metric','Murata','GRM32ER71A476KE15L','TDK','C3225X7R1A476M250AC','47uF 10V X7R 1210'),
 '22u10v1210':   ('Capacitor_SMD:C_1210_3225Metric','Murata','GRM32ER71A226KE20L','TDK','C3225X7R1A226M230AC','22uF 10V X7R 1210'),
 '100u6v1210':   ('Capacitor_SMD:C_1210_3225Metric','Murata','GRM32ER60J107ME20L','TDK','C3225X5R0J107M250AC','100uF 6.3V X5R 1210'),
 '33n0603':      ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71H333KA61D','Samsung','CL10B333KB8NNNC','33nF 50V X7R 0603'),
 '22n0603':      ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71H223KA01D','Samsung','CL10B223KB8NNNC','22nF 50V X7R 0603'),
 '15n0603':      ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71H153KA01D','Samsung','CL10B153KB8NNNC','15nF 50V X7R 0603'),
 '10n0603':      ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71H103KA01D','Samsung','CL10B103KB8NNNC','10nF 50V X7R 0603'),
 '100n0603':     ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71H104KA93D','Samsung','CL10B104KB8NNNC','100nF 50V X7R 0603'),
 '6n8_0603':     ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71H682KA01D','Samsung','CL10B682KB8NNNC','6.8nF 50V X7R 0603'),
 '5n6_0603':     ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM188R71H562KA01D','Samsung','CL10B562KB8NNNC','5.6nF 50V X7R 0603'),
 '820p0603':     ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM1885C1H821JA01D','Samsung','CL10C821JB8NNNC','820pF 50V C0G 0603'),
 '220p0603':     ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM1885C1H221JA01D','Samsung','CL10C221JB8NNNC','220pF 50V C0G 0603'),
 '33p0603':      ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM1885C1H330JA01D','Samsung','CL10C330JB8NNNC','33pF 50V C0G 0603'),
 '10p0603':      ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM1885C1H100JA01D','Samsung','CL10C100JB8NNNC','10pF 50V C0G 0603'),
 '2p2_0603':     ('Capacitor_SMD:C_0603_1608Metric','Murata','GRM1885C1H2R2CA01D','Samsung','CL10C2R2CB8NNNC','2.2pF 50V C0G 0603'),
 'XAL5050-223ME':('Inductor_SMD:L_Coilcraft_XAL5050-XXX','Coilcraft','XAL5050-223MEC','','','22uH shielded, XAL5050'),
 'XAL6060-682ME':('Inductor_SMD:L_Coilcraft_XAL6060-XXX','Coilcraft','XAL6060-682MEC','','','6.8uH shielded, XAL6060'),
 'XAL7070-332ME':('Inductor_SMD:L_Coilcraft_XAL7070-XXX','Coilcraft','XAL7070-332MEC','','','3.3uH shielded, XAL7070'),
 'XEL6030-222ME':('Inductor_SMD:L_Coilcraft_XAL6030-XXX','Coilcraft','XEL6030-222MEC','Coilcraft','XAL6030-222MEC','2.2uH shielded, XEL6030 (datasheet part)'),
 'XAL8080-222ME':('Inductor_SMD:L_Coilcraft_XAL8080-XXX','Coilcraft','XAL8080-222MEC','','','2.2uH shielded, XAL8080 (datasheet part)'),
 'XAL1010-681ME':('Inductor_SMD:L_Coilcraft_XAL1010-XXX','Coilcraft','XAL1010-681MEC','','','0.68uH shielded, XAL1010'),
 'SiS468DN':     ('Package_SO:Vishay_PowerPAK_1212-8_Single','Vishay','SIS468DN-T1-GE3','','','N-MOSFET 80V PowerPAK 1212-8 (datasheet part)'),
}

IC_BOM = {
 'MAX17761': ('Analog Devices (Maxim)','MAX17761ATC+','Analog Devices (Maxim)','MAX17761ATC+T'),
 'MAX17503': ('Analog Devices (Maxim)','MAX17503ATP+','Analog Devices (Maxim)','MAX17503ATP+T'),
 'MAX17506': ('Analog Devices (Maxim)','MAX17506ATP+','Analog Devices (Maxim)','MAX17506ATP+T'),
 'RAA211630': ('Renesas','RAA211630GSP#HA0','Renesas','RAA211630GNP#HA0 (QFN, no SS pin)'),
 'RAA211450': ('Renesas','RAA211450GSP#HA0','Renesas','RAA211450GNP#HA0 (QFN, no SS pin)'),
 'LT8640S': ('Analog Devices','LT8640SEV#PBF','Analog Devices','LT8640SIV#PBF'),
 'LT8645S': ('Analog Devices','LT8645SEV#PBF','Analog Devices','LT8645SIV#PBF'),
 'LT8648S': ('Analog Devices','LT8648SEV#PBF','Analog Devices','LT8648SJV#PBF'),
 'MP8795H': ('Monolithic Power Systems','MP8795HGLE-Z','Monolithic Power Systems','MP8795HGLE-P'),
}

IMG = {  # image files + caption
 'MAX17761': [('MAX17761.png', 'Analog Devices/Maxim MAX17761 datasheet 19-8608 Rev 1, p.15, Figure 5 (3.3 V output)')],
 'MAX17503': [('MAX17503.png', 'Analog Devices/Maxim MAX17503 datasheet 19-7005, p.24, Figure 4b (3.3 V, 500 kHz)')],
 'MAX17506': [('MAX17506.png', 'Analog Devices/Maxim MAX17506 datasheet 19-8526, p.18, Figure 4 (3.3 V output)')],
 'RAA211630': [('RAA211630.png', 'Renesas RAA211630 datasheet R16DS0178EU0101 Rev 1.01, p.1, Figure 1'),
               ('RAA211630_tbl.png', 'Renesas RAA211630 datasheet, p.5, Sec 2.3 Recommended component values')],
 'RAA211450': [('RAA211450.png', 'Renesas RAA211450 datasheet R16DS0183EU0102 Rev 1.02, p.1, Figure 1'),
               ('RAA211450_tbl.png', 'Renesas RAA211450 datasheet, p.5, Sec 2.3 Recommended component values')],
 'LT8640S': [('LT8640S.png', 'Analog Devices LT8640S datasheet Rev D, p.27, Figure 11 (3.3 V, 6 A, 1 MHz)')],
 'LT8645S': [('LT8645S.png', 'Analog Devices LT8645S/LT8646S datasheet Rev E, p.26, Figure 9 (3.3 V, 8 A)')],
 'LT8648S': [('LT8648S.png', 'Analog Devices LT8648S datasheet Rev E, p.24, Figure 10 (400 kHz 3.3 V, 15 A)')],
 'MP8795H': [('MP8795H.png', 'MPS MP8795H datasheet Rev 1.0, p.2, Typical Application')],
}

ORDER = ['MAX17761', 'MAX17503', 'RAA211630', 'MAX17506', 'RAA211450', 'LT8640S', 'LT8645S', 'LT8648S', 'MP8795H']
MFR = {'MAX17761':'Analog Devices (Maxim)','MAX17503':'Analog Devices (Maxim)','MAX17506':'Analog Devices (Maxim)',
       'RAA211630':'Renesas (Intersil)','RAA211450':'Renesas (Intersil)','LT8640S':'Analog Devices (LTC)',
       'LT8645S':'Analog Devices (LTC)','LT8648S':'Analog Devices (LTC)','MP8795H':'Monolithic Power Systems'}

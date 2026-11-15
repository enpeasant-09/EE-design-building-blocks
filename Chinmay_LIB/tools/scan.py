import re,os,json,glob,sys
def blocks(s, start):
    # return end index of balanced paren block starting at start
    d=0;i=start
    while True:
        c=s[i]
        if c=='"':
            i+=1
            while s[i]!='"':
                if s[i]=='\\': i+=1
                i+=1
        elif c=='(': d+=1
        elif c==')':
            d-=1
            if d==0: return i+1
        i+=1
def prop(b,n):
    m=re.search(r'\(property\s+"%s"\s+"((?:[^"\\]|\\.)*)"'%re.escape(n),b); return m.group(1) if m else ''
rows=[]
roots={'BUCK':'/mnt/user-data/outputs/buck','LDO':'/mnt/user-data/outputs/ldo','XTAL':'/mnt/user-data/outputs/xtal_blocks','WD_RST':'/mnt/user-data/outputs/wd','USB2UART':'/mnt/user-data/outputs/usb'}
for lib,root in roots.items():
    for f in sorted(glob.glob(root+'/**/*.kicad_sch',recursive=True)):
        s=open(f,encoding='utf-8').read()
        ls=s.find('(lib_symbols'); le=blocks(s,ls) if ls>=0 else 0
        for m in re.finditer(r'\(symbol\s+\(lib_id\s+"([^"]+)"\)',s):
            if ls<=m.start()<le: continue
            e=blocks(s,m.start()); b=s[m.start():e]
            lid=m.group(1)
            if lid.startswith('power:'): continue
            rows.append(dict(lib=lib,file=os.path.relpath(f,root),lib_id=lid,ref=prop(b,'Reference'),val=prop(b,'Value'),fp=prop(b,'Footprint'),mpn=prop(b,'MPN1') or prop(b,'MPN'),mfr=prop(b,'Manufacturer'),ds=prop(b,'Datasheet'),desc=prop(b,'Description'),dnp=bool(re.search(r'\(dnp\s+yes\)',b[:600]))))
json.dump(rows,open('rows.json','w'),indent=0)
import collections
print(len(rows))
c=collections.Counter((r['fp']) for r in rows)
for k,v in c.most_common(): print(v,k)
print('--- empty fp:');rows=[r for r in rows if not r['ref'].startswith('#')]
for r in rows:
    if not r['fp']: print(r['lib'],r['file'],r['ref'],r['lib_id'],r['val'])

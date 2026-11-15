import re,glob,os,json
def parse(path):
    s=open(path).read()
    name=os.path.basename(path)[:-10]
    desc=(re.search(r'\(descr\s+"([^"]*)"',s) or [None,''])[1]
    pads=[]
    for m in re.finditer(r'\(pad\s+"([^"]*)"\s+(\w+)\s+(\w+)\s*\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)\s*\(size\s+([\d.]+)\s+([\d.]+)\)',s):
        num,typ,shape,x,y,a,w,h=m.groups(); a=float(a or 0)
        w,h=float(w),float(h)
        if a in (90,270,-90): w,h=h,w
        pads.append(dict(num=num,typ=typ,shape=shape,x=float(x),y=float(y),w=w,h=h))
    models=re.findall(r'\(model\s+"([^"]+)"',s)
    # fab outline extent
    fab=[]
    for m in re.finditer(r'\(fp_(?:line|rect|poly)[\s\S]*?\(layer\s+"F\.Fab"\)',s):
        fab+= [(float(a),float(b)) for a,b in re.findall(r'\((?:start|end|xy)\s+([-\d.]+)\s+([-\d.]+)\)',m.group(0))]
    body=None
    if fab:
        xs=[p[0] for p in fab]; ys=[p[1] for p in fab]; body=(round(max(xs)-min(xs),3),round(max(ys)-min(ys),3))
    return dict(name=name,desc=desc,pads=pads,models=models,body=body)
if __name__=='__main__':
    R={}
    for p in glob.glob('/mnt/user-data/uploads/kicad/footprints/*/*.kicad_mod')+glob.glob('/mnt/user-data/uploads/Chinmay_WD_RST/Chinmay_Supervisor.pretty/*.kicad_mod'):
        lib=os.path.basename(os.path.dirname(p)).replace('.pretty','')
        d=parse(p); R[lib+':'+d['name']]=d
    json.dump(R,open('fpdata.json','w'),indent=0)
    for k,d in sorted(R.items()):
        smd=[p for p in d['pads'] if p['num'] not in ('','~')]
        nums=sorted(set(p['num'] for p in smd))
        print(k, '| pads',len(smd),'uniq',len(nums),'| body',d['body'],'| models',[os.path.basename(m) for m in d['models']])

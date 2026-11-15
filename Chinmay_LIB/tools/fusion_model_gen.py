import adsk.core, adsk.fusion, json, os

SPECS = json.load(open(r'C:/Users/crmar/Documents/Chinmay_LIB/model_specs.json'))
OUTDIR = r'C:/Users/crmar/Documents/Chinmay_LIB/Chinmay_3D.3dshapes'
ONLY = globals().get("ONLY_SET", [])

def cm(v):
    return v / 10.0

def box(tbm, cx, cy, cz, sx, sy, sz):
    c = adsk.core.Point3D.create(cm(cx), cm(cy), cm(cz))
    obb = adsk.core.OrientedBoundingBox3D.create(c, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
                                                 cm(sx), cm(sy), cm(sz))
    return tbm.createBox(obb)

def find_app(app, words):
    for libname in ('Fusion Appearance Library', 'Fusion 360 Appearance Library'):
        lib = app.materialLibraries.itemByName(libname)
        if not lib: continue
        for i in range(lib.appearances.count):
            a = lib.appearances.item(i)
            n = a.name.lower()
            if all(w in n for w in words): return a
    return None

def run(_context: str):
    app = adsk.core.Application.get()
    os.makedirs(OUTDIR, exist_ok=True)
    black = find_app(app, ['plastic', 'matte', 'black']) or find_app(app, ['black'])
    metal = find_app(app, ['tin']) or find_app(app, ['aluminum', 'satin']) or find_app(app, ['steel', 'satin'])
    gold = find_app(app, ['gold', 'polished']) or metal
    done = []
    for d in list(app.documents):
        if d.name.startswith('Untitled') and not d.isSaved: d.close(False)
    for name, s in SPECS.items():
        if ONLY and name not in ONLY: continue
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.DirectDesignType
        root = design.rootComponent
        tbm = adsk.fusion.TemporaryBRepManager.get()
        bw, bl = s['body']; h = s['h']; st = s['style']
        hx, hy = bw / 2.0, bl / 2.0
        z0 = {'flat': 0.05, 'gull': 0.10, 'wlcsp': 0.17}[st]
        bodies = []
        body = box(tbm, 0, 0, (z0 + h) / 2.0, bw, bl, h - z0)
        bodies.append(('Body', body, black))
        # pin-1 marker (small square recess look-alike, light coloured disc on top)
        p1 = [p for p in s['pads'] if p['num'] == '1']
        if p1:
            px, py = p1[0]['x'], -p1[0]['y']
            mx = max(-hx + 0.25, min(hx - 0.25, px * 0.75)); my = max(-hy + 0.25, min(hy - 0.25, py * 0.75))
            r = min(0.15, bw / 8.0)
            cyl = tbm.createCylinderOrCone(adsk.core.Point3D.create(cm(mx), cm(my), cm(h)), cm(r),
                                           adsk.core.Point3D.create(cm(mx), cm(my), cm(h + 0.01)), cm(r))
            bodies.append(('Pin1', cyl, metal))
        for i, p in enumerate(s['pads']):
            x, y, w, hh = p['x'], -p['y'], p['w'], p['h']
            if st == 'wlcsp':
                sph = tbm.createSphere(adsk.core.Point3D.create(cm(x), cm(y), cm(0.125)), cm(0.125))
                bodies.append((f'Ball{p["num"]}', sph, metal)); continue
            if st == 'flat':
                # terminal footprint = pad shrunk 15 %, clipped to the body outline
                x0, x1 = x - w * 0.425, x + w * 0.425; y0, y1 = y - hh * 0.425, y + hh * 0.425
                x0, x1 = max(x0, -hx), min(x1, hx); y0, y1 = max(y0, -hy), min(y1, hy)
                if x1 - x0 < 0.02 or y1 - y0 < 0.02: continue
                t = box(tbm, (x0 + x1) / 2, (y0 + y1) / 2, 0.025, x1 - x0, y1 - y0, 0.05)
                bodies.append((f'Pad{p["num"]}_{i}', t, metal))
                # wrap-around on the package side for perimeter terminals
                if abs(abs(x) - hx) < w and (abs(x0 + hx) < 0.01 or abs(x1 - hx) < 0.01):
                    sx = -hx if x < 0 else hx
                    bodies.append((f'Side{i}', box(tbm, sx + (0.01 if x < 0 else -0.01), (y0 + y1) / 2, 0.11, 0.02, y1 - y0, 0.2), metal))
                elif abs(abs(y) - hy) < hh and (abs(y0 + hy) < 0.01 or abs(y1 - hy) < 0.01):
                    sy = -hy if y < 0 else hy
                    bodies.append((f'Side{i}', box(tbm, (x0 + x1) / 2, sy + (0.01 if y < 0 else -0.01), 0.11, x1 - x0, 0.02, 0.2), metal))
                continue
            # gull wing: foot + leg + arm, direction from body outward
            if abs(x) > hx:      # left/right leads
                d = 1 if x > 0 else -1
                foot_out = d * s['span'] / 2 if 'span' in s else x + d * w * 0.35
                foot_in = foot_out - d * s['L'] if 'L' in s else x - d * w * 0.35
                lw = hh * 0.7; t = 0.15
                bodies.append((f'Foot{i}', box(tbm, (foot_in + foot_out) / 2, y, t / 2, abs(foot_out - foot_in), lw, t), metal))
                leg_x = foot_in + d * t / 2
                bodies.append((f'Leg{i}', box(tbm, leg_x, y, h * 0.3, t, lw, h * 0.6), metal))
                ax0, ax1 = d * hx, leg_x
                bodies.append((f'Arm{i}', box(tbm, (ax0 + ax1) / 2, y, h * 0.55, abs(ax1 - ax0) + t / 2, lw, t), metal))
            elif abs(y) > hy:
                d = 1 if y > 0 else -1
                foot_out = d * s['span'] / 2 if 'span' in s else y + d * hh * 0.35
                foot_in = foot_out - d * s['L'] if 'L' in s else y - d * hh * 0.35
                lw = w * 0.7; t = 0.15
                bodies.append((f'Foot{i}', box(tbm, x, (foot_in + foot_out) / 2, t / 2, lw, abs(foot_out - foot_in), t), metal))
                leg_y = foot_in + d * t / 2
                bodies.append((f'Leg{i}', box(tbm, x, leg_y, h * 0.3, lw, t, h * 0.6), metal))
                ay0, ay1 = d * hy, leg_y
                bodies.append((f'Arm{i}', box(tbm, x, (ay0 + ay1) / 2, h * 0.55, lw, abs(ay1 - ay0) + t / 2, t), metal))
            else:                # exposed pad under the body
                t = box(tbm, x, y, 0.05, w * 0.9, hh * 0.9, 0.1)
                bodies.append((f'EP{i}', t, metal))
        for nm, tb, ap in bodies:
            b = root.bRepBodies.add(tb)
            b.name = nm
            if ap:
                a = design.appearances.itemByName(ap.name) or design.appearances.addByCopy(ap, ap.name)
                b.appearance = a
        path = os.path.join(OUTDIR, name + '.step')
        opts = design.exportManager.createSTEPExportOptions(path, root)
        design.exportManager.execute(opts)
        done.append((name, len(bodies), os.path.getsize(path)))
        doc.close(False)
    for d in done: print(d)
    print('appearances', black.name if black else None, metal.name if metal else None)

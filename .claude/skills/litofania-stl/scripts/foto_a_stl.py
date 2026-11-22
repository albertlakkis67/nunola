#!/usr/bin/env python3
"""Foto -> STL (litofanía o relieve) con marco y agujero opcionales. Solo numpy y Pillow."""
import argparse, os, numpy as np
from PIL import Image, ImageOps, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("foto"); ap.add_argument("salida")
ap.add_argument("--tipo", choices=["litofania", "relieve"], default="litofania")
ap.add_argument("--ancho", type=float, default=100)
ap.add_argument("--proporcion", default="3:4")
ap.add_argument("--centro-x", type=float, default=0.5); ap.add_argument("--centro-y", type=float, default=0.5)
ap.add_argument("--min", type=float); ap.add_argument("--max", type=float)
ap.add_argument("--marco", type=float, default=4); ap.add_argument("--agujero", type=float, default=5)
ap.add_argument("--invertir", action="store_true"); ap.add_argument("--res", type=float, default=0.25)
a = ap.parse_args()
lito = a.tipo == "litofania"
tmin = a.min if a.min is not None else (0.8 if lito else 2.0)
tmax = a.max if a.max is not None else (3.0 if lito else 5.0)
RES = a.res

im = ImageOps.exif_transpose(Image.open(a.foto)).convert("L")
w, h = im.size
if a.proporcion != "original":
    pw, ph = map(float, a.proporcion.split(":")); r = pw / ph
    cw, ch = (w, w / r) if w / h < r else (h * r, h)
    x0 = min(max(a.centro_x * w - cw / 2, 0), w - cw); y0 = min(max(a.centro_y * h - ch / 2, 0), h - ch)
    im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))
im = ImageOps.autocontrast(im, cutoff=1).filter(ImageFilter.SMOOTH)
F = a.marco
iw = a.ancho - 2 * F; ih = iw * im.size[1] / im.size[0]
nx, ny = int(round(iw / RES)), int(round(ih / RES))
g = np.asarray(im.resize((nx, ny), Image.LANCZOS), dtype=float) / 255.0
if lito or not a.invertir:
    inner = tmax - (tmax - tmin) * g          # oscuro = grueso (litofanía) / oscuro sube (relieve)
else:
    inner = tmin + (tmax - tmin) * g
ft = tmax + 1.0
f = int(round(F / RES))
R = a.agujero / 2
hb = int(round((2 * R + 3) / RES)) if R > 0 else 0
H = np.full((ny + 2 * f + hb, nx + 2 * f), ft if F > 0 or hb else tmin)
H[f + hb:f + hb + ny, f:f + nx] = inner
H = np.flipud(H)
rows, cols = H.shape
yy, xx = np.mgrid[0:rows, 0:cols] * RES
solid = np.ones_like(H, bool)
if R > 0:
    solid = (xx - (cols - 1) * RES / 2) ** 2 + (yy - ((rows - 1) * RES - F - R - 1.5)) ** 2 > R ** 2

X = np.arange(cols) * RES; Y = np.arange(rows) * RES
def V(i, j, top): return np.stack([X[j], Y[i], H[i, j] if top else np.zeros(len(i))], -1)
cell = solid[:-1, :-1] & solid[1:, :-1] & solid[:-1, 1:] & solid[1:, 1:]
ii, jj = np.nonzero(cell)
t = [V(ii, jj, 1), V(ii, jj + 1, 1), V(ii + 1, jj + 1, 1), V(ii + 1, jj, 1)]
b = [V(ii, jj, 0), V(ii, jj + 1, 0), V(ii + 1, jj + 1, 0), V(ii + 1, jj, 0)]
parts = [np.stack([t[0], t[1], t[2]], 1), np.stack([t[0], t[2], t[3]], 1),
         np.stack([b[0], b[2], b[1]], 1), np.stack([b[0], b[3], b[2]], 1)]
Cp = np.zeros((cell.shape[0] + 2, cell.shape[1] + 2), bool); Cp[1:-1, 1:-1] = cell
def wall(i0, j0, i1, j1):
    a0, a1, z0, z1 = V(i0, j0, 1), V(i1, j1, 1), V(i0, j0, 0), V(i1, j1, 0)
    parts.extend([np.stack([z0, z1, a1], 1), np.stack([z0, a1, a0], 1)])
c = Cp[1:-1, 1:-1]
i, j = np.nonzero(c & ~Cp[:-2, 1:-1]); wall(i, j, i, j + 1)
i, j = np.nonzero(c & ~Cp[2:, 1:-1]);  wall(i + 1, j + 1, i + 1, j)
i, j = np.nonzero(c & ~Cp[1:-1, :-2]); wall(i + 1, j, i, j)
i, j = np.nonzero(c & ~Cp[1:-1, 2:]);  wall(i, j + 1, i + 1, j + 1)
T = np.concatenate(parts).astype(np.float32)
n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]); rec["n"] = n; rec["v"] = T
with open(a.salida, "wb") as fh:
    fh.write(b"foto_a_stl".ljust(80, b" ")); fh.write(np.uint32(len(T)).tobytes()); fh.write(rec.tobytes())

# comprobación: malla cerrada (cada arista con su pareja inversa)
_, idx = np.unique(np.round(T.reshape(-1, 3), 4), axis=0, return_inverse=True); Fc = idx.reshape(-1, 3).astype(np.int64)
e = np.concatenate([Fc[:, [0, 1]], Fc[:, [1, 2]], Fc[:, [2, 0]]]); k = e[:, 0] * 10**9 + e[:, 1]; rk = e[:, 1] * 10**9 + e[:, 0]
cerrada = len(np.unique(k)) == len(k) and np.isin(k, rk).all()
vol = np.einsum("ij,ij->i", T[:, 0].astype(float), np.cross(T[:, 1], T[:, 2]).astype(float)).sum() / 6

# vista previa: relieve sombreado + simulación al trasluz
Hv = np.flipud(H); sv = np.flipud(solid)
gy, gx = np.gradient(Hv, RES); sh = np.clip(0.6 + 0.5 * (-gx * 0.7 + gy * 0.7) / np.sqrt(1 + gx**2 + gy**2), 0, 1); sh[~sv] = 0.15
rel = Image.fromarray((sh * 235).astype(np.uint8)).convert("RGB")
L = np.exp(-1.2 * (Hv - tmin)); L[~sv] = 1
lit = (np.stack([L, L * 0.9, L * 0.72], -1) / L.max()) ** 0.8 * 255
lit = Image.fromarray(lit.astype(np.uint8))
pw = 2 * cols + 30; out = Image.new("RGB", (pw, rows), (30, 30, 36)); out.paste(rel, (0, 0)); out.paste(lit, (cols + 30, 0))
if pw > 1600: out = out.resize((1600, int(rows * 1600 / pw)))
vista = os.path.splitext(a.salida)[0] + "_vista.png"; out.save(vista)
print(f"STL: {a.salida} ({os.path.getsize(a.salida)/1e6:.1f} MB, {len(T)} triángulos)")
print(f"Tamaño: {cols*RES:.1f} x {rows*RES:.1f} mm, grosor {H.min():.1f}-{H.max():.1f} mm")
print(f"Volumen: {vol/1000:.1f} cm3 (~{vol/1000*1.24:.0f} g de PLA). Malla cerrada: {'sí' if cerrada else 'NO'}")
print(f"Vista previa: {vista}")

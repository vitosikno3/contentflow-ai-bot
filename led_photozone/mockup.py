"""Нарезка 3:2 картинки на две стены + макет угловой фотозоны с силуэтами людей.
python3 mockup.py walls_3x2.png floor_1x1.png|- out_prefix   ('-' = без пола)
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

walls_p, floor_p, out = sys.argv[1:4]
walls = Image.open(walls_p).convert('RGB')
floor = None if floor_p == '-' else Image.open(floor_p).convert('RGB')

# --- нарезка под экраны: каждая стена 1,5 x 2,0 м (3:4) ---
W, H = walls.size
target_w = int(H * 3 / 2)
if W != target_w:  # подрезаем до точного 3:2
    x0 = (W - target_w) // 2
    walls = walls.crop((x0, 0, x0 + target_w, H)); W = target_w
L = walls.crop((0, 0, W // 2, H)).resize((1080, 1440), Image.LANCZOS)
R = walls.crop((W // 2, 0, W, H)).resize((1080, 1440), Image.LANCZOS)
L.save(f'{out}_wall_LEFT_1080x1440.png'); R.save(f'{out}_wall_RIGHT_1080x1440.png')
if floor is not None:
    F = floor.resize((1080, 1080), Image.LANCZOS); F.save(f'{out}_floor_1080x1080.png')


def coeffs(dst, src):  # перспективное преобразование: dst-квадрат -> src
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; b += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(b, float)).tolist()


def warp(img, quad, size):
    w, h = img.size
    c = coeffs(quad, [(0, 0), (w, 0), (w, h), (0, h)])
    out = img.transform(size, Image.PERSPECTIVE, c, Image.BICUBIC)
    mask = Image.new('L', size, 0); ImageDraw.Draw(mask).polygon(quad, fill=255)
    return out, mask


S = (2000, 1500)
canvas = Image.new('RGB', S, (12, 12, 18))
g = ImageDraw.Draw(canvas)
for y in range(S[1]):  # фон зала
    t = y / S[1]; g.line([(0, y), (S[0], y)], fill=(int(18 + 10 * t), int(16 + 8 * t), int(26 + 6 * t)))
cx, top, mid, depth = 1000, 170, 1080, 330
lw = 640  # ширина стены в проекции
# угол стоит к зрителю «вглубь»: сгиб по центру
left_q = [(cx - lw, top + depth * 0.55), (cx, top), (cx, mid), (cx - lw, mid + depth * 0.55)]
right_q = [(cx, top), (cx + lw, top + depth * 0.55), (cx + lw, mid + depth * 0.55), (cx, mid)]
floor_q = [(cx, mid), (cx + lw, mid + depth * 0.55), (cx, mid + depth * 1.1), (cx - lw, mid + depth * 0.55)]
for img, q in [(L, left_q), (R, right_q)]:
    o, m = warp(img, q, S); canvas.paste(o, (0, 0), m)
# пол: квадрат повёрнут так, что его угол уходит в сгиб
if floor is not None:
    o, m = warp(F, floor_q, S); canvas.paste(o, (0, 0), m)
else:  # обычный пол зала
    ImageDraw.Draw(canvas).polygon(floor_q, fill=(38, 34, 40))
# лёгкая тень в углу
sh = Image.new('L', S, 0); ImageDraw.Draw(sh).line([(cx, top), (cx, mid)], fill=90, width=30)
canvas.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(25)))


def person(x, base, h, col=(10, 10, 14, 235)):
    lay = Image.new('RGBA', S, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); hw = h * 0.125
    d.ellipse([x - h * 0.06, base - h, x + h * 0.06, base - h + h * 0.13], fill=col)          # голова
    d.rectangle([x - h * 0.025, base - h * 0.88, x + h * 0.025, base - h * 0.83], fill=col)     # шея
    d.polygon([(x - hw, base - h * 0.8), (x + hw, base - h * 0.8), (x + hw * 0.75, base - h * 0.47),
               (x - hw * 0.75, base - h * 0.47)], fill=col)                                    # торс
    d.ellipse([x - hw - h*0.02, base - h * 0.84, x + hw + h*0.02, base - h * 0.74], fill=col)  # плечи
    d.polygon([(x - hw * 0.75, base - h * 0.48), (x - hw * 0.05, base - h * 0.48), (x - hw * 0.12, base), (x - hw * 0.6, base)], fill=col)
    d.polygon([(x + hw * 0.05, base - h * 0.48), (x + hw * 0.75, base - h * 0.48), (x + hw * 0.6, base), (x + hw * 0.12, base)], fill=col)
    for sgn in (-1, 1):                                                                      # руки
        d.polygon([(x + sgn * hw, base - h * 0.8), (x + sgn * (hw + h * 0.04), base - h * 0.78),
                   (x + sgn * (hw + h * 0.02), base - h * 0.45), (x + sgn * (hw - h * 0.03), base - h * 0.45)], fill=col)
    canvas.paste(lay, (0, 0), lay)


# масштаб: высота стены 2 м ≈ (mid-top) px у сгиба; люди ~1,75 м чуть впереди сгиба
mpx = (mid - top) / 2.0
for dx, hh in [(-115, 1.80), (115, 1.68)]:
    person(cx + dx, mid + depth * 0.62, hh * mpx * 1.08)
canvas.save(f'{out}_MOCKUP.jpg', quality=90)
print('ok')

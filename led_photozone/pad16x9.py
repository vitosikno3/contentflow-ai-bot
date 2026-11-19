"""Расширяет 3:2 развёртку до 16:9 (размытые края-поля), чтобы видеомодель не обрезала надписи.
После генерации видео центральную 3:2 часть вырезаем обратно: crop=ih*3/2:ih."""
import sys
from PIL import Image, ImageFilter
src, dst = sys.argv[1:3]
im = Image.open(src).convert('RGB')
h = 1080; w = int(round(h * 1.5)); im = im.resize((w, h), Image.LANCZOS)
W = 1920; pad = (W - w) // 2
out = im.resize((W, h)).filter(ImageFilter.GaussianBlur(40))  # фон-растяжка
# только размытый фон по краям (без зеркального текста, чтобы модель его не «оживляла»)
out.paste(im, (pad, 0))
out.save(dst)

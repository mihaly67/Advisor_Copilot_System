#!/usr/bin/env python3
"""
Z.ai Token Dashboard ikon generator.
Motivum: $ jel + token korongok + grafikon sávok.
Szin: Breeze Dark (zold/kek/sarga keverek).
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

ICON_DIR = "/data/mcp_server/state/icons"
SIZES = [16, 22, 32, 48, 64, 128, 256]

BG_DARK = (35, 38, 41)
BG_CARD = (45, 48, 51)
GREEN = (28, 220, 154)
BLUE = (29, 153, 243)
YELLOW = (253, 188, 75)
RED = (218, 68, 83)
WHITE = (239, 240, 241)
DIM = (189, 195, 199)
BORDER = (92, 96, 99)

def try_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def draw_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size

    # Háttér: lekerekített kártya
    margin = max(1, s // 16)
    d.rounded_rectangle(
        [margin, margin, s - margin, s - margin],
        radius=s // 6,
        fill=BG_DARK,
        outline=BORDER,
        width=max(1, s // 64),
    )

    # Grafikon sávok alul
    bar_area_top = int(s * 0.55)
    bar_area_bottom = int(s * 0.85)
    bar_area_left = int(s * 0.15)
    bar_area_right = int(s * 0.85)
    bar_w = (bar_area_right - bar_area_left) // 5
    bar_gap = bar_w // 4
    bar_actual_w = bar_w - bar_gap
    heights = [0.35, 0.55, 0.45, 0.75, 0.60]
    colors = [BLUE, BLUE, GREEN, YELLOW, GREEN]
    for i, (h, c) in enumerate(zip(heights, colors)):
        bh = int((bar_area_bottom - bar_area_top) * h)
        bx = bar_area_left + i * bar_w
        by = bar_area_bottom - bh
        d.rectangle([bx, by, bx + bar_actual_w, bar_area_bottom], fill=c)

    # $ jel középen felül
    font_size = int(s * 0.32)
    font = try_font(font_size)
    text = "$"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (s - tw) // 2 - bbox[0]
    ty = int(s * 0.12) - bbox[1]
    # $ jel köré korong
    coin_r = int(s * 0.22)
    cx, cy = s // 2, int(s * 0.28)
    d.ellipse([cx - coin_r, cy - coin_r, cx + coin_r, cy + coin_r],
              fill=BG_CARD, outline=GREEN, width=max(1, s // 80))
    d.text((tx, ty), text, font=font, fill=GREEN)

    # "Z.ai" felirat legfelül (kicsi)
    if size >= 48:
        small_font = try_font(max(8, int(s * 0.085)))
        label = "Z.ai"
        bbox2 = d.textbbox((0, 0), label, font=small_font)
        lw = bbox2[2] - bbox2[0]
        lx = (s - lw) // 2 - bbox2[0]
        ly = margin + max(1, s // 32)
        d.text((lx, ly), label, font=small_font, fill=DIM)

    return img

def main():
    os.makedirs(ICON_DIR, exist_ok=True)
    for sz in SIZES:
        img = draw_icon(sz)
        path = os.path.join(ICON_DIR, f"zai-token-{sz}.png")
        img.save(path)
        print(f"Generated: {path} ({sz}x{sz})")
    # 256-as a fő ikon
    img256 = draw_icon(256)
    img256.save(os.path.join(ICON_DIR, "zai-token-dashboard.png"))
    print(f"Generated: {ICON_DIR}/zai-token-dashboard.png (256x256)")

if __name__ == "__main__":
    main()
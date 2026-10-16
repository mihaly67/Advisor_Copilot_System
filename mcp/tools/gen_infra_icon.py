#!/usr/bin/env python3
"""
MCP Infrastruktura Dashboard ikon generator.
Kulonbozik a Z.ai token dashboard ikontol.
Motivum: szerver rack + GPU negyzetek + racs halo.
Szin: Breeze Dark sarku (kek/zold lila keverek).
"""
import os
from PIL import Image, ImageDraw, ImageFont

ICON_DIR = "/data/mcp_server/state/icons"
SIZES = [16, 22, 32, 48, 64, 128, 256]

# Breeze Dark szinek
BG_DARK = (35, 38, 41)        # #232629
BG_CARD = (45, 48, 51)        # #2d3033
BLUE = (29, 153, 243)          # #1d99f3
GREEN = (28, 220, 154)        # #1cdc9a
PURPLE = (155, 89, 182)       # #9b59b6
ORANGE = (246, 116, 0)        # #f67400
TEAL = (61, 174, 233)         # #3daee9
WHITE = (239, 240, 241)       # #eff0f1
DIM = (189, 195, 199)         # #bdc3c7
BORDER = (92, 96, 99)         # #5c6063


def try_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_infra_icon(size):
    """Infrastruktura ikon: szerver rack + GPU negyzetek + halo."""
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Hatter: lekeritett negyzet, sotet
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=max(2, s // 8),
                        fill=BG_DARK)

    margin = max(1, s // 10)
    inner = s - 2 * margin

    # === Szerver rack (3 sor, like server blades) ===
    n_rows = 3
    row_h = max(2, inner // (n_rows + 1))
    row_gap = max(1, row_h // 4)
    rack_x = margin + max(1, s // 20)
    rack_w = inner - max(2, s // 10)

    for i in range(n_rows):
        y = margin + i * (row_h + row_gap)
        # Szerver blade hatter
        d.rounded_rectangle(
            [rack_x, y, rack_x + rack_w - 1, y + row_h - 1],
            radius=max(1, row_h // 4),
            fill=BG_CARD,
            outline=BORDER,
            width=1,
        )
        # LED pottyok a rack sorokon
        led_r = max(1, row_h // 5)
        led_y = y + row_h // 2
        colors = [GREEN, ORANGE, BLUE]
        led_spacing = max(led_r * 2 + 1, s // 12)
        led_start_x = rack_x + max(1, s // 20)
        for j, c in enumerate(colors):
            cx = led_start_x + j * led_spacing
            if cx + led_r > rack_x + rack_w - led_r:
                break
            d.ellipse([cx - led_r, led_y - led_r, cx + led_r, led_y + led_r],
                      fill=c)

    # === GPU negyzetek (jobb also sarok, mini grid) ===
    gpu_size = max(2, s // 6)
    gx = s - margin - gpu_size * 2 - max(1, gpu_size // 3)
    gy = s - margin - gpu_size * 2 - max(1, gpu_size // 3)
    gpu_colors = [BLUE, GREEN]
    for row in range(2):
        for col in range(2):
            x0 = gx + col * (gpu_size + max(1, gpu_size // 3))
            y0 = gy + row * (gpu_size + max(1, gpu_size // 3))
            c = gpu_colors[(row + col) % 2]
            d.rounded_rectangle(
                [x0, y0, x0 + gpu_size - 1, y0 + gpu_size - 1],
                radius=max(1, gpu_size // 5),
                fill=c,
            )

    # === Halo vonalak (bal felso, halozati motívum) ===
    if size >= 32:
        net_x = margin + max(1, s // 20)
        net_y = margin + max(1, s // 20)
        net_r = max(2, s // 8)
        # 3 pont + vonalak
        pts = [
            (net_x, net_y),
            (net_x + net_r * 2, net_y + net_r),
            (net_x + net_r, net_y + net_r * 2),
        ]
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                d.line([pts[i], pts[j]], fill=TEAL, width=1)
        for p in pts:
            d.ellipse(
                [p[0] - max(1, net_r // 3), p[1] - max(1, net_r // 3),
                 p[0] + max(1, net_r // 3), p[1] + max(1, net_r // 3)],
                fill=PURPLE,
            )

    # === Felirat: "INFRA" (csak nagy meretnel) ===
    if size >= 64:
        font = try_font(max(8, s // 8))
        text = "INFRA"
        bbox = d.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (s - tw) // 2
        ty = s - margin - th - max(1, th // 4)
        # Hatter a szoveg mogott
        d.rounded_rectangle(
            [tx - 2, ty - 1, tx + tw + 2, ty + th + 1],
            radius=max(1, th // 4),
            fill=(0, 0, 0, 160),
        )
        d.text((tx, ty), text, font=font, fill=WHITE)

    return img


def main():
    os.makedirs(ICON_DIR, exist_ok=True)
    for size in SIZES:
        img = draw_infra_icon(size)
        path = os.path.join(ICON_DIR, "mcp-infra-%d.png" % size)
        img.save(path, "PNG")
        print("Mentve: " + path + " (%dx%d)" % (size, size))
    print("Kesz! %d ikon generalva." % len(SIZES))


if __name__ == "__main__":
    main()

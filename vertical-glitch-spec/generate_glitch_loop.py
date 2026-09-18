from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH, HEIGHT = 540, 960
FPS = 15
SECONDS = 7
FRAME_COUNT = FPS * SECONDS
HERE = Path(__file__).resolve().parent


def font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\impact.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


TITLE = font(72)
SMALL = font(24)


def centered_text_layer(text: str, y: int, jitter: int) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    box = draw.textbbox((0, 0), text, font=TITLE, stroke_width=2)
    x = (WIDTH - (box[2] - box[0])) // 2

    draw.text((x - 5 + jitter, y), text, font=TITLE, fill=(255, 28, 106, 210), stroke_width=2)
    draw.text((x + 5 - jitter, y), text, font=TITLE, fill=(0, 240, 255, 190), stroke_width=2)
    draw.text((x, y), text, font=TITLE, fill=(246, 244, 238, 255), stroke_width=1, stroke_fill=(10, 10, 15, 255))
    return layer


def make_frame(i: int) -> Image.Image:
    rng = random.Random(7731 + i)
    t = i / FPS
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]

    pulse = 0.5 + 0.5 * math.sin(t * math.tau * 0.75)
    vignette = np.sqrt(((xx - WIDTH / 2) / (WIDTH / 2)) ** 2 + ((yy - HEIGHT / 2) / (HEIGHT / 2)) ** 2)
    base = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
    base[:, :, 0] = 12 + 30 * pulse + 24 * np.maximum(0, 1 - vignette)
    base[:, :, 1] = 7 + 10 * np.maximum(0, 1 - vignette)
    base[:, :, 2] = 20 + 38 * (1 - pulse) + 30 * np.maximum(0, 1 - vignette)

    grain = np.random.default_rng(9000 + i).normal(0, 12, (HEIGHT, WIDTH, 1))
    base = np.clip(base + grain, 0, 255).astype(np.uint8)
    image = Image.fromarray(base, "RGB").convert("RGBA")

    figure = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    fd = ImageDraw.Draw(figure)
    sway = int(12 * math.sin(t * 2.1))
    cx = WIDTH // 2 + sway
    fd.ellipse((cx - 64, 212, cx + 64, 340), fill=(5, 5, 9, 238))
    fd.polygon(
        [(cx - 150, 420), (cx - 88, 320), (cx + 88, 320), (cx + 150, 420), (cx + 205, 890), (cx - 205, 890)],
        fill=(3, 3, 8, 245),
    )
    fd.arc((cx - 92, 250, cx + 92, 392), 205, 335, fill=(255, 40, 118, 145), width=4)
    image = Image.alpha_composite(image, figure.filter(ImageFilter.GaussianBlur(radius=2.4)))

    if t < 2.1:
        title, title_y = "NO SIGNAL", 470
    elif t < 4.7:
        title, title_y = "STAY // LOST", 455
    else:
        title, title_y = "REPLAY ME", 470

    image = Image.alpha_composite(image, centered_text_layer(title, title_y, rng.randint(-3, 3)))
    draw = ImageDraw.Draw(image)
    draw.text((28, 28), "UNDERGROUND VISUAL STUDY  //  001", font=SMALL, fill=(235, 235, 235, 205))
    draw.text((28, HEIGHT - 58), f"00:0{int(t)}:{int((t % 1) * 100):02d}   CRT / RAW / LOOP", font=SMALL, fill=(0, 230, 255, 190))

    for y in range(0, HEIGHT, 4):
        draw.line((0, y, WIDTH, y), fill=(0, 0, 0, 48), width=1)

    for _ in range(5):
        y = rng.randrange(70, HEIGHT - 70)
        h = rng.randrange(4, 22)
        shift = rng.randrange(-24, 25)
        band = image.crop((0, y, WIDTH, min(HEIGHT, y + h)))
        image.alpha_composite(band, (shift, y))

    if i % 11 in (0, 1):
        flash = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 22 if i % 11 == 0 else 10))
        image = Image.alpha_composite(image, flash)

    return image.convert("RGB")


def main() -> None:
    frames = [make_frame(i) for i in range(FRAME_COUNT)]
    frames[0].save(HERE / "emo-trap-loop-preview.png", optimize=True)
    frames[0].save(
        HERE / "emo-trap-7s-loop.webp",
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / FPS),
        loop=0,
        quality=72,
        method=4,
    )


if __name__ == "__main__":
    main()

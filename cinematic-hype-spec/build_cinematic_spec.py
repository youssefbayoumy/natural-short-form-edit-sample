from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy.editor import CompositeVideoClip, ImageClip, VideoFileClip


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
OUTPUT = OUT_DIR / "cinematic-hype-spec.mp4"
PREVIEW = OUT_DIR / "cinematic-hype-preview.jpg"
FONT = r"C:\Windows\Fonts\bahnschrift.ttf"

W, H = 720, 1280
FPS = 24
SR = 44100


def grade(frame: np.ndarray, *, warm: float, contrast: float = 1.12) -> np.ndarray:
    arr = frame.astype(np.float32) / 255.0
    arr = (arr - 0.5) * contrast + 0.5
    arr[..., 0] *= 1.0 + warm
    arr[..., 2] *= 1.0 - warm * 0.65
    # Cinematic highlight roll-off with slightly lifted shadows.
    arr = np.clip(arr, 0.0, 1.0)
    arr = np.power(arr, 0.94)
    return (arr * 255.0).astype(np.uint8)


def source_clip(filename: str, start: float, duration: float, warm: float, drift: int) -> VideoFileClip:
    clip = VideoFileClip(str(ROOT / "outputs" / filename), audio=False).subclip(start, start + duration)
    # The free stock previews are 9:16. Overscan slightly so a slow vertical drift
    # can add camera movement without exposing an edge.
    clip = clip.resize(height=H + 80)
    clip = clip.fl_image(lambda frame: grade(frame, warm=warm))
    return clip.set_position(lambda t: ("center", -40 + drift * (t / max(duration, 0.01))))


def vignette() -> ImageClip:
    yy, xx = np.ogrid[:H, :W]
    nx = (xx - W / 2) / (W / 2)
    ny = (yy - H / 2) / (H / 2)
    radius = np.sqrt(nx * nx + ny * ny)
    alpha = np.clip((radius - 0.32) / 0.75, 0.0, 1.0) * 145
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 3] = alpha.astype(np.uint8)
    return ImageClip(rgba, transparent=True)


def text_card(
    text: str,
    start: float,
    duration: float,
    y: int,
    size: int,
    *,
    accent: bool = False,
    subtitle: str | None = None,
) -> ImageClip:
    canvas = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT, size=size)
    fill = (241, 203, 119, 255) if accent else (248, 248, 246, 255)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw.text((x + 3, 25 + 3), text, font=font, fill=(0, 0, 0, 160))
    draw.text((x, 25), text, font=font, fill=fill)
    if subtitle:
        small = ImageFont.truetype(FONT, size=22)
        sb = draw.textbbox((0, 0), subtitle, font=small)
        sx = (W - (sb[2] - sb[0])) // 2
        draw.text((sx, 115), subtitle, font=small, fill=(235, 235, 232, 230))
    arr = np.asarray(canvas)
    return (
        ImageClip(arr, transparent=True)
        .set_start(start)
        .set_duration(duration)
        .set_position(lambda t: ("center", y + int(14 * (1 - min(t / 0.45, 1.0)))))
        .crossfadein(0.32)
        .crossfadeout(0.28)
    )


def original_audio(duration: float) -> AudioArrayClip:
    n = int(duration * SR)
    t = np.arange(n, dtype=np.float64) / SR
    # A restrained original ambient bed: sub, fifth, shimmer, and gentle pulse.
    attack = np.clip(t / 1.2, 0.0, 1.0)
    release = np.clip((duration - t) / 1.0, 0.0, 1.0)
    env = attack * release
    pad = (
        0.18 * np.sin(2 * np.pi * 55.0 * t)
        + 0.09 * np.sin(2 * np.pi * 82.41 * t + 0.7)
        + 0.035 * np.sin(2 * np.pi * 220.0 * t + 1.3)
    ) * env

    audio = pad
    rng = np.random.default_rng(917)
    for cut in (2.45, 4.85, 7.2, 9.55, 11.8):
        dt = t - cut
        hit = np.where(dt >= 0, np.exp(-dt * 8.0) * np.sin(2 * np.pi * 46.0 * dt), 0.0)
        audio += 0.24 * hit
        whoosh_env = np.where(np.abs(dt) < 0.26, 1.0 - np.abs(dt) / 0.26, 0.0)
        audio += 0.035 * rng.standard_normal(n) * whoosh_env

    peak = max(float(np.max(np.abs(audio))), 1e-6)
    audio = (0.78 * audio / peak).astype(np.float32)
    stereo = np.column_stack([audio, audio])
    return AudioArrayClip(stereo, fps=SR)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    segments = [
        ("mixkit-26100.mp4", 0.6, 2.8, -0.04, 22),
        ("mixkit-4949.mp4", 1.2, 2.7, 0.055, -18),
        ("mixkit-49939.mp4", 0.4, 2.6, 0.025, 20),
        ("mixkit-51373.mp4", 1.1, 2.7, 0.075, -20),
        ("mixkit-12132.mp4", 1.0, 2.9, 0.035, 18),
        ("mixkit-26100.mp4", 4.0, 2.6, -0.055, -16),
    ]
    starts = [0.0, 2.35, 4.65, 6.85, 9.15, 11.45]
    layers = []
    opened = []
    for (filename, trim, dur, warm, drift), at in zip(segments, starts):
        clip = source_clip(filename, trim, dur, warm, drift)
        opened.append(clip)
        layers.append(clip.set_start(at).crossfadein(0.28).crossfadeout(0.24))

    duration = 14.0
    layers.append(vignette().set_duration(duration))

    # Thin gold rules make the typography feel like a deliberate promo system.
    rule = np.zeros((3, 250, 4), dtype=np.uint8)
    rule[..., :3] = (241, 203, 119)
    rule[..., 3] = 230
    layers.append(ImageClip(rule, transparent=True).set_start(0.55).set_duration(1.75).set_position(("center", 875)).crossfadein(0.25).crossfadeout(0.25))

    layers.extend(
        [
            text_card("SOME NIGHTS", 0.45, 1.9, 760, 54),
            text_card("ASK FOR STILLNESS.", 2.55, 1.9, 760, 48, accent=True),
            text_card("OTHERS", 4.95, 1.55, 770, 58),
            text_card("ASK FOR EVERYTHING.", 7.15, 1.95, 760, 46, accent=True),
            text_card("MAKE IT FEEL", 9.45, 1.85, 770, 52),
            text_card(
                "UNFORGETTABLE.",
                11.65,
                2.15,
                735,
                56,
                accent=True,
                subtitle="CINEMATIC SPEC EDIT • YOUSSEF BAYOUMY",
            ),
        ]
    )

    final = CompositeVideoClip(layers, size=(W, H), bg_color=(4, 6, 8)).set_duration(duration)
    final = final.set_audio(original_audio(duration))
    final.write_videofile(
        str(OUTPUT),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="4500k",
        audio_bitrate="192k",
        preset="medium",
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        threads=4,
        logger="bar",
    )

    frames = []
    for at in (0.9, 3.0, 5.3, 7.6, 9.9, 12.3):
        frame = final.get_frame(at)
        image = Image.fromarray(frame).resize((180, 320), Image.Resampling.LANCZOS)
        frames.append(image)
    sheet = Image.new("RGB", (180 * len(frames), 320), "black")
    for i, frame in enumerate(frames):
        sheet.paste(frame, (i * 180, 0))
    sheet.save(PREVIEW, quality=93)

    final.close()
    for clip in opened:
        clip.close()


if __name__ == "__main__":
    main()

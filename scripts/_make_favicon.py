"""Generate public/favicon.ico (multi-size) from the Orthodox-cross design.

Runs as a one-shot. Produces a 16/32/48px multi-resolution .ico containing
the same eight-pointed Orthodox cross as favicon.svg, in burgundy on a
transparent background.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "favicon.ico"

# Match the Header brand-mark color exactly (var(--color-gold) #b08d57).
GOLD = (176, 141, 87, 255)
SIZES = (16, 32, 48, 64)


def render(size: int) -> Image.Image:
    """Draw the cross at the given pixel size into a transparent canvas."""
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    drw = ImageDraw.Draw(img)

    # Coordinate scale relative to a 32px reference.
    k = s / 32.0

    def rect(x, y, w, h):
        drw.rectangle([x * k, y * k, (x + w) * k, (y + h) * k], fill=GOLD)

    # Vertical post
    rect(14.6, 2.5, 2.8, 27)
    # Top crossbar (titulus)
    rect(11.2, 6.5, 9.6, 1.8)
    # Main crossbar
    rect(7.6, 11, 16.8, 2.6)
    # Slanted footrest — approximate as flat at small sizes (rotation
    # is invisible at 16/32px)
    rect(10.0, 20.6, 12.0, 1.8)

    return img


def main() -> None:
    images = [render(s) for s in SIZES]
    # Pillow accepts multi-size .ico via save with sizes= kwarg
    images[0].save(OUT, format="ICO", sizes=[(s, s) for s in SIZES],
                   append_images=images[1:])
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, sizes={SIZES})")


if __name__ == "__main__":
    main()

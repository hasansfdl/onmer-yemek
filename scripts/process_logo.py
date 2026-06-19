"""One-off helper: turn the supplied logo into transparent variants.

Run with `python scripts/process_logo.py`.
"""

from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'static' / 'images' / 'onmer-logo.png'
OUT_DIR = ROOT / 'static' / 'images'


def whiten_to_alpha(img: Image.Image, threshold: int = 235) -> Image.Image:
    """Convert near-white pixels of a logo to transparent."""
    img = img.convert('RGBA')
    r, g, b, a = img.split()

    # Pixel is "white" when each channel ≥ threshold. Multiply the masks so the
    # result is 255 only when all three channels qualify.
    near_white = ImageChops.multiply(
        ImageChops.multiply(
            r.point(lambda v: 255 if v >= threshold else 0),
            g.point(lambda v: 255 if v >= threshold else 0),
        ),
        b.point(lambda v: 255 if v >= threshold else 0),
    )
    # Where near_white==255, alpha=0; otherwise alpha=original (full).
    alpha_mask = near_white.point(lambda v: 0 if v == 255 else 255)
    return Image.merge('RGBA', (r, g, b, alpha_mask))


def autocrop_to_content(img: Image.Image, padding: int = 12) -> Image.Image:
    """Trim transparent borders, then re-pad with a small even margin."""
    bbox = img.getbbox()
    if not bbox:
        return img
    cropped = img.crop(bbox)
    side = max(cropped.size) + padding * 2
    canvas = Image.new('RGBA', (side, side), (255, 255, 255, 0))
    canvas.paste(
        cropped,
        ((side - cropped.size[0]) // 2, (side - cropped.size[1]) // 2),
        cropped,
    )
    return canvas


def main() -> None:
    src = Image.open(SRC)
    transparent = whiten_to_alpha(src)
    transparent.save(OUT_DIR / 'onmer-logo-transparent.png')

    # The chef-hat lives in the upper-left quadrant of the source; the "ONMER"
    # wordmark starts roughly below y=620. Crop just above the wordmark so the
    # hat is the only visible element, then let autocrop trim the rest.
    hat_region = transparent.crop((40, 180, 660, 595))
    mark = autocrop_to_content(hat_region, padding=24)
    mark.save(OUT_DIR / 'onmer-mark.png')

    # Resize variants (favicon, apple-touch, PWA icon).
    for size, name in [
        (32, 'favicon-32.png'),
        (180, 'apple-touch-icon.png'),
        (192, 'onmer-logo-192.png'),
    ]:
        mark.resize((size, size), Image.LANCZOS).save(OUT_DIR / name)

    print('Logo variants written to', OUT_DIR)
    print(f'  onmer-mark.png size = {mark.size}')


if __name__ == '__main__':
    main()

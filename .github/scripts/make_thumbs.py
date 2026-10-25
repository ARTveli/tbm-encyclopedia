"""
make_thumbs.py — зменшені копії обкладинок для Полиці, «Альбому дня», хронології
та сторінки Liner Notes: covers/thumbs/<назва>.webp, 400×400, ~30 КБ.

Оригінали в covers/ не змінюються (їх показують сторінки альбомів і прев'ю).
Запускати після додавання нових обкладинок; робить лише відсутні/застарілі.
Потрібен Pillow:  python3 -m pip install pillow

    python3 make_thumbs.py --vault ~/TBM/TBM_Vault
"""
import argparse
from pathlib import Path

from PIL import Image

SIZE = 400


def thumb_path(v: Path, cover: str) -> Path:
    return v / "covers" / "thumbs" / (Path(cover).stem + ".webp")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    v = ap.parse_args().vault.expanduser()
    src = v / "covers"
    out = src / "thumbs"
    out.mkdir(exist_ok=True)
    made = skipped = 0
    before = after = 0
    for f in sorted(src.iterdir()):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp") or not f.is_file():
            continue
        t = out / (f.stem + ".webp")
        before += f.stat().st_size
        if t.exists() and t.stat().st_mtime >= f.stat().st_mtime:
            skipped += 1
            after += t.stat().st_size
            continue
        im = Image.open(f).convert("RGB")
        im.thumbnail((SIZE, SIZE), Image.LANCZOS)
        im.save(t, "WEBP", quality=80, method=6)
        after += t.stat().st_size
        made += 1
    print(f"✓ мініатюр створено: {made}, без змін: {skipped} · {before // 1048576} МБ → {after // 1024} КБ")


if __name__ == "__main__":
    main()

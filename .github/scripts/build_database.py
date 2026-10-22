"""
build_database.py — збирає data.json для інтерактивної сторінки /explore/
з усіх .md файлів vault (Альбоми, Артисти, Liner_Notes).

Запускається автоматично в GitHub Actions при кожному push.
Локально:
    python3 build_database.py --vault ~/TBM/TBM_Vault --out /tmp/data.json
"""

import argparse
import json
import re
from pathlib import Path


def parse_frontmatter(text: str):
    """Мінімальний YAML-парсер для нашого формату (key: value, списки '- item')."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    data, key = {}, None
    for line in block.split("\n"):
        if not line.strip():
            continue
        m_item = re.match(r"^\s*-\s+(.*)$", line)
        if m_item and key:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(_clean(m_item.group(1)))
            continue
        m_kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m_kv:
            key, val = m_kv.group(1), m_kv.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                data[key] = [_clean(v) for v in val[1:-1].split(",") if v.strip()]
            else:
                data[key] = _clean(val) if val else None
    return data, body


def _clean(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    if v in ("null", "~", ""):
        return None
    return v


def slugify(path_no_ext: str) -> str:
    """Та сама логіка, що й у Quartz v4 (sluggify)."""
    parts = []
    for seg in path_no_ext.split("/"):
        seg = re.sub(r"\s", "-", seg)
        seg = seg.replace("&", "-and-").replace("%", "-percent").replace("?", "").replace("#", "")
        parts.append(seg)
    return "/".join(parts)


WIKILINK = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]|\[\[([^\]]+)\]\]")


def strip_md(s: str) -> str:
    s = WIKILINK.sub(lambda m: m.group(2) or m.group(3), s)
    s = re.sub(r"!\[\[[^\]]*\]\]", "", s)
    s = re.sub(r"[*_`>#]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def section(body: str, title: str) -> str:
    m = re.search(rf"^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def to_int(v):
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    v = args.vault

    # ── Артисти ──
    artists = {}
    for f in sorted((v / "Артисти").glob("*.md")):
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        name = fm.get("name") or f.stem.replace("Артист — ", "")
        artists[name] = {
            "instr": fm.get("instruments") or "",
            "url": slugify(f"Артисти/{f.stem}"),
        }

    # ── Liner notes ──
    liners = {}
    ln_dir = v / "Liner_Notes"
    if ln_dir.exists():
        for f in sorted(ln_dir.glob("*.md")):
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            if fm.get("type") != "liner_notes" or not fm.get("catalog"):
                continue
            liners.setdefault(fm["catalog"], []).append({
                "author": fm.get("original_author") or "",
                "translator": fm.get("translator") or "",
                "url": slugify(f"Liner_Notes/{f.stem}"),
            })

    # ── Альбоми ──
    albums = []
    for f in sorted((v / "Альбоми").glob("*.md")):
        fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        if fm.get("type") != "album":
            continue
        cat = fm.get("catalog") or f.stem
        cover = fm.get("cover")
        if cover and not (v / cover).exists():
            cover = None
        review = strip_md(section(body, "Рецензія"))
        personnel = [p for p in (fm.get("personnel") or []) if p]
        albums.append({
            "id": f.stem,
            "cat": cat,
            "title": fm.get("title") or "",
            "title_ua": fm.get("title_ua") or "",
            "artist": fm.get("artist") or "",
            "artist_en": fm.get("artist_en") or "",
            "year": to_int(fm.get("year")),
            "engineer": fm.get("sound_engineer") or "",
            "awards": fm.get("awards") or "",
            "personnel": personnel,
            "cover": cover,
            "review": review[:600] + ("…" if len(review) > 600 else ""),
            "liner": liners.get(cat, []),
            "url": slugify(f"Альбоми/{f.stem}"),
        })

    albums.sort(key=lambda a: (a["year"] or 9999, a["cat"]))

    # лишаємо тільки артистів, що фігурують у складах
    used = {p for a in albums for p in a["personnel"]}
    artists = {k: val for k, val in artists.items() if k in used}

    data = {"albums": albums, "artists": artists}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"✓ data.json: {len(albums)} альбомів, {len(artists)} артистів, "
          f"{sum(len(x) for x in liners.values())} liner notes, "
          f"{sum(1 for a in albums if a['cover'])} обкладинок → {args.out}")


if __name__ == "__main__":
    main()

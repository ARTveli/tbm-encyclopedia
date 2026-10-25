"""
build_home.py — генерує верхню частину index.md (герой, статистика, стрічка
обкладинок, картки розділів) у стилі «TBM Полиця».

Таблиці нагород / інтерв'ю / нарисів нижче не чіпаються.
Блок обмежений маркерами <!-- tbm-home:start --> … <!-- tbm-home:end -->,
тому скрипт можна запускати повторно (оновить цифри й обкладинки).

Запуск:
    python3 build_home.py --vault ~/TBM/TBM_Vault --dry-run
    python3 build_home.py --vault ~/TBM/TBM_Vault
"""

import argparse
import html
import re
import shutil
from datetime import datetime
from pathlib import Path

SITE = "https://artveli.github.io/tbm-encyclopedia"
START, END = "<!-- tbm-home:start -->", "<!-- tbm-home:end -->"


def fm(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    out = {}
    for line in text[3:end].split("\n"):
        m = re.match(r"^([A-Za-z_]\w*):\s*(.*)$", line)
        if m:
            v = m.group(2).strip().strip("\"'")
            out[m.group(1)] = v or None
    return out


def collect(vault: Path):
    albums = []
    for f in sorted((vault / "Альбоми").glob("*.md")):
        d = fm(f.read_text(encoding="utf-8"))
        if d.get("type") != "album":
            continue
        try:
            year = int(str(d.get("year"))[:4])
        except (TypeError, ValueError):
            year = None
        cover = d.get("cover")
        albums.append({
            "stem": f.stem, "cat": d.get("catalog") or f.stem, "title": d.get("title") or "",
            "artist": d.get("artist") or "", "year": year, "awards": d.get("awards"),
            "cover": cover if cover and (vault / cover).exists() else None,
            "thumb": (f"covers/thumbs/{Path(cover).stem}.webp"
                      if cover and (vault / "covers" / "thumbs" / f"{Path(cover).stem}.webp").exists() else None),
        })
    count = lambda folder: len([f for f in (vault / folder).glob("*.md") if f.name != "index.md"]) if (vault / folder).exists() else 0
    stats = {
        "albums": len(albums),
        "artists": count("Артисти"),
        "liner": len([f for f in (vault / "Liner_Notes").glob("*.md") if f.name != "index.md"]) if (vault / "Liner_Notes").exists() else 0,
        "interviews": count("Інтервʼю"),
        "topics": count("Topics"),
    }
    years = [a["year"] for a in albums if a["year"] and a["year"] >= 1970]
    stats["span"] = f"{min(years)}–{max(years)}" if years else ""
    return albums, stats


def build_block(albums, stats) -> str:
    e = html.escape
    sections = [
        (f"{SITE}/explore/", "Полиця альбомів", "Обкладинки, пошук і фільтри"),
        ("Каталог", "Каталог релізів", "Повний хронологічний список"),
        (f"{SITE}/explore/#time", "Хронологія лейблу", "Інтерактивна шкала 1963–2014"),
        (f"{SITE}/explore/#graph", "Граф музикантів", f'{stats["artists"]} музикантів і їхні зв\'язки'),
        ("Інтервʼю/", "Інтерв'ю", f'{stats["interviews"]} розмови'),
        ("Topics/", "Тематичні нариси", f'{stats["topics"]} нарисів'),
        ("Передмова", "Передмова", "Про книгу та переклад"),
        (f"{SITE}/Liner_Notes/", "Liner Notes", f'{stats["liner"]} текстів з конвертів'),
    ]

    def card(i, href, title, sub):
        ext = " data-router-ignore" if href.startswith("http") else ""
        return f'<a href="{e(href)}"{ext}><span>{i:02d}</span><b>{e(title)}</b><small>{e(sub)}</small></a>'

    cards = "\n".join(card(i, *s) for i, s in enumerate(sections, 1))

    def stat(n, label):
        return f"<div><b>{n}</b><span>{e(label)}</span></div>"

    return f"""{START}
<div class="tbm-hero">
<div class="tbm-hero-text">
<p class="tbm-kicker"><img class="tbm-logo" src="static/icon.png" alt="">Three Blind Mice · Tokyo · {e(stats["span"])}</p>
<h1 class="tbm-title">TBM Енциклопедія</h1>
<p class="tbm-lead">Інтерактивний український переклад книги <em>Three Blind Mice — The Complete Disc Guide</em>: альбоми, музиканти, liner notes та історія токійського джаз-лейблу.</p>
</div>
</div>
<div class="tbm-stats">
{stat(stats["albums"], "альбомів")}
{stat(stats["artists"], "музикантів")}
{stat(stats["liner"], "liner notes")}
{stat(stats["interviews"] + stats["topics"], "статей та інтерв'ю")}
</div>
<div class="tbm-daily" id="tbm-daily"></div>

## Розділи

<div class="tbm-sections">
{cards}
</div>
{END}
"""


# ── Сторінка Liner Notes ──
LN_START, LN_END = "<!-- tbm-liner:start -->", "<!-- tbm-liner:end -->"


def slugify(path: str) -> str:
    """Як у Quartz v4."""
    out = []
    for seg in path.split("/"):
        seg = re.sub(r"\s", "-", seg)
        seg = seg.replace("&", "-and-").replace("%", "-percent").replace("?", "").replace("#", "")
        out.append(seg)
    return "/".join(out)


def excerpt(body: str, n: int = 220) -> str:
    for line in body.split("\n"):
        t = line.strip()
        if not t or t.startswith(("#", "!", ">", "|", "---", "<", "-", "*")):
            continue
        t = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", t)
        t = re.sub(r"[*_`]", "", t)
        if len(t) < 40:
            continue
        return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"
    return ""


def build_liner_page(vault: Path, albums) -> tuple[Path, int] | None:
    d = vault / "Liner_Notes"
    if not d.is_dir():
        return None
    by_cat = {a["cat"]: a for a in albums}
    items = []
    for f in sorted(d.glob("*.md")):
        if f.name == "index.md":
            continue
        text = f.read_text(encoding="utf-8")
        meta = fm(text)
        if meta.get("type") != "liner_notes":
            continue
        m = re.match(r"^---\n.*?\n---\n", text, re.S)
        body = text[m.end():] if m else text
        a = by_cat.get(meta.get("catalog") or "", {})
        items.append({
            "url": f"{SITE}/{slugify('Liner_Notes/' + f.stem)}",
            "cat": meta.get("catalog") or f.stem, "year": a.get("year"),
            "title": a.get("title") or meta.get("title") or f.stem,
            "artist": a.get("artist") or "", "cover": a.get("thumb") or a.get("cover"),
            "author": meta.get("original_author") or "", "tr": meta.get("translator") or "",
            "ex": excerpt(body),
        })
    items.sort(key=lambda x: (x["year"] or 9999, x["cat"]))
    e = html.escape

    def row(x):
        img = (f'<img loading="lazy" src="{SITE}/{e(x["cover"])}" alt="">' if x["cover"]
               else f'<i>{e(x["cat"])}</i>')
        by = " · ".join(p for p in (
            f'Автор: {e(x["author"])}' if x["author"] else "",
            f'Переклад: {e(x["tr"])}' if x["tr"] else "") if p)
        return (f'<a class="tbm-ln" href="{e(x["url"])}" data-router-ignore>'
                f'<span class="tbm-ln-cover">{img}</span>'
                f'<span class="tbm-ln-body">'
                f'<span class="tbm-ln-k">{e(x["cat"])}{" · " + str(x["year"]) if x["year"] else ""}</span>'
                f'<b>{e(x["title"])}</b>'
                f'<span class="tbm-ln-a">{e(x["artist"])}</span>'
                + (f'<span class="tbm-ln-ex">{e(x["ex"])}</span>' if x["ex"] else "")
                + (f'<span class="tbm-ln-by">{by}</span>' if by else "")
                + '</span></a>')

    block = (f"{LN_START}\n"
             f'<p class="tbm-ln-lead">Оригінальні тексти з конвертів платівок TBM — історії записів, '
             f'слова продюсерів, критиків і самих музикантів. Упорядковано за роком запису.</p>\n'
             f'<div class="tbm-ln-list">\n' + "\n".join(row(x) for x in items) + "\n</div>\n"
             f"{LN_END}\n")
    page = d / "index.md"
    old = page.read_text(encoding="utf-8") if page.exists() else ""
    if LN_START in old and LN_END in old:
        new = old.split(LN_START)[0] + block + old.split(LN_END, 1)[1].lstrip("\n")
    else:
        if old:
            shutil.copy2(page, page.with_name("index.md.backup-liner"))
        new = "---\ntitle: Liner Notes\ntype: index\n---\n\n" + block
    page.write_text(new, encoding="utf-8")
    return page, len(items)


def split_index(text: str):
    """Повертає (frontmatter, tail) — tail = все, що йде після нашого блоку / старої шапки."""
    m = re.match(r"^---\n.*?\n---\n", text, re.S)
    front = m.group(0) if m else ""
    body = text[len(front):]
    if START in body and END in body:
        return front, body.split(END, 1)[1].lstrip("\n")
    # перший запуск: відрізаємо стару шапку до таблиць
    idx = body.find("### Альбоми з нагородами")
    if idx < 0:
        idx = body.find("## Швидкі запити")
    if idx < 0:
        raise SystemExit("✗ Не знайшов «### Альбоми з нагородами» у index.md — перевір файл")
    tail = body[idx:]
    tail = re.sub(r"^## Швидкі запити\s*\n", "", tail, flags=re.M)
    tail = re.sub(r"^### ", "## ", tail, flags=re.M)
    return front, tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    index = a.vault / "index.md"
    text = index.read_text(encoding="utf-8")
    front, tail = split_index(text)
    albums, stats = collect(a.vault)
    new = front + "\n" + build_block(albums, stats) + "\n" + tail

    print(f"Альбомів: {stats['albums']} · музикантів: {stats['artists']} · liner notes: {stats['liner']} · "
          f"обкладинок: {sum(1 for x in albums if x['cover'])}")
    if a.dry_run:
        print("[DRY-RUN] Liner_Notes/index.md не записано")
        print("\n[DRY-RUN] Перші 25 рядків нового index.md:\n")
        print("\n".join(new.split("\n")[:25]))
        return
    first = index.with_name("index.md.backup-design")      # оригінал до першого запуску
    if not first.exists():
        shutil.copy2(index, first)
    backup = index.with_name(f"index.md.backup-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(index, backup)
    index.write_text(new, encoding="utf-8")
    print(f"✓ index.md оновлено · бекап: {backup.name}")
    r = build_liner_page(a.vault, albums)
    if r:
        print(f"✓ {r[0].relative_to(a.vault)} · {r[1]} liner notes")


if __name__ == "__main__":
    main()

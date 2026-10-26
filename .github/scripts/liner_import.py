"""
liner_import.py — нові liner notes з _originals/ і посилання на них зі сторінок альбомів.

1. Для кожного файлу в _originals/, у назві якого є каталожний номер (…(TBM-39).md)
   і для якого ще немає Liner_Notes/<каталог>_liner.md, створює оброблений файл:
     • frontmatter: type, title «<Альбом>: liner notes», catalog, album_title,
       album_artist, original_author, translator, year, tags
     • автор — з першого заголовка «# Рецензія <Автор>» / «# Огляд <Автор>»,
       або з рядка «Текст: …», «Автор: …»
     • перекладач — з рядка «*Переклад: …*» (за замовчуванням «Юко М. Дарвен»)
     • посилання на артистів [[Артист — …]] і каталожні номери [[TBM-…]] у тексті
2. На сторінці кожного альбому з liner notes перебудовує розділ
   «## Liner Notes (переклади)» зі статичним списком посилань
   (якщо розділу немає — додає перед «## Рецензія»).

Готові файли в Liner_Notes/ не перезаписує. Можна запускати повторно.
    python3 liner_import.py --vault ~/TBM/TBM_Vault --dry-run
    python3 liner_import.py --vault ~/TBM/TBM_Vault
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_database import _catkey, parse_frontmatter  # noqa: E402

CATALOG_RE = re.compile(r"(TBM(?:\(P\))?-(?:CD-|XR-|P-)?\d+(?:[-/]\d+)?|PAP-\d+|NKCD-\d+|XRCD24-[A-Z]+\d+)")
DEFAULT_TRANSLATOR = "Юко М. Дарвен"
SECTION = "## Liner Notes (переклади)"
SECTION_RE = re.compile(r"\n*## Liner Notes \(переклади\).*?(?=\n## |\n---|\Z)", re.S)


def safe(s):
    return re.sub(r"[\\/:*?\"<>|]", "-", s)


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def load_albums(v):
    out = {}
    for f in (v / "Альбоми").glob("*.md"):
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        if fm.get("type") == "album" and fm.get("catalog"):
            out[_catkey(fm["catalog"])] = {"file": f, "cat": fm["catalog"], "title": fm.get("title") or "",
                                           "artist": fm.get("artist") or "", "year": fm.get("year")}
    return out


def name_lookup(v):
    look = {}
    for f in (v / "Артисти").glob("*.md"):
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        n = fm.get("name") or f.stem.replace("Артист — ", "")
        look[n] = f.stem.replace("Артист — ", "")
        p = n.split()
        if len(p) == 2:
            look[f"{p[1]} {p[0]}"] = look[n]
    return look


def autolink(text, names, cats):
    out = []
    for line in text.split("\n"):
        if line.lstrip().startswith("|") or line.startswith("#"):
            out.append(line)
            continue
        for variant in sorted(names, key=len, reverse=True):
            if len(variant) >= 4 and variant in line:
                line = re.sub(rf"(?<![\w\[\]|]){re.escape(variant)}(?![\w\]|])",
                              f"[[Артист — {names[variant]}|{variant}]]", line)
        for cat in sorted(cats, key=len, reverse=True):
            if cat in line:
                line = re.sub(rf"(?<![\w\-\[\]/|]){re.escape(cat)}(?![\w\-\]/|])", f"[[{cat}]]", line)
        out.append(line)
    return "\n".join(out)


def parse_original(text):
    body = text
    if body.startswith("---\n"):
        end = body.find("\n---\n", 4)
        if end > 0:
            body = body[end + 5:]
    author = None
    for line in body.split("\n"):
        if line.startswith("# "):
            m = re.match(r"^#\s+(?:Рецензія|Огляд|Стаття|Liner Notes)\s+(.+)$", line.strip())
            if m:
                author = m.group(1).strip()
            break
    if not author:
        m = re.search(r"(?:Текст|Автор(?: тексту)?)[^:\n]*:\**\s*([^\n*(]+)", body)
        if m:
            author = m.group(1).strip(" *")
    tr = None
    m = re.search(r"\*Переклад[:\s]+([^*\n]+?)\*", body)
    if m:
        tr = m.group(1).strip()
    if not tr or "DARWEN" in tr.upper():
        tr = DEFAULT_TRANSLATOR
    return body, author, tr


def import_new(v, albums, dry):
    orig = v / "_originals"
    if not orig.is_dir():
        return []
    have = set()
    for f in (v / "Liner_Notes").glob("*.md"):
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        if fm.get("type") == "liner_notes" and fm.get("catalog"):
            have.add(_catkey(fm["catalog"]))
    names = name_lookup(v)
    cats = [a["cat"] for a in albums.values()]
    made = []
    for f in sorted(orig.glob("*.md")):
        m = CATALOG_RE.search(f.stem)
        if not m:
            print(f"  ⚠ без каталожного номера в назві, пропущено: {f.name}")
            continue
        key = _catkey(m.group(1))
        if key in have:
            continue
        a = albums.get(key)
        if not a:
            print(f"  ⚠ {m.group(1)}: альбому з таким номером немає в Альбоми/, пропущено: {f.name}")
            continue
        body, author, tr = parse_original(f.read_text(encoding="utf-8"))
        fm = ["type: liner_notes", f"title: {q(a['title'] + ': liner notes')}", f"catalog: {a['cat']}",
              f"album_title: {q(a['title'])}", f"album_artist: {q(a['artist'])}"]
        if author:
            fm.append(f"original_author: {q(author)}")
        fm.append(f"translator: {q(tr)}")
        if a["year"]:
            fm.append(f"year: {a['year']}")
        fm += ["tags:", "  - liner_notes", "  - tbm", f"  - catalog/{a['cat']}"]
        if author:
            tag = re.sub(r"[^\w-]+", "_", author).strip("_")
            fm.append(f"  - by/{tag}")
        out = v / "Liner_Notes" / f"{safe(a['cat'])}_liner.md"
        text = "---\n" + "\n".join(fm) + "\n---\n\n" + autolink(body.strip("\n"), names, cats) + "\n"
        made.append((out, a["cat"], author))
        have.add(key)
        if not dry:
            out.write_text(text, encoding="utf-8")
    return made


def link_albums(v, albums, dry):
    grouped = {}
    for f in sorted((v / "Liner_Notes").glob("*.md")):
        if f.name == "index.md":
            continue
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        if fm.get("type") != "liner_notes" or not fm.get("catalog"):
            continue
        grouped.setdefault(_catkey(fm["catalog"]), []).append(
            (f.stem, fm.get("original_author") or "", fm.get("translator") or "", fm.get("year") or ""))
    changed = []
    for key, items in grouped.items():
        a = albums.get(key)
        if not a:
            continue
        lines = [SECTION, ""]
        for stem, au, tr, yr in items:
            desc = " ".join(x for x in (au or "Liner notes", f"({yr})" if yr else "") if x)
            lines.append(f"- [[Liner_Notes/{stem}|{desc}{' — пер. ' + tr if tr else ''}]]")
        block = "\n".join(lines) + "\n"
        t = a["file"].read_text(encoding="utf-8")
        if SECTION in t:
            n = SECTION_RE.sub(lambda _: "\n\n" + block, t, count=1)
        elif "\n## Рецензія" in t:
            n = t.replace("\n## Рецензія", "\n" + block + "\n## Рецензія", 1)
        else:
            n = t.rstrip("\n") + "\n\n" + block
        if n != t:
            changed.append(a["cat"])
            if not dry:
                a["file"].write_text(n, encoding="utf-8")
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    albums = load_albums(v)
    made = import_new(v, albums, a.dry_run)
    for out, cat, au in made:
        print(f"  + {out.name}  ({cat}{', ' + au if au else ', автор не визначений'})")
    linked = link_albums(v, albums, a.dry_run)
    print(f"✓ нових liner notes: {len(made)} · сторінок альбомів з оновленим списком: {len(linked)}"
          + (" [DRY-RUN]" if a.dry_run else ""))


if __name__ == "__main__":
    main()

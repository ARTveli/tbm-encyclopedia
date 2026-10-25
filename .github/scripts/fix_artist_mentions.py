"""
fix_artist_mentions.py — замінює на сторінках артистів Dataview-блок
«Згадки в статтях та інтерв'ю» на статичний список посилань і прибирає
підказку «Усі беклінки / Cmd+Shift+B».

Згадкою вважається: посилання [[Артист — Ім'я…]] або ім'я текстом
у файлах тек Інтервʼю/ і Topics/ (а також поле subject інтерв'ю).

Можна запускати повторно — секція перебудовується з актуальних файлів.
Бекап теки Артисти/ кладеться ПОЗА vault: ~/TBM/backups/Артисти-<дата>/

Запуск:
    python3 fix_artist_mentions.py --vault ~/TBM/TBM_Vault --dry-run
    python3 fix_artist_mentions.py --vault ~/TBM/TBM_Vault
"""

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

HEAD = "## Згадки в статтях та інтерв'ю"
SECTION_RE = re.compile(r"\n*^## Згадки в статтях та інтерв.ю\s*$.*?(?=^## (?!Усі беклінки)|\Z)", re.M | re.S)
BACKLINKS_RE = re.compile(r"\n*^## Усі беклінки\s*\n(?:Cmd\+Shift\+B[^\n]*\n?)?", re.M)


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1) if m else ""), text[m.end():] if m else text


def field(fm, key):
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def load_sources(vault: Path):
    out = []
    for folder, kind in (("Інтервʼю", "Інтерв'ю"), ("Інтерв'ю", "Інтерв'ю"), ("Topics", "Нарис")):
        d = vault / folder
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name == "index.md":
                continue
            fm, body = frontmatter(f.read_text(encoding="utf-8"))
            title = field(fm, "title") or f.stem
            out.append({
                "link": f"{folder}/{f.stem}",
                "title": title,
                "kind": kind,
                "subject": field(fm, "subject"),
                "body": body,
            })
    return out


def mentions(name: str, sources):
    link_re = re.compile(r"\[\[Артист — " + re.escape(name) + r"(?:\||\]\])")
    hits = []
    for s in sources:
        if name in s["subject"] or link_re.search(s["body"]) or name in s["body"]:
            hits.append(s)
    return hits


def build_section(hits):
    if not hits:
        return "\n"
    lines = [f"- [[{h['link']}|{h['title']}]] · {h['kind']}" for h in hits]
    return f"\n\n{HEAD}\n\n" + "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    vault = a.vault.expanduser()
    artists_dir = vault / "Артисти"

    sources = load_sources(vault)
    changed, total_links, samples = [], 0, []
    for f in sorted(artists_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        fm, _ = frontmatter(text)
        name = field(fm, "name") or f.stem.replace("Артист — ", "")
        hits = mentions(name, sources)
        new = BACKLINKS_RE.sub("\n", text)
        if SECTION_RE.search(new):
            new = SECTION_RE.sub(lambda _: build_section(hits), new, count=1)
        else:
            new = new.rstrip("\n") + build_section(hits)
        new = re.sub(r"\n{3,}", "\n\n", new).rstrip("\n") + "\n"
        if new != text:
            changed.append((f, new))
            total_links += len(hits)
            if hits and len(samples) < 3:
                samples.append((name, [h["title"] for h in hits]))

    print(f"Джерел (інтерв'ю + нариси): {len(sources)}")
    print(f"Сторінок артистів до зміни: {len(changed)} з {len(list(artists_dir.glob('*.md')))}")
    print(f"Посилань-згадок буде додано: {total_links}")
    for n, t in samples:
        print(f"  • {n}: {', '.join(t)}")

    if a.dry_run:
        print("\n[DRY-RUN] Нічого не записано.")
        return
    if changed:
        bdir = vault.parent / "backups" / f"Артисти-{datetime.now():%Y%m%d-%H%M%S}"
        shutil.copytree(artists_dir, bdir)
        for f, new in changed:
            f.write_text(new, encoding="utf-8")
        print(f"\n✓ Оновлено {len(changed)} сторінок · бекап: {bdir}")


if __name__ == "__main__":
    main()

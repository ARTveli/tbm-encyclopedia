"""
build_ensembles.py — додає на сторінку кожного альбому схему ансамблю:
ритм-секція позаду, солісти попереду, з інструментами і підказками українською.

Інструменти беруться з блоків «○ Склад» у тексті книги (як у build_database.py).
Схема стоїть одразу під заголовком «## Склад»; звичайний список під нею
лишається у файлі (для зворотних посилань), але на сайті ховається стилем.

Можна запускати повторно — блок між маркерами перебудовується.
Бекап теки Альбоми/ кладеться ПОЗА vault: ~/TBM/backups/Альбоми-<дата>/

Запуск (з теки, де лежить build_database.py):
    python3 build_ensembles.py --vault ~/TBM/TBM_Vault --dry-run
    python3 build_ensembles.py --vault ~/TBM/TBM_Vault
"""

import argparse
import html
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_database import (INSTR_GROUP, INSTR_UA, _catkey, _norm, find_book, parse_frontmatter,  # noqa: E402
                            parse_lineups, slugify)

START, END = "<!-- tbm-ensemble:start -->", "<!-- tbm-ensemble:end -->"
BACK = ["drums", "bass", "keys", "guitar"]          # ритм-секція
FRONT = ["reeds", "brass", "strings", "vocal"]      # солісти
BLOCK_RE = re.compile(r"\n*" + re.escape(START) + r".*?" + re.escape(END) + r"\n*", re.S)


def member(name, ins, pages):
    e = html.escape
    page = pages.get(_norm(name))
    nm = f'<a href="../{e(slugify("Артисти/" + page))}">{e(name)}</a>' if page else f"<span>{e(name)}</span>"
    ab = " ".join(f'<abbr class="tbm-i" tabindex="0" data-t="{e(INSTR_UA.get(x, x))}">{e(x)}</abbr>' for x in ins)
    g = INSTR_GROUP.get(next((x for x in ins if INSTR_GROUP.get(x) != "other"), ins[0]), "other")
    return f'<span class="tbm-ens-m" data-g="{g}"><i></i>{nm} {ab}</span>'


def build(lineup, pages):
    def sec(x):
        play = [i for i in x[1] if INSTR_GROUP.get(i) != "other"]
        return INSTR_GROUP.get(play[0], "other") if play else "other"

    rows = {"back": [], "front": [], "other": []}
    for n, ins in lineup:
        g = sec((n, ins))
        rows["back" if g in BACK else "front" if g in FRONT else "other"].append((g, n, ins))
    order = {g: i for i, g in enumerate(BACK + FRONT + ["other"])}
    out = [START, '<div class="tbm-ens">']
    for key, label in (("back", "Ритм-секція"), ("front", "Солісти")):
        ms = sorted(rows[key], key=lambda x: order[x[0]])
        if ms:
            out.append(f'<div class="tbm-ens-row"><b>{label}</b>'
                       + "".join(member(n, ins, pages) for _, n, ins in ms) + "</div>")
    if rows["other"]:
        out.append('<div class="tbm-ens-row tbm-ens-extra"><b>Аранжування та диригування</b>'
                   + "".join(member(n, ins, pages) for _, n, ins in rows["other"]) + "</div>")
    out += ['<p class="tbm-ens-stage">слухачі</p>', "</div>", END]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    book = find_book(v)
    if not book:
        raise SystemExit("✗ Не знайшов у vault файл книги з блоками «○ Склад»")
    lineups = parse_lineups(book)
    pages = {_norm(f.stem.replace("Артист — ", "")): f.stem for f in (v / "Артисти").glob("*.md")}

    changed, skipped = [], []
    for f in sorted((v / "Альбоми").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        cat = fm.get("catalog") or f.stem
        book_lu = {_norm(n): ins for n, ins in lineups.get(_catkey(cat), [])}
        lineup = [(p, book_lu[_norm(p)]) for p in (fm.get("personnel") or []) if p and book_lu.get(_norm(p))]
        new = BLOCK_RE.sub("\n\n", text)
        if lineup and re.search(r"^## Склад\s*$", new, re.M):
            new = re.sub(r"^(## Склад)[ \t]*\n+", lambda m: m.group(1) + "\n\n" + build(lineup, pages) + "\n\n",
                         new, count=1, flags=re.M)
        else:
            skipped.append(cat)
        if new != text:
            changed.append((f, new))

    print(f"Книга: {book.name} · альбомів зі схемою: {len(changed)} · без схеми: {len(skipped)}")
    if skipped:
        print("  без схеми (немає «○ Склад» у книзі або розділу «## Склад»):", ", ".join(skipped))
    if a.dry_run:
        if changed:
            f, new = changed[0]
            i = new.find(START)
            print(f"\n[DRY-RUN] {f.name}:\n" + new[i:new.find(END) + len(END)])
        return
    if changed:
        bdir = v.resolve().parent / "backups" / f"Альбоми-{datetime.now():%Y%m%d-%H%M%S}"
        shutil.copytree(v / "Альбоми", bdir)
        for f, new in changed:
            f.write_text(new, encoding="utf-8")
        print(f"✓ Оновлено {len(changed)} сторінок · бекап: {bdir}")


if __name__ == "__main__":
    main()

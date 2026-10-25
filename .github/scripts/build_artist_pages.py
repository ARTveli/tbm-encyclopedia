"""
build_artist_pages.py — оновлює сторінки артистів:
  • рядок «Інструменти:» — скорочення з підказками українською (працюють і на телефоні, тапом);
  • таблиця «Дискографія на TBM» — нова колонка «Інструмент»: на чому музикант грав
    саме на цьому альбомі (з блоків «○ Склад» у книзі).

Можна запускати повторно (після виправлення імен тощо) — рядок і колонка перебудовуються.
Бекап теки Артисти/ кладеться ПОЗА vault: ~/TBM/backups/Артисти-<дата>/

Запуск (з теки, де лежить build_database.py):
    python3 build_artist_pages.py --vault ~/TBM/TBM_Vault --dry-run
    python3 build_artist_pages.py --vault ~/TBM/TBM_Vault
"""
import argparse
import html
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_database import (INSTR_UA, _ALIAS, _catkey, _norm, find_book,  # noqa: E402
                            parse_frontmatter, parse_lineups)

EXTRA = {"etc": "та інші інструменти", "etc.": "та інші інструменти"}
CELL = re.compile(r"(?<!\\)\|")


def abbr(tok):
    t = tok.strip()
    k = t.lower().rstrip(".") if t.lower() not in EXTRA else t.lower()
    d = EXTRA.get(t.lower()) or INSTR_UA.get(_ALIAS.get(k, k))
    if not d:
        return html.escape(t)
    return f'<abbr class="tbm-i" tabindex="0" data-t="{html.escape(d)}">{html.escape(t)}</abbr>'


def abbr_list(tokens):
    return ", ".join(abbr(t) for t in tokens if t.strip())


def fix_table(lines, name, lineups):
    """Додає/оновлює колонку «Інструмент» у таблиці дискографії."""
    out, i, n_hit = [], 0, 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\|\s*Рік\s*\|\s*Каталог\s*\|", line) and i + 1 < len(lines) and re.match(r"^\|[-\s|:]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in CELL.split(line)[1:-1]]
            has = "Інструмент" in head
            if not has:
                head.insert(3, "Інструмент")
            out.append("| " + " | ".join(head) + " |")
            out.append("|" + "|".join("-" * (len(h) + 2) for h in head) + "|")
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in CELL.split(lines[i])[1:-1]]
                m = re.search(r"\[\[([^\]|\\]+)", cells[1]) if len(cells) > 1 else None
                ins = []
                if m:
                    lu = {_norm(n): x for n, x in lineups.get(_catkey(m.group(1)), [])}
                    ins = lu.get(_norm(name), [])
                if ins:
                    n_hit += 1
                val = abbr_list(ins)
                if has:
                    cells[3] = val
                else:
                    cells.insert(3, val)
                out.append("| " + " | ".join(cells) + " |")
                i += 1
            continue
        out.append(line)
        i += 1
    return out, n_hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    book = find_book(v)
    lineups = parse_lineups(book) if book else {}
    changed, rows_total, rows_hit = [], 0, 0
    for f in sorted((v / "Артисти").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        name = fm.get("name") or f.stem.replace("Артист — ", "")
        instr = fm.get("instruments") or ""
        new = text
        if instr:
            new = re.sub(r"^\*\*Інструменти:\*\*.*$", lambda _: "**Інструменти:** " + abbr_list(instr.split(",")),
                         new, count=1, flags=re.M)
        lines, hit = fix_table(new.split("\n"), name, lineups)
        new = "\n".join(lines)
        rows_total += sum(1 for l in lines if re.match(r"^\|\s*\d{4}\s*\|", l))
        rows_hit += hit
        if new != text:
            changed.append((f, new))
    print(f"Сторінок артистів до зміни: {len(changed)} · рядків дискографії з інструментом: {rows_hit} з {rows_total}")
    if a.dry_run:
        if changed:
            f, new = next(((f, n) for f, n in changed if "Ісао Судзукі" in f.name), changed[0])
            body = new.split("---", 2)[2]
            print(f"\n[DRY-RUN] {f.name}:\n" + "\n".join(body.split("\n")[:22]))
        return
    if changed:
        bdir = v.parent / "backups" / f"Артисти-{datetime.now():%Y%m%d-%H%M%S}"
        shutil.copytree(v / "Артисти", bdir)
        for f, new in changed:
            f.write_text(new, encoding="utf-8")
        print(f"✓ Оновлено {len(changed)} сторінок · бекап: {bdir}")


if __name__ == "__main__":
    main()

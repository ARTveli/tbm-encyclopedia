"""
add_personnel.py — доповнює склади альбомів музикантами з тексту книги.

У блоках «○ Склад» книги для біг-бендів і великих складів вказано більше людей,
ніж у полі personnel сторінки альбому. Скрипт дописує відсутніх:
  • у frontmatter `personnel:`
  • у список під «## Склад» (у тому ж форматі [[Артист — Ім'я|Ім'я]])
Назви гуртів («Дует … та …») і латинські назви (Freezer) пропускає.

Можна запускати повторно — додає лише тих, кого ще немає.
Бекап теки Альбоми/: ~/TBM/backups/Альбоми-personnel-<дата>/
Запуск:
    python3 add_personnel.py --vault ~/TBM/TBM_Vault --dry-run
    python3 add_personnel.py --vault ~/TBM/TBM_Vault
"""
import argparse, re, shutil, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_database import _catkey, _norm, find_book, parse_frontmatter, parse_lineups  # noqa: E402


def is_person(n):
    return bool(re.search(r"[А-Яа-яІіЇїЄєҐґ]", n)) and not n.startswith("Дует") and " та " not in n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    lineups = parse_lineups(find_book(v))
    changed, total = [], 0
    for f in sorted((v / "Альбоми").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        have = {_norm(p) for p in fm.get("personnel") or []}
        add = []
        for n, _ins in lineups.get(_catkey(fm.get("catalog") or f.stem), []):
            if is_person(n) and _norm(n) not in have:
                add.append(n)
                have.add(_norm(n))
        if not add:
            continue
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        fmt = m.group(1)
        pm = re.search(r"^personnel:\n((?:\s*-\s+.*\n?)*)", fmt + "\n", re.M)
        if not pm:
            continue
        block = pm.group(0).rstrip("\n")
        fm_new = fmt.replace(block, block + "".join(f"\n- {n}" for n in add), 1)
        new = text.replace(fmt, fm_new, 1)
        # список під «## Склад»: після останнього пункту-посилання на артиста
        sec = re.search(r"^## Склад\s*\n(.*?)(?=^## |\Z)", new, re.S | re.M)
        if sec:
            body = sec.group(1)
            items = list(re.finditer(r"^- \[\[Артист — [^\n]*$", body, re.M))
            if items:
                end = sec.start(1) + items[-1].end()
                new = new[:end] + "".join(f"\n- [[Артист — {n}|{n}]]" for n in add) + new[end:]
        changed.append((f, new, add))
        total += len(add)
    print(f"Альбомів до зміни: {len(changed)} · музикантів додається: {total}")
    for f, _, add in changed:
        print(f"  {f.stem}: {', '.join(add)}")
    if a.dry_run:
        print("\n[DRY-RUN] Нічого не записано.")
        return
    if changed:
        bdir = v.resolve().parent / "backups" / f"Альбоми-personnel-{datetime.now():%Y%m%d-%H%M%S}"
        shutil.copytree(v / "Альбоми", bdir)
        for f, new, _ in changed:
            f.write_text(new, encoding="utf-8")
        print(f"✓ Оновлено {len(changed)} альбомів · бекап: {bdir}")


if __name__ == "__main__":
    main()

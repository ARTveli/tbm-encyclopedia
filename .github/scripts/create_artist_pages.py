"""
create_artist_pages.py — створює сторінки для музикантів, які є в складах альбомів
(personnel), але ще не мають своєї сторінки в Артисти/.

Інструменти — з блоків «○ Склад» книги (усі, на яких музикант грав на TBM,
від найчастішого). Таблицю дискографії та згадки потім заповнюють
build_artist_pages.py і fix_artist_mentions.py (tbm_update.py робить це сам).

    python3 create_artist_pages.py --vault ~/TBM/TBM_Vault --dry-run
    python3 create_artist_pages.py --vault ~/TBM/TBM_Vault
"""
import argparse, collections, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_database import INSTR_GROUP, _catkey, _norm, find_book, parse_frontmatter, parse_lineups  # noqa: E402

SKIP = {"Гість", "Гості", "Струнний оркестр", "Фортепіанне тріо"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    pages = {_norm(f.stem.replace("Артист — ", "")) for f in (v / "Артисти").glob("*.md")}
    lineups = parse_lineups(find_book(v))
    need = collections.OrderedDict()
    for f in sorted((v / "Альбоми").glob("*.md")):
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        lu = {_norm(n): i for n, i in lineups.get(_catkey(fm.get("catalog") or f.stem), [])}
        for p in fm.get("personnel") or []:
            if p in SKIP or _norm(p) in pages or not re.search(r"[А-Яа-яІіЇї]", p):
                continue
            need.setdefault(p, collections.Counter()).update(lu.get(_norm(p), []))
    for name, cnt in need.items():
        ins = [k for k, _ in cnt.most_common()]
        play = [k for k in ins if INSTR_GROUP.get(k) != "other"] or ins
        tags = ["- artist"] + ([f"- instr/{play[0]}"] if play else [])
        text = ("---\ntype: artist\n" f'title: "{name}"\nname: {name}\n'
                + (f"instruments: {', '.join(ins)}\n" if ins else "")
                + "tags:\n" + "\n".join(tags) + "\n---\n\n"
                f"# {name}\n\n" + (f"**Інструменти:** {', '.join(ins)}\n\n" if ins else "")
                + "## Дискографія на TBM (0 альбомів)\n\n| Рік | Каталог | Альбом | Інструмент | Лідер |\n"
                "|-----|---------|--------|------------|-------|\n")
        print(f"  + Артист — {name}.md  ({', '.join(ins) or 'інструмент невідомий'})")
        if not a.dry_run:
            (v / "Артисти" / f"Артист — {name}.md").write_text(text, encoding="utf-8")
    print(f"✓ нових сторінок артистів: {len(need)}" + (" [DRY-RUN]" if a.dry_run else ""))


if __name__ == "__main__":
    main()

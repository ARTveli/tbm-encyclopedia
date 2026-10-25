"""
fix_liner.py — порядок у liner notes (ітерація 4 аудиту).

  • title: «<Назва альбому>: liner notes» замість назви файлу TBM-39_liner
    (вкладка браузера, пошук, прев'ю в месенджерах);
  • одне написання перекладача: «Юко М. DARWEN» → «Юко М. Дарвен»;
  • «Такео Фудзії» → «Такеші Фудзії» (це засновник лейблу).
Поле автора (original_author) не чіпається.

Бекап змінених файлів: ~/TBM/backups/liner-<дата>/
    python3 fix_liner.py --vault ~/TBM/TBM_Vault --dry-run
    python3 fix_liner.py --vault ~/TBM/TBM_Vault
"""
import argparse, re, shutil
from datetime import datetime
from pathlib import Path

REPL = {"Юко М. DARWEN": "Юко М. Дарвен", "Такео Фудзії": "Такеші Фудзії"}
IGN = {".github", ".obsidian", "_originals", "copilot", "media-lib", ".git"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    changes, titles, hits = {}, 0, {k: 0 for k in REPL}
    for f in v.rglob("*.md"):
        if IGN & set(f.relative_to(v).parts):
            continue
        t = f.read_text(encoding="utf-8")
        n = t
        for k, r in REPL.items():
            hits[k] += n.count(k)
            n = n.replace(k, r)
        if f.parent.name == "Liner_Notes" and f.name != "index.md":
            m = re.match(r"^---\n(.*?)\n---\n", n, re.S)
            if m and not re.search(r"^title:", m.group(1), re.M):
                at = re.search(r"^album_title:\s*(.+)$", m.group(1), re.M)
                cat = re.search(r"^catalog:\s*(.+)$", m.group(1), re.M)
                name = (at.group(1) if at else cat.group(1) if cat else f.stem).strip().strip("\"'")
                title = f"{name}: liner notes".replace('"', '\\"')
                fm = re.sub(r"^(type:.*)$", rf'\1\ntitle: "{title}"', m.group(1), count=1, flags=re.M)
                n = n.replace(m.group(1), fm, 1)
                titles += 1
        if n != t:
            changes[f] = n
    print(f"Файлів до зміни: {len(changes)} · назв liner notes: {titles} · " +
          " · ".join(f"«{k}»: {c}" for k, c in hits.items()))
    if a.dry_run:
        ex = next((n for f, n in changes.items() if f.name == "TBM-39_liner.md"), None)
        if ex:
            print("\n[DRY-RUN] TBM-39_liner.md:\n" + "\n".join(ex.split("\n")[:5]))
        return
    bdir = v.resolve().parent / "backups" / f"liner-{datetime.now():%Y%m%d-%H%M%S}"
    for f, n in changes.items():
        b = bdir / f.relative_to(v)
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, b)
        f.write_text(n, encoding="utf-8")
    print(f"✓ Записано · бекап: {bdir}")


if __name__ == "__main__":
    main()

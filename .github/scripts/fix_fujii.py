"""
fix_fujii.py — ім'я засновника TBM за нормами української транскрипції: «Такесі Фудзії».

Замінює «Такеші Фуджі», «Такеші Фудзії», «Фуджі Такеші», окреме «Фуджі»/«Фуджі-сан»
(крім «Ейічі Фуджі» — це інша людина) і теги з підкресленням.
«Фуджіі» не чіпає — так записані прізвища інших музикантів (Садаясу Фуджіі тощо).
Перейменовує «Інтерв'ю з Такеші Фуджі.md» (стара адреса лишається перенаправленням).

    python3 fix_fujii.py --vault ~/TBM/TBM_Vault --dry-run
    python3 fix_fujii.py --vault ~/TBM/TBM_Vault
"""
import argparse, re, shutil
from datetime import datetime
from pathlib import Path

IGN = {".github", ".obsidian", "_originals", "copilot", "media-lib", ".git"}
L = r"А-Яа-яІіЇїЄєҐґA-Za-z'ʼ’"
RULES = [
    (r"Такеш[іи](\s+\"Ті\"\s+|\s+|_)Фу(?:дж|дз)і[ії]?(?![" + L + "])", lambda m: f"Такесі{m.group(1)}Фудзії"),
    (r"Такео(\s+|_)Фудзії", lambda m: f"Такесі{m.group(1)}Фудзії"),
    (r"Фуджі Такеші", lambda m: "Фудзії Такесі"),
    (r"(?<![" + L + r"])(?<!Ейічі )Фуджі(?=-сан|[^" + L + "]|$)", lambda m: "Фудзії"),
]
OLD, NEW = "Інтерв'ю з Такеші Фуджі", "Інтерв'ю з Такесі Фудзії"


def fix(t):
    n = 0
    for pat, rep in RULES:
        t, k = re.subn(pat, rep, t)
        n += k
    return t, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    changes, total = {}, 0
    for f in v.rglob("*.md"):
        if IGN & set(f.relative_to(v).parts):
            continue
        t = f.read_text(encoding="utf-8")
        n, k = fix(t)
        if k:
            changes[f] = n
            total += k
    src = v / "Інтервʼю" / f"{OLD}.md"
    print(f"Замін: {total} у {len(changes)} файлах · перейменування: {src.name if src.exists() else '—'}")
    if a.dry_run:
        return
    bdir = v.resolve().parent / "backups" / f"fujii-{datetime.now():%Y%m%d-%H%M%S}"
    for f, n in changes.items():
        b = bdir / f.relative_to(v)
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, b)
        f.write_text(n, encoding="utf-8")
    if src.exists():
        t = src.read_text(encoding="utf-8")
        t = re.sub(r"^---\n", f"---\naliases: [\"Інтервʼю/{OLD}\"]\n", t, count=1) if t.startswith("---") else t
        (v / "Інтервʼю" / f"{NEW}.md").write_text(t, encoding="utf-8")
        src.unlink()
    print(f"✓ Записано · бекап: {bdir}")


if __name__ == "__main__":
    main()

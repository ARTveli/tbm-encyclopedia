"""
build_series.py — рядок «Серія …» на сторінці кожного альбому.

Серію визначає за каталожним номером (SERIES / series_of у build_database.py),
вставляє блок одразу після рядка з артистом і роком:

    <!-- tbm-series:start -->
    <div class="tbm-ser">…Серія 3000 · 76 см/с — пояснення…</div>
    <!-- tbm-series:end -->

Ідемпотентний: старий блок замінюється, без змін файл не перезаписується.
    python3 build_series.py --vault ~/TBM/TBM_Vault --dry-run
"""
import argparse
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_database import SERIES, parse_frontmatter, series_of  # noqa: E402

START, END = "<!-- tbm-series:start -->", "<!-- tbm-series:end -->"
BLOCK_RE = re.compile(r"\n*" + re.escape(START) + r".*?" + re.escape(END) + r"\n*", re.S)
INFO = {i: (l, s, d) for i, l, s, d in SERIES}


def block(sid):
    label, short, desc = INFO[sid]
    # «/» у тексті посилання Quartz обрізає (лишає частину після слеша) → дробова риска «⁄»
    return (f'{START}\n<div class="tbm-ser s-{sid}"><a class="tbm-ser-tag" href="../Каталог#серії-каталогу">'
            f'{html.escape(label + " · " + short).replace("/", "⁄")}</a> <span class="tbm-ser-d">{html.escape(desc)}</span></div>\n{END}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    changed = 0
    for f in sorted((v / "Альбоми").glob("*.md")):
        t = f.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(t)
        if fm.get("type") != "album" or not fm.get("catalog"):
            continue
        b = block(series_of(fm["catalog"]))
        n = BLOCK_RE.sub("\n\n", t, count=1)
        # після першого рядка, що йде за заголовком «# …» (артист · рік)
        m = re.search(r"^# .*\n(?:[ \t]*\n)*(\*\*.*\n)", n, re.M)
        if not m:
            print(f"  ⚠ {f.name}: не знайшов рядок з артистом, пропущено")
            continue
        pos = m.end()
        n = n[:pos] + "\n" + b + "\n\n" + n[pos:].lstrip("\n")
        if n != t:
            changed += 1
            if not a.dry_run:
                f.write_text(n, encoding="utf-8")
    print(f"✓ серії: оновлено сторінок альбомів — {changed}" + (" [DRY-RUN]" if a.dry_run else ""))


if __name__ == "__main__":
    main()

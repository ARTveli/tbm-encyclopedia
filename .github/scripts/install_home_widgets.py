"""
install_home_widgets.py — підключає компонент TBMHome (стопка платівок + «Альбом дня»).

Робить у ~/TBM/TBM_Vault/.github/:
  1. quartz/quartz.layout.ts — import TBMHome + afterBody: [TBMHome()]
  2. workflows/deploy.yml   — копіювання TBMHome.tsx і scripts/tbmhome.inline.ts у збірку
Бекапи: *.backup-widgets (один раз).

Запуск:
    python3 install_home_widgets.py --vault ~/TBM/TBM_Vault
"""

import argparse
import re
import shutil
from pathlib import Path

CP_LINES = [
    "          cp vault/.github/quartz/components/TBMHome.tsx quartz/quartz/components/TBMHome.tsx",
    "          cp vault/.github/quartz/components/scripts/tbmhome.inline.ts quartz/quartz/components/scripts/tbmhome.inline.ts",
]


def backup(p: Path):
    b = p.with_name(p.name + ".backup-widgets")
    if not b.exists():
        shutil.copy2(p, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    gh = ap.parse_args().vault.expanduser() / ".github"
    comp = gh / "quartz" / "components"
    for f in (comp / "TBMHome.tsx", comp / "scripts" / "tbmhome.inline.ts"):
        if not f.exists():
            raise SystemExit(f"✗ Не знайдено {f} — спочатку поклади файл")

    # 1. layout
    lay = gh / "quartz" / "quartz.layout.ts"
    t = lay.read_text(encoding="utf-8")
    if "TBMHome" in t:
        print("✓ quartz.layout.ts: TBMHome вже підключений")
    else:
        backup(lay)
        t = re.sub(r'(import \* as Component from "\./quartz/components"\n)',
                   r'\1import TBMHome from "./quartz/components/TBMHome"\n', t, count=1)
        t, n = re.subn(r"(sharedPageComponents[^{]*\{[^}]*?afterBody:\s*\[)", r"\1TBMHome(), ", t, count=1, flags=re.S)
        if not n:
            raise SystemExit("✗ Не знайшов afterBody у sharedPageComponents")
        lay.write_text(t, encoding="utf-8")
        print("✓ quartz.layout.ts: додано TBMHome")

    # 2. workflow
    wf = gh / "workflows" / "deploy.yml"
    w = wf.read_text(encoding="utf-8")
    missing = [l for l in CP_LINES if l.strip() not in w]
    if not missing:
        print("✓ deploy.yml: файли вже копіюються")
    else:
        backup(wf)
        anchor = "          cp vault/.github/quartz/quartz.layout.ts quartz/quartz.layout.ts"
        if anchor not in w:
            raise SystemExit("✗ Не знайшов рядок копіювання quartz.layout.ts у deploy.yml")
        wf.write_text(w.replace(anchor, anchor + "\n" + "\n".join(missing), 1), encoding="utf-8")
        print("✓ deploy.yml: додано копіювання TBMHome")


if __name__ == "__main__":
    main()

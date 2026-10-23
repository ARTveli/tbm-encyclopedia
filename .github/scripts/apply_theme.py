"""
apply_theme.py — переводить сайт на палітру й шрифти «TBM Полиця».

Робить у ~/TBM/TBM_Vault/.github/:
  1. quartz/quartz.config.ts — кольори світлої/темної теми + шрифт тексту
  2. workflows/deploy.yml   — копіювання quartz/styles/custom.scss у збірку
Перед змінами кладе бекапи *.backup-design (один раз, не перезаписує).

Запуск:
    python3 apply_theme.py --vault ~/TBM/TBM_Vault
"""

import argparse
import re
import shutil
from pathlib import Path

COLORS = """colors: {
        lightMode: {
          light: "#f4efe6",
          lightgray: "#e3dacb",
          gray: "#8f8576",
          darkgray: "#3a342c",
          dark: "#1d1a16",
          secondary: "#b4432b",
          tertiary: "#d0694f",
          highlight: "rgba(180, 67, 43, 0.07)",
          textHighlight: "#f2c94c66",
        },
        darkMode: {
          light: "#14120f",
          lightgray: "#2f2a24",
          gray: "#8d8475",
          darkgray: "#d9d1c4",
          dark: "#efe8dc",
          secondary: "#e0694d",
          tertiary: "#f08a6e",
          highlight: "rgba(224, 105, 77, 0.1)",
          textHighlight: "#b3aa0288",
        },
      }"""

CSS_LINE = "          cp vault/.github/quartz/styles/custom.scss quartz/quartz/styles/custom.scss"


def backup(p: Path):
    b = p.with_name(p.name + ".backup-design")
    if not b.exists():
        shutil.copy2(p, b)
        print(f"  бекап: {b.relative_to(p.parents[2])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    gh = ap.parse_args().vault / ".github"

    cfg = gh / "quartz" / "quartz.config.ts"
    wf = gh / "workflows" / "deploy.yml"
    css = gh / "quartz" / "styles" / "custom.scss"
    if not css.exists():
        raise SystemExit(f"✗ Спочатку поклади custom.scss у {css}")

    # 1. кольори + шрифт
    backup(cfg)
    t = cfg.read_text(encoding="utf-8")
    t2, n = re.subn(r"colors:\s*\{\s*lightMode:\s*\{.*?\},\s*darkMode:\s*\{.*?\},\s*\}", COLORS, t, count=1, flags=re.S)
    if not n:
        raise SystemExit("✗ Не знайшов блок theme.colors у quartz.config.ts")
    t2 = re.sub(r'body:\s*"[^"]*"', 'body: "Schibsted Grotesk"', t2, count=1)
    cfg.write_text(t2, encoding="utf-8")
    print("✓ quartz.config.ts: палітра і шрифт оновлені")

    # 2. workflow
    w = wf.read_text(encoding="utf-8")
    if CSS_LINE.strip() in w:
        print("✓ deploy.yml: custom.scss вже копіюється")
    else:
        backup(wf)
        anchor = "          cp vault/.github/quartz/quartz.layout.ts quartz/quartz.layout.ts"
        if anchor not in w:
            raise SystemExit("✗ Не знайшов рядок копіювання quartz.layout.ts у deploy.yml")
        wf.write_text(w.replace(anchor, anchor + "\n" + CSS_LINE, 1), encoding="utf-8")
        print("✓ deploy.yml: додано копіювання custom.scss")


if __name__ == "__main__":
    main()

"""
tbm_update.py — одна команда, яка оновлює все згенероване в енциклопедії.

Запускається автоматично в GitHub Actions при кожному push (і зберігає зміни
назад у репозиторій), а також вручну — щоб одразу побачити результат в Obsidian:

    python3 .github/scripts/tbm_update.py --vault ~/TBM/TBM_Vault

Порядок кроків (кожен ідемпотентний — без нових даних нічого не змінює):
  1. liner_import        — нові liner notes з _originals/ + списки на сторінках альбомів
  2. fix_names           — одне написання імен музикантів
  3. fix_fujii           — «Такесі Фудзії»
  4. fix_liner           — назви сторінок liner notes, написання перекладача
  5. build_artist_pages  — дискографії й інструменти на сторінках артистів
  6. build_ensembles     — схеми ансамблів на сторінках альбомів
  7. fix_artist_mentions — згадки артистів в інтерв'ю та нарисах
  8. build_meta          — описи й картинки прев'ю
  9. make_thumbs         — мініатюри обкладинок (якщо встановлено Pillow)
 10. build_home          — головна, сторінка Liner Notes, обкладинки на liner notes
"""
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["liner_import", "fix_names", "fix_fujii", "fix_liner", "build_artist_pages",
         "build_ensembles", "fix_artist_mentions", "build_meta", "make_thumbs", "build_home"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    vault = str(ap.parse_args().vault.expanduser())
    failed = []
    for name in STEPS:
        if name == "make_thumbs" and importlib.util.find_spec("PIL") is None:
            print(f"── {name}: пропущено (немає Pillow: python3 -m pip install pillow)")
            continue
        print(f"── {name}")
        r = subprocess.run([sys.executable, str(HERE / f"{name}.py"), "--vault", vault],
                           capture_output=True, text=True)
        lines = [l for l in (r.stdout + r.stderr).strip().split("\n") if l.strip()]
        for l in lines[-4:]:
            print("   " + l)
        if r.returncode != 0:
            failed.append(name)
    if failed:
        sys.exit(f"✗ помилки в кроках: {', '.join(failed)}")
    print("✓ усе оновлено")


if __name__ == "__main__":
    main()

"""
fix_names.py — одне написання для кожного музиканта (ітерація 2 аудиту).

Замінює варіанти імен на обране написання в усіх .md vault (склади альбомів,
посилання [[Артист — …]], текст книги, liner notes, інтерв'ю), крім _originals/.
Для 4 музикантів, у яких помилка була в назві сторінки, перейменовує сторінку
(стара адреса лишається як перенаправлення через aliases).

Бекап усіх змінених файлів: ~/TBM/backups/names-<дата>/
Запуск:
    python3 fix_names.py --vault ~/TBM/TBM_Vault --dry-run
    python3 fix_names.py --vault ~/TBM/TBM_Vault
"""
import argparse, re, shutil
from datetime import datetime
from pathlib import Path

# варіант → обране написання
NAMES = {
    # A: одна людина, різна транслітерація (лишаємо як у назві сторінки)
    "Кендзі Морі": "Кенджі Морі", "Казумі Ватанабе": "Кадзумі Ватанабе",
    "Такаші Мідзухаші": "Такаші Мізухаші", "Тошіюкі Міяма": "Тосіюкі Міяма",
    "Кодзабуро Ямакі": "Козабуро Ямакі", "Йосіо Судзукі": "Йошіо Судзукі",
    "Сігеко Тоя": "Шігеко Тоя", "Сейічі Накамура": "Сеїчі Накамура",
    "Хіроші Ямазакі": "Хіроші Ямадзакі", "Акіра Окадзава": "Акіра Оказава",
    "Кадзунорі Огуро": "Казунорі Огуро", "Аллан Праскін": "Алан Праскін",
    "Йоїчі Огава": "Йоічі Огава", "Кенджі Накадзава": "Кенджі Наказава",
    "Тошіо Оїда": "Тошіо Оіда", "Кадзухіро Ебісава": "Казухіро Ебісава",
    "Казухіро Мацуіші": "Казухіро Мацуїші", "Кадзуаки Ямамото": "Казуакі Ямамото",
    "Шідзуо Накаяма": "Шізуо Накаяма", "Юкіхіко Нішідзава": "Юкіхіко Нішізава",
    "Хіроші Коїдзумі": "Хіроші Коїзумі", "Шудзі Ацута": "Шюджі Ацута",
    "Шоджі Іто": "Шьоджі Іто", "Шухей Кубо": "Шюхей Кубо", "Шозо Сасакі": "Шьозо Сасакі",
    "Шоджі Ямада": "Шьоджі Ямада", "Акіра Дої": "Акіра Дой", "Тейічі Табата": "Теїчі Табата",
    "Масакадзу Гото": "Масаказу Гото", "Ясуакі Шімідзу": "Ясуаки Шимізу",
    "Казумі Такеда": "Кадзумі Такеда", "Сусуму Кадзухара": "Сусуму Казухара",
    "Шин Окабе": "Шін Окабе", "Йоїчі Кімура": "Йоічі Кімура", "Томокадзу Сайо": "Томокадзу Саїо",
    "Шоічі Кудо": "Шьоїчі Кудо", "Тошіо Йокої": "Тошіо Йокоі", "Сігехару Канда": "Шігехару Канда",
    "Шоджі Такеучі": "Шьоджі Такеучі", "Джосуке Охата": "Джьосуке Охата",
    "Ясуказу Амемія": "Ясукадзу Амемія", "Шудзо Морікава": "Шузо Морікава",
    # B: друкарські помилки
    "Саданорі Накамуре": "Саданорі Накамура", "Шунзо Охно": "Шунзо Оно",
    "Масаабу Кікучі": "Масабумі Кікучі", "Такаші Шіка": "Такаші Шіката",
    "Ясуро Осава": "Ясуо Осава", "Джордж Кейблз": "Джордж Кейблс",
    "Джунічі Камеока": "Джун'ічі Камеока", "Джон Феддіс": "Джон Фаддіс",
    "Фуміо Шіраяма": "Фуміо Шірояма", "Садаюсу Фудзії": "Садаясу Фуджіі",
    "Шінічіро Окабе": "Шін'ічіро Окабе", "Шіннічі Катоока": "Шін'ічі Катоока",
    "Гайнц Зауер": "Хайнц Зауер", "Ікуо Шіозакі": "Ікуо Шіосакі",
    "Джорджі Курікі": "Джоджі Курікі", "Еспер Рунгорд": "Єспер Лундгаард",
    "Нобуйюкі Морікава": "Нобуюкі Морікава", "Томоя Хао": "Томоя Ханао",
}
# у складі альбому замість імені стояла назва гурту
PERSONNEL_ONLY = {"Дует Такаші Мізухаші": "Такаші Мізухаші"}
# сторінки, назва яких сама містила помилку
RENAME = ["Масаабу Кікучі", "Джорджі Курікі", "Еспер Рунгорд", "Нобуйюкі Морікава"]
IGN = {".github", ".obsidian", "_originals", "copilot", "media-lib", ".git"}
L = r"A-Za-zА-Яа-яІіЇїЄєҐґ'ʼ’"
PAT = re.compile(rf"(?<![{L}])(" + "|".join(re.escape(k) for k in sorted(NAMES, key=len, reverse=True)) + rf")(?![{L}])")


def _sub_keep_aliases(t, fn):
    """Заміна в усьому тексті, крім рядків aliases: (старі адреси для перенаправлень)."""
    return "\n".join(ln if ln.startswith("aliases:") else fn(ln) for ln in t.split("\n"))


def fix_text(t):
    t = _sub_keep_aliases(t, lambda ln: PAT.sub(lambda m: NAMES[m.group(1)], ln))
    t = t.replace("[[Артист — Дует Такаші Мізухаші", "[[Артист — Такаші Мізухаші")
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if m and "personnel:" in m.group(1):
        fm = m.group(1)
        lines, seen, out, inp = fm.split("\n"), set(), [], False
        for ln in lines:
            if re.match(r"^personnel:", ln):
                inp = True
                out.append(ln)
                continue
            if inp and re.match(r"^\s*-\s+", ln):
                name = re.sub(r"^\s*-\s+", "", ln).strip().strip("\"'")
                name = PERSONNEL_ONLY.get(name, name)
                if name in seen:
                    continue
                seen.add(name)
                out.append(f"- {name}")
                continue
            inp = False
            out.append(ln)
        t = t.replace(fm, "\n".join(out), 1)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    changes, hits = {}, {}
    for f in v.rglob("*.md"):
        if IGN & set(f.relative_to(v).parts):
            continue
        t = f.read_text(encoding="utf-8")
        for m in PAT.finditer("\n".join(ln for ln in t.split("\n") if not ln.startswith("aliases:"))):
            hits[m.group(1)] = hits.get(m.group(1), 0) + 1
        n = fix_text(t)
        if n != t:
            changes[f] = n
    renames = []
    for old in RENAME:
        src = v / "Артисти" / f"Артист — {old}.md"
        dst = v / "Артисти" / f"Артист — {NAMES[old]}.md"
        if src.exists() and not dst.exists():
            renames.append((src, dst, old))

    print(f"Замін: {sum(hits.values())} у {len(changes)} файлах · перейменувань сторінок: {len(renames)}")
    for k in sorted(hits, key=lambda k: -hits[k]):
        print(f"  {hits[k]:4} × {k} → {NAMES[k]}")
    for s, d, _ in renames:
        print(f"  ↪ {s.name} → {d.name}")
    missing = [k for k in NAMES if k not in hits]
    if missing and hits:
        print(f"  (ще {len(missing)} варіантів не знайдено — вже виправлені)")
    if a.dry_run:
        print("\n[DRY-RUN] Нічого не записано.")
        return
    bdir = v.resolve().parent / "backups" / f"names-{datetime.now():%Y%m%d-%H%M%S}"
    for f, n in changes.items():
        b = bdir / f.relative_to(v)
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, b)
        f.write_text(n, encoding="utf-8")
    for src, dst, old in renames:
        t = src.read_text(encoding="utf-8")
        t = re.sub(r"^---\n", f"---\naliases: [\"Артист — {old}\"]\n", t, count=1)
        dst.write_text(t, encoding="utf-8")
        src.unlink()
    print(f"✓ Записано · бекап: {bdir}")


if __name__ == "__main__":
    main()

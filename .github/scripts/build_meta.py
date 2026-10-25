"""
build_meta.py — назви й прев'ю сторінок для пошуку, вкладок і месенджерів.

  • Альбоми: description «TBM-39 · Тріо Масару Імади + 2 · 1975. Перше речення рецензії»
             і socialImage — обкладинка альбому (картинка прев'ю в Telegram тощо).
  • Артисти: title «Ісоо Фукуї» (без «Артист — ») і description з інструментами
             та кількістю альбомів.
  • Індекс_артистів.md: title «Індекс артистів».
Файли й посилання не змінюються — лише поля frontmatter. Можна запускати повторно.

Бекап змінених файлів: ~/TBM/backups/meta-<дата>/
    python3 build_meta.py --vault ~/TBM/TBM_Vault --dry-run
    python3 build_meta.py --vault ~/TBM/TBM_Vault
"""
import argparse, re, shutil, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_database import INSTR_UA, _ALIAS, parse_frontmatter, section, strip_md  # noqa: E402

MAXLEN = 200


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def set_fields(text, fields):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return text
    fm = m.group(1)
    for k, val in fields.items():
        line = f"{k}: {q(val)}"
        if re.search(rf"^{k}:.*$", fm, re.M):
            fm = re.sub(rf"^{k}:.*$", lambda _: line, fm, count=1, flags=re.M)
        else:
            fm = re.sub(r"^(type:.*)$", lambda mm: mm.group(1) + "\n" + line, fm, count=1, flags=re.M) \
                if re.search(r"^type:", fm, re.M) else line + "\n" + fm
    return text.replace(m.group(1), fm, 1)


def first_sentence(review, room):
    review = re.sub(r"\s+", " ", review).strip()
    if not review:
        return ""
    m = re.match(r"(.+?[.!?…])(\s|$)", review)
    s = m.group(1) if m else review
    if len(s) > room:
        s = s[:room].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"
    return s


def instr_ua(s):
    out = []
    for t in (s or "").split(","):
        t = t.strip().lower().rstrip(".")
        if t == "etc":
            continue
        d = INSTR_UA.get(_ALIAS.get(t, t))
        if d and d not in out:
            out.append(d)
    return ", ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    v = a.vault.expanduser()
    changes, samples = {}, []
    n_alb = {}
    for f in sorted((v / "Альбоми").glob("*.md")):
        t = f.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(t)
        if fm.get("type") != "album":
            continue
        head = " · ".join(str(x) for x in (fm.get("catalog"), fm.get("artist"), fm.get("year")) if x)
        rev = strip_md(section(body, "Рецензія").split("\n\n")[0]) if section(body, "Рецензія") else ""
        sent = first_sentence(rev, MAXLEN - len(head) - 2)
        fields = {"description": f"{head}. {sent}" if sent else head}
        if fm.get("cover") and (v / fm["cover"]).exists():
            fields["socialImage"] = fm["cover"]
        for p in fm.get("personnel") or []:
            n_alb[p] = n_alb.get(p, 0) + 1
        n = set_fields(t, fields)
        if n != t:
            changes[f] = n
            if len(samples) < 2:
                samples.append((f.name, fields))
    for f in sorted((v / "Артисти").glob("*.md")):
        t = f.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(t)
        name = fm.get("name") or f.stem.replace("Артист — ", "")
        cnt = n_alb.get(name, 0)
        ins = instr_ua(fm.get("instruments"))
        bits = [x for x in (ins, f"{cnt} альб. на Three Blind Mice" if cnt else "") if x]
        fields = {"title": name, "description": f"{name}: " + "; ".join(bits) if bits else name}
        n = set_fields(t, fields)
        if n != t:
            changes[f] = n
            if len(samples) < 4 and f.name.startswith("Артист — Ісоо"):
                samples.append((f.name, fields))
    idx = v / "Індекс_артистів.md"
    if idx.exists():
        t = idx.read_text(encoding="utf-8")
        n = set_fields(t, {"title": "Індекс артистів"}) if t.startswith("---") else "---\ntitle: \"Індекс артистів\"\n---\n" + t
        if n != t:
            changes[idx] = n
    print(f"Файлів до зміни: {len(changes)}")
    for name, fl in samples:
        print(f"  {name}: {fl}")
    if a.dry_run:
        return
    bdir = v.resolve().parent / "backups" / f"meta-{datetime.now():%Y%m%d-%H%M%S}"
    for f, n in changes.items():
        b = bdir / f.relative_to(v)
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, b)
        f.write_text(n, encoding="utf-8")
    print(f"✓ Записано · бекап: {bdir}")


if __name__ == "__main__":
    main()

"""
build_database.py — збирає data.json для інтерактивної сторінки /explore/
з усіх .md файлів vault (Альбоми, Артисти, Liner_Notes).

Запускається автоматично в GitHub Actions при кожному push.
Локально:
    python3 build_database.py --vault ~/TBM/TBM_Vault --out /tmp/data.json
"""

import argparse
import json
import re
from pathlib import Path


def parse_frontmatter(text: str):
    """Мінімальний YAML-парсер для нашого формату (key: value, списки '- item')."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    data, key = {}, None
    for line in block.split("\n"):
        if not line.strip():
            continue
        m_item = re.match(r"^\s*-\s+(.*)$", line)
        if m_item and key:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(_clean(m_item.group(1)))
            continue
        m_kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m_kv:
            key, val = m_kv.group(1), m_kv.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                data[key] = [_clean(v) for v in val[1:-1].split(",") if v.strip()]
            else:
                data[key] = _clean(val) if val else None
    return data, body


def _clean(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    if v in ("null", "~", ""):
        return None
    return v


def slugify(path_no_ext: str) -> str:
    """Та сама логіка, що й у Quartz v4 (sluggify)."""
    parts = []
    for seg in path_no_ext.split("/"):
        seg = re.sub(r"\s", "-", seg)
        seg = seg.replace("&", "-and-").replace("%", "-percent").replace("?", "").replace("#", "")
        parts.append(seg)
    return "/".join(parts)


# ── Склад альбомів з інструментами (з тексту книги) ──
INSTR_GROUP = {
    "vo": "vocal", "cho": "vocal", "voice": "vocal", "humming": "vocal",
    "p": "keys", "elp": "keys", "key": "keys", "org": "keys", "syn": "keys",
    "g": "guitar",
    "b": "bass", "elb": "bass",
    "ds": "drums", "per": "drums", "conga": "drums", "tabla": "drums", "wadaiko": "drums",
    "vib": "drums", "xylophone": "drums", "marimba": "drums", "maracas": "drums",
    "as": "reeds", "ts": "reeds", "ss": "reeds", "bs": "reeds", "cl": "reeds", "bcl": "reeds",
    "fl": "reeds", "afl": "reeds", "pic": "reeds", "piccolo": "reeds", "recorder": "reeds",
    "hca": "reeds", "lyricon": "reeds", "reed": "reeds", "reeds": "reeds", "sax": "reeds", "oboe": "reeds", "fagot": "reeds", "bassoon": "reeds",
    "tp": "brass", "tb": "brass", "btb": "brass", "vtb": "brass", "fgh": "brass", "frh": "brass",
    "tuba": "brass", "cor": "brass",
    "vln": "strings", "vin": "strings", "viola": "strings", "cello": "strings",
    "arr": "other", "com": "other", "con": "other", "effectors": "other",
}
GROUPS = [
    ("keys", "Клавішні"), ("bass", "Бас"), ("drums", "Ударні та перкусія"), ("guitar", "Гітара"),
    ("reeds", "Саксофони та дерев'яні"), ("brass", "Мідні духові"), ("strings", "Струнні"),
    ("vocal", "Вокал"), ("other", "Аранжування / інше"),
]
INSTR_UA = {"afl":"альт-флейта","arr":"аранжування","as":"альт-саксофон","b":"бас (контрабас)","bcl":"бас-кларнет","bs":"баритон-саксофон","btb":"бас-тромбон","cho":"бек-вокал (хор)","cl":"кларнет","com":"композитор","con":"диригент","ds":"ударні","elb":"бас-гітара","elp":"електропіаніно","fgh":"флюгельгорн","fl":"флейта","frh":"валторна","g":"гітара","hca":"губна гармоніка","org":"орган","p":"фортепіано","per":"перкусія","pic":"пікколо","ss":"сопрано-саксофон","syn":"синтезатор","tb":"тромбон","tp":"труба","ts":"тенор-саксофон","vib":"вібрафон","vln":"скрипка","vo":"вокал","vtb":"вентильний тромбон","cello":"віолончель","viola":"альт (віола)","key":"клавішні","conga":"конги","tabla":"табла","wadaiko":"вадайко (японський барабан)","reed":"дерев'яні духові","reeds":"дерев'яні духові","sax":"саксофон","oboe":"гобой","fagot":"фагот","bassoon":"фагот","tuba":"туба","xylophone":"ксилофон","marimba":"марімба","maracas":"маракаси","recorder":"блокфлейта","lyricon":"лірикон","voice":"голос","humming":"наспівування","effectors":"ефекти","cor":"корнет"}
_ALIAS = {"vin": "vln", "piccolo": "pic", "keys": "key", "ele": "elp"}

_ENTRY = re.compile(
    r"(?:\[\[[^\]|]+\|([^\]]+)\]\]|\[\[([^\]]+)\]\]|([A-ZА-ЯІЇЄҐ][^,()=\[\]\n:;*]*?))\s*\(([^()]*)\)")
_TRACK = re.compile(r"(?<![A-Za-zА-Яа-я])[ABCDАВСD]\s*-?\s*[①-⑳\d]+|[①-⑳]+")


def _catkey(c: str) -> str:
    """TBM-1002/3 і TBM-1002-3 — один і той самий каталожний номер."""
    return re.sub(r"\s+", "", c).replace("/", "-").upper()


def _norm(n: str) -> str:
    n = re.sub(r"^Артист — ", "", n)
    return re.sub(r"[ʼ'’`\s]+", " ", n).strip().lower().replace("ё", "е")


def _instr_tokens(raw: str):
    t = _TRACK.sub(" ", raw).lower()
    out = []
    for tok in re.split(r"[,/\s\-–]+", t):
        tok = tok.strip(". ")
        tok = _ALIAS.get(tok, tok)
        if tok in INSTR_GROUP and tok not in out:
            out.append(tok)
    return out


def find_book(v: Path):
    best, n = None, 0
    for f in v.rglob("*.md"):
        if ".obsidian" in f.parts or "_originals" in f.parts:
            continue
        try:
            c = f.read_text(encoding="utf-8").count("○ Склад")
        except Exception:
            continue
        if c > n:
            best, n = f, c
    return best


def _split_top(line: str):
    out, depth, cur = [], 0, ""
    for ch in line:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


_WIKI = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]|\[\[([^\]]+)\]\]")


def _lineup_block(block: str):
    people = {}

    def add(name, ins):
        cur = people.setdefault(name, [])
        for x in ins:
            if x not in cur:
                cur.append(x)

    for line in block.split("\n"):
        line = _WIKI.sub(lambda m: re.sub(r"^Артист — ", "", m.group(2) or m.group(3)), line)
        line = line.strip().lstrip("*").strip()
        if not line:
            continue
        arr_line = bool(re.match(r"^(Аранжування|Аранжувальник)", line))
        if "=" in line:
            line = line.rsplit("=", 1)[1]
        pending = []
        for piece in _split_top(line):
            piece = piece.split(":")[-1].strip()
            m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", piece)
            name, inner = (m.group(1).strip(), m.group(2)) if m else (piece.strip(), None)
            name = re.sub(r"\s*\([^()]*\)", "", name).strip()
            name = re.sub(r"\s*\[[^\]]*\]", "", name).strip()   # «Лео Ванда Сміт [Вадада Лео Сміт]»
            name = re.sub(r"^(?:[a-zа-яіїєґ'ʼ’]+\s+)+", "", name)   # «додається Коносуке…»
            if not re.match(r"^[A-ZА-ЯІЇЄҐ]", name) or len(name) > 40:
                pending = []
                continue
            ins = ["arr"] if arr_line else (_instr_tokens(inner) if inner is not None else [])
            if inner is None:
                pending.append(name)
                continue
            for n in pending + [name]:
                if ins:
                    add(n, ins)
            pending = []
    return list(people.items())


def parse_lineups(book: Path):
    """{catalog: [(name, [instr…]), …]} з блоків «○ Склад» у книзі."""
    text = book.read_text(encoding="utf-8")
    parts = re.split(r"^# \[\[([^\]]+)\]\]\s*$", text, flags=re.M)
    res = {}
    for i in range(1, len(parts) - 1, 2):
        cat, sec = parts[i].split("|")[0].strip(), parts[i + 1]
        m = re.search(r"○ Склад[^\n]*\n(.*?)(?=\n\s*(?:Записано|Запис |Живий запис|\*\*[^○])|\Z)", sec, re.S)
        if m:
            res[_catkey(cat)] = _lineup_block("\n".join(m.group(1).split("\n")[:30]))
    return res


WIKILINK = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]|\[\[([^\]]+)\]\]")


def strip_md(s: str) -> str:
    s = WIKILINK.sub(lambda m: m.group(2) or m.group(3), s)
    s = re.sub(r"!\[\[[^\]]*\]\]", "", s)
    s = re.sub(r"[*_`>#]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def section(body: str, title: str) -> str:
    m = re.search(rf"^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def to_int(v):
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--report", type=Path, help="записати звіт про нерозпізнані інструменти")
    args = ap.parse_args()
    v = args.vault

    # ── Артисти ──
    artists = {}
    for f in sorted((v / "Артисти").glob("*.md")):
        fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        name = fm.get("name") or f.stem.replace("Артист — ", "")
        artists[name] = {
            "instr": fm.get("instruments") or "",
            "url": slugify(f"Артисти/{f.stem}"),
        }

    # ── Liner notes ──
    liners = {}
    ln_dir = v / "Liner_Notes"
    if ln_dir.exists():
        for f in sorted(ln_dir.glob("*.md")):
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            if fm.get("type") != "liner_notes" or not fm.get("catalog"):
                continue
            liners.setdefault(fm["catalog"], []).append({
                "author": fm.get("original_author") or "",
                "translator": fm.get("translator") or "",
                "url": slugify(f"Liner_Notes/{f.stem}"),
            })

    # ── Склади з інструментами (з тексту книги) ──
    book = find_book(v)
    lineups = parse_lineups(book) if book else {}
    stat = {"albums": 0, "from_book": 0, "fallback": 0, "none": [], "no_lineup": []}

    def profile_instr(name):
        a = artists.get(name)
        return _instr_tokens(a["instr"]) if a and a.get("instr") else []

    # ── Альбоми ──
    albums = []
    for f in sorted((v / "Альбоми").glob("*.md")):
        fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        if fm.get("type") != "album":
            continue
        cat = fm.get("catalog") or f.stem
        cover = fm.get("cover")
        if cover and not (v / cover).exists():
            cover = None
        review = "\n\n".join(x for x in (strip_md(par) for par in
                  re.split(r"\n\s*\n", section(body, "Рецензія"))) if x)
        personnel = [p for p in (fm.get("personnel") or []) if p]
        book_lu = {_norm(n): ins for n, ins in lineups.get(_catkey(cat), [])}
        if _catkey(cat) not in lineups:
            stat["no_lineup"].append(cat)
        lineup = []
        for p in personnel:
            ins = book_lu.get(_norm(p))
            if ins:
                stat["from_book"] += 1
            else:
                ins = profile_instr(p)
                if ins:
                    stat["fallback"] += 1
                else:
                    stat["none"].append(f"{cat}: {p}")
            lineup.append([p, ins or []])
        albums.append({
            "id": f.stem,
            "cat": cat,
            "title": fm.get("title") or "",
            "title_ua": fm.get("title_ua") or "",
            "artist": fm.get("artist") or "",
            "artist_en": fm.get("artist_en") or "",
            "year": to_int(fm.get("year")),
            "engineer": fm.get("sound_engineer") or "",
            "awards": fm.get("awards") or "",
            "personnel": personnel,
            "lineup": lineup,
            "cover": cover,
            "review": review,
            "liner": liners.get(cat, []),
            "url": slugify(f"Альбоми/{f.stem}"),
        })

    albums.sort(key=lambda a: (a["year"] or 9999, a["cat"]))

    # ── Хронологія лейблу ──
    events = []
    chron = next((f for f in v.rglob("Хронологія*.md")
                  if ".obsidian" not in f.parts and "_originals" not in f.parts), None)
    if chron:
        _, cbody = parse_frontmatter(chron.read_text(encoding="utf-8"))
        year = label = None
        for line in cbody.split("\n"):
            m = re.match(r"^\s*(?:#+\s*)?\**\s*(\d{4})(?:\s*[~–-]\s*(\d{4}))?\s*р", line)
            if m and not re.match(r"^\s*[*-]\s", line):
                year = int(m.group(1))
                label = f"{m.group(1)}–{m.group(2)}" if m.group(2) else m.group(1)
                continue
            m = re.match(r"^\s*[*-]\s+(.*)$", line)
            if m and year:
                raw = m.group(1)
                dm = re.match(r"^\*\*(.+?):?\*\*:?\s*(.*)$", raw)
                date, text = (dm.group(1).rstrip(":"), dm.group(2)) if dm else ("", raw)
                text = strip_md(text)
                cats = re.findall(r"TBM\s?(?:\(P\))?-(?:CD-|XR-)?\d+(?:/\d+)?", text)
                events.append({"year": year, "label": label, "date": strip_md(date),
                               "text": text, "cats": [c.replace(" ", "") for c in cats]})


    # лишаємо тільки артистів, що фігурують у складах
    used = {p for a in albums for p in a["personnel"]}
    artists = {k: val for k, val in artists.items() if k in used}

    # основний інструмент і секція кожного музиканта (за кількістю альбомів)
    for name, a in artists.items():
        cnt = {}
        for al in albums:
            for n, ins in al["lineup"]:
                if n == name:
                    for x in ins:
                        cnt[x] = cnt.get(x, 0) + 1
        a["instr_count"] = cnt
        play = {k: c for k, c in cnt.items() if INSTR_GROUP.get(k) != "other"} or cnt
        main = max(play, key=lambda k: (play[k], -list(INSTR_GROUP).index(k))) if play else None
        a["main"] = main
        a["group"] = INSTR_GROUP.get(main, "other") if main else "other"

    data = {"albums": albums, "artists": artists, "events": events,
            "groups": [{"id": g, "label": l} for g, l in GROUPS],
            "instr_group": INSTR_GROUP}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"✓ data.json: {len(albums)} альбомів, {len(artists)} артистів, "
          f"{sum(len(x) for x in liners.values())} liner notes, "
          f"{sum(1 for a in albums if a['cover'])} обкладинок, {len(events)} подій хронології → {args.out}")
    tot = stat["from_book"] + stat["fallback"] + len(stat["none"])
    print(f"✓ інструменти: {stat['from_book']} з книги ({book.name if book else '—'}), "
          f"{stat['fallback']} з профілю артиста, {len(stat['none'])} без інструмента (з {tot})")
    if args.report:
        lines = ["Альбоми без блоку «○ Склад» у книзі (інструменти взято з профілів артистів):"]
        lines += [f"  {c}" for c in stat["no_lineup"]]
        lines += ["", "Музиканти без інструмента (немає ні в книзі, ні в профілі):"]
        lines += [f"  {x}" for x in stat["none"]]
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  звіт: {args.report}")


if __name__ == "__main__":
    main()

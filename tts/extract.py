#!/usr/bin/env python3
"""Generic text extractor for Lingvara course audio (any course_<c>/ folder).

Mirrors the app's tool/tts_en_texts.py (English) but reads the plain-text course sources
(brief.md format) directly, so no app code is needed here.

Usage: extract.py <course> <course_dir> <out.json>

Output: JSON list [[pack, key, spoken, voice, tempo], ...]  (same item structure as texts_en.json)
  pack : "bundle" (A0, A1, dialogs, grammar) or "<c>-<LEVEL>-<NN>" (NN = unit file number)
  key  : md5 of lowercased ("m|" if male) + text  — same as Voice.keyOf(text, male)
         For non-Latin courses (reading_parens) the "(romanization)" part is removed first.
  voice: engine voice id (langs.json voices.f / voices.m)
  tempo: 1.0 for single words, 0.92 for sentences/phrases
"""
import glob, hashlib, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{HERE}/langs.json"))
# quiz.dart tokenize() punctuation + CJK / Arabic punctuation
PUNCT = re.compile(r'^[«»"„“”()\[\].,!?:;—–…\-¿¡。、！？，；：「」『』（）・〜،؛؟]+'
                   r'|[«»"„“”()\[\].,!?:;—–…\-¿¡。、！？，；：「」『』（）・〜،؛؟]+$')
LATIN = re.compile(r"[A-Za-zÀ-ɏḀ-ỿ]")
GENDER = re.compile(r"\s*\((?:e|d|o|m|f|n|pl|m/f|f/m|m\.|f\.|çoğul)\)", re.I)
NOSPACE = {"ja", "zh"}
NONLATIN = re.compile(r"[\u0600-\u06ff\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")


def strip_reading(t):
    """'ありがとう (arigatō)' → 'ありがとう'; '早上好，老师！(Zǎoshang hǎo, lǎoshī!)' → '早上好，老师！'"""
    t = re.sub(r"\s*[(（][^()（）]*[)）]", lambda m: "" if LATIN.search(m.group(0)) else m.group(0), t)
    return re.sub(r"\s+", " ", t).strip()


def norm(text, c):
    text = text.strip()
    if CFG[c].get("reading_parens"):
        text = strip_reading(text)
    return text


def key(text, male=False):
    t = (("m|" if male else "") + text.replace("́", "").replace("`", "").strip()).lower()
    return hashlib.md5(t.encode("utf-8")).hexdigest()


def tokens(s):
    return [w for w in (PUNCT.sub("", x) for x in s.split()) if w]


def speak_text(w):
    return re.split(r"[/;,(]", w)[0].strip()


def spoken(t):
    """What the engine reads: gender markers dropped, other parentheses and slashes → short pause."""
    t = GENDER.sub("", t)
    t = re.sub(r"\s*[(（]\s*", ", ", t)
    t = re.sub(r"[)）]", "", t)
    t = re.sub(r"\s*/\s*", ", ", t)
    t = re.sub(r"\s+", " ", t).strip(" ,")
    return t


def is_word(sp, c):
    if c in NOSPACE:
        return not re.search(r"[。、！？，,.!?\s]", sp) and len(sp) <= 6
    return " " not in sp and "," not in sp


def has_letters(t):
    return bool(re.search(r"\w", t)) and not t.isdigit()


def parse_units(path):
    """Yields (unit_title, rows) from a word file; rows = 5-field lists."""
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) >= 5:
            rows.append(p)
    return rows


def unit_boundaries(path):
    """A0/01.txt holds 3 units: returns list of (unit_no, rows)."""
    units, cur = [], None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("# UNIT"):
            cur = []
            units.append(cur)
            continue
        if not line or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) >= 5:
            if cur is None:
                cur = []
                units.append(cur)
            cur.append(p)
    return list(enumerate(units, 1))


def main():
    c, cdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    cfg = CFG[c]
    vf, vm = cfg["voices"]["f"], cfg["voices"]["m"]
    males = {n.casefold() for n in cfg.get("male_names", [])}
    items, unknown = {}, Counter()

    def add(pack, text, male=False):
        male = male and vm != vf  # same voice: no separate "m|" clip, the app falls back to the plain key
        text = norm(text, c)
        if not text or not has_letters(text):
            return
        if cfg.get("reading_parens") and not NONLATIN.search(text):
            return  # bare romanization (pinyin, rōmaji…) is not spoken
        k = key(text, male)
        if k in items:
            if pack == "bundle":
                items[k][0] = "bundle"
            return
        sp = spoken(text)
        if not sp:
            return
        items[k] = [pack, k, sp, vm if male else vf, 1.0 if is_word(sp, c) else 0.92]

    levels = ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]
    for code in levels:
        for f in sorted(glob.glob(f"{cdir}/{code}/[0-9][0-9].txt")):
            nn = int(os.path.basename(f)[:2])
            pack = "bundle" if code in ("A0", "A1") else f"{c}-{code}-{nn:02d}"
            for ui, rows in (unit_boundaries(f) if code == "A0" else [(nn, parse_units(f))]):
                letter = code == "A0" and ui in (1, 2)
                for w in rows:
                    if not letter:
                        add(pack, w[0])
                        add(pack, speak_text(norm(w[0], c)))
                    add(pack, w[3])
                    for tk in tokens(norm(w[3], c)):
                        add(pack, tk)
    for f in sorted(glob.glob(f"{cdir}/dialog/*.txt")):
        spk = []
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if line.startswith("# DIALOG"):
                h = [x.strip() for x in line.split(":", 1)[1].split("|")]
                spk = h[2:4] if len(h) >= 4 else []
                continue
            if not line or line.startswith("#"):
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) < 2 or p[0] not in ("A", "B"):
                continue
            who = 0 if p[0] == "A" else 1
            name = spk[who] if who < len(spk) else ""
            male = name.casefold() in males
            if name and not male:
                unknown[name] += 1
            add("bundle", p[1], male)
    for f in sorted(glob.glob(f"{cdir}/grammar/*.txt")):
        for line in open(f, encoding="utf-8"):
            if line.startswith("="):
                add("bundle", line[1:].split("|")[0])
    res = sorted(items.values(), key=lambda x: (x[0], x[1]))
    json.dump(res, open(out, "w"), ensure_ascii=False)
    cnt = Counter(x[0].split("-")[1] if x[0] != "bundle" else "bundle" for x in res)
    print(c, len(res), dict(sorted(cnt.items())), "male", sum(x[3] == vm and vm != vf for x in res))
    print("speakers treated as female (add to male_names in langs.json if male):", dict(unknown))


if __name__ == "__main__":
    main()


def END_OK(t):
    return bool(re.search(r"[.!?。！？؟]$", t))

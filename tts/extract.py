#!/usr/bin/env python3
"""Generic text extractor for Lingvara course audio — reads course_<c>/ text sources (brief.md format).

Port of the app's reference generator tool/audio_texts.py (contract: docs/AUDIO-LAYOUT.md in the app repo).
Key rule, packs and text splitting must stay identical to it.

Usage: extract.py <course> <course_dir> <out.json>

Output: JSON list [[pack, key, spoken, voice, tempo], ...]
  pack : "<c>-<LEVEL>-<NN>"  NN = unit number within the level (01…, counted over '# UNIT' headers in
         sorted files, like the app's content builder); NN=00 = that level's dialog lines + grammar examples
         (A0-00 also holds the app's fixed phrases from app_phrases.json)
  key  : md5 per AUDIO-LAYOUT §4 (male dialog lines: "m|" prefix)
  voice: langs.json voices.f / voices.m ; tempo: 1.0 single word, 0.92 otherwise
The same text may appear in several packs (each level is self-contained); unique within a pack.
Also writes <out>.male.json: speaker names recorded with the male voice (manifest "_male").
"""
import glob, hashlib, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{HERE}/langs.json"))

READING_COURSES = {"ja", "ko", "zh", "ar"}
NATIVE = re.compile("[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿ᄀ-ᇿ぀-ヿ"
                    "㄰-㆏㐀-䶿一-鿿가-힯豈-﫿]")
PAREN = re.compile(r"\s*[(（]([^()（）]*)[)）]")
_P = "«»\"„“”()\\[\\].,!?:;—–…\\-،؛؟。、，！？：；「」『』《》"
PUNCT = re.compile(f"^[{_P}]+|[{_P}]+$")
GENDER = re.compile(r"\s*\((?:e|d|o|m|f|n|pl|m/f|f/m|m\.|f\.|çoğul)\)", re.I)
NOSPACE = {"ja", "zh"}
LEVELS = ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]


def strip_reading(s, course):
    if course not in READING_COURSES:
        return s
    return PAREN.sub(lambda m: m.group(0) if NATIVE.search(m.group(1)) else "", s).strip()


def key(text, course, male=False):
    t = strip_reading(text.replace("́", "").replace("`", ""), course).strip()
    t = (("m|" if male else "") + t).replace("İ", "i").lower()
    return hashlib.md5(t.encode("utf-8")).hexdigest()


def tokens(s, course):
    return [w for w in (PUNCT.sub("", x) for x in strip_reading(s, course).split()) if w]


def speak_text(w):
    return re.split(r"[/;,(（]", w)[0].strip()


def spoken(text, course):
    """TTS input (audio_texts.spoken) + gender markers like 'novo (e)' dropped (key unaffected)."""
    t = strip_reading(text.replace("́", "").replace("`", ""), course)
    t = GENDER.sub("", t)
    t = re.sub(r"\s*[(（]\s*", ", ", t).replace(")", "").replace("）", "")
    t = re.sub(r"\s*/\s*", ", ", t)
    return re.sub(r"\s+", " ", t).strip(" ,")


def is_word(sp, c):
    if c in NOSPACE:
        return not re.search(r"[。、！？，,.!?\s]", sp) and len(sp) <= 6
    return " " not in sp and "," not in sp


def END_OK(t):
    return bool(re.search(r"[.!?。！？؟]$", t))


def level_units(cdir, code):
    """Units of a level as the app's build_content.py builds them: every '# UNIT' in sorted files."""
    units = []
    for f in sorted(glob.glob(f"{cdir}/{code}/*.txt")):
        unit = None
        for line in open(f, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if line.startswith("# UNIT:"):
                unit = []
                units.append(unit)
                continue
            if line.startswith("#"):
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) != 5 or unit is None:
                continue
            unit.append(p)
    return units


def collect(c, cdir):
    cfg = CFG[c]
    male_names = set(cfg.get("male_names", [])) if cfg["voices"]["m"] != cfg["voices"]["f"] else set()
    packs, used_male, other = {}, set(), Counter()

    def add(pack, text, male=False):
        text = (text or "").strip()
        if not text or not re.search(r"\w", strip_reading(text, c)):
            return
        k = key(text, c, male)
        packs.setdefault(pack, {}).setdefault(k, [pack, k, spoken(text, c), male])

    for code in LEVELS:
        for ui, rows in enumerate(level_units(cdir, code), 1):
            pack = f"{c}-{code}-{ui:02d}"
            for w in rows:
                if not (code == "A0" and ui in (1, 2)):
                    add(pack, w[0])
                    add(pack, speak_text(w[0]))
                else:
                    add(pack, speak_text(w[3]))
                add(pack, w[3])
                for tk in tokens(w[3], c):
                    add(pack, tk)
    for f in sorted(glob.glob(f"{cdir}/dialog/*.txt")):
        code = os.path.splitext(os.path.basename(f))[0]
        spk = []
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if line.startswith("# DIALOG:"):
                h = [x.strip() for x in line[9:].split("|")]
                spk = h[2:4] if len(h) >= 4 else []
                continue
            if not line or line.startswith("#"):
                continue
            p = [x.strip() for x in line.split("|")]
            if len(p) < 2 or p[0] not in ("A", "B"):
                continue
            who = 0 if p[0] == "A" else 1
            name = spk[who] if who < len(spk) else ""
            male = name in male_names
            (used_male.add(name) if male else other.update([name]))
            add(f"{c}-{code}-00", p[1], male)
    for f in sorted(glob.glob(f"{cdir}/grammar/*.txt")):
        code = os.path.splitext(os.path.basename(f))[0]
        for line in open(f, encoding="utf-8"):
            if line.startswith("="):
                add(f"{c}-{code}-00", line[1:].split("|")[0])
    try:
        for t in json.load(open(f"{HERE}/app_phrases.json"))[c]:
            add(f"{c}-A0-00", t)
    except (FileNotFoundError, KeyError):
        pass
    vf, vm = cfg["voices"]["f"], cfg["voices"]["m"]
    res, skipped = [], 0
    for p in sorted(packs):
        for pack, k, sp, male in sorted(packs[p].values(), key=lambda x: x[1]):
            if c in READING_COURSES and not NATIVE.search(sp):
                skipped += 1  # bare romanization (pinyin/rōmaji/…): TTS can't read it; app falls back to phone TTS
                continue
            if sp:
                res.append([pack, k, sp, vm if male else vf, 1.0 if is_word(sp, c) else 0.92])
    if skipped:
        print(f"skipped {skipped} romanization-only texts")
    return res, sorted(used_male), other


def main():
    c, cdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    res, males, other = collect(c, cdir)
    json.dump(res, open(out, "w"), ensure_ascii=False)
    json.dump(males, open(out + ".male.json", "w"), ensure_ascii=False)
    cnt = Counter(x[0].split("-")[1] for x in res)
    print(c, len(res), "items,", len({x[1] for x in res}), "unique keys,", len({x[0] for x in res}), "packs",
          dict(sorted(cnt.items())), "male lines", sum(1 for x in res if x[3] == CFG[c]["voices"]["m"]
                                                     and CFG[c]["voices"]["m"] != CFG[c]["voices"]["f"]))
    print("male voice speakers:", males, "| other speakers (female voice):", dict(other))


if __name__ == "__main__":
    main()

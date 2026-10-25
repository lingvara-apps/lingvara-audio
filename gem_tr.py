#!/usr/bin/env python3
"""Kurs kelime dosyalarını Gemini ile arayüz dillerine çevirir. Kullanım: gem_tr.py en|es
en: src/ → out/<dil>/ ; es: course_es/ → out_es/<dil>/. Hazır ve denetimden geçen dosyalar atlanır."""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gem_common import call, out_of_time  # noqa: E402

C = sys.argv[1]
SRC, OUT = ("src", "out") if C == "en" else (f"course_{C}", f"out_{C}")
CNAME = {"en": "English", "es": "Spanish", "de": "German", "fr": "French", "it": "Italian", "pt": "Brazilian Portuguese",
         "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "ar": "Arabic", "tr": "Turkish"}[C]
ORDER = [l for l in ["en", "de", "es", "fr", "pt", "ru", "zh", "id", "az", "ar", "hi", "uz", "kk", "ky"] if l != C]
_sh, _n = (int(x) for x in os.environ.get("SHARD", "0/1").split("/"))
ORDER = ORDER[_sh::_n]
LANGS = {
    "en": "English (neutral international English)",
    "de": "German (informal 'du', nouns capitalised)", "es": "Spanish (neutral, 'tú')",
    "fr": "French ('tu'; French typography: space before ? ! : ;)", "pt": "Brazilian Portuguese ('você')",
    "ru": "Russian ('ты'; no stress marks)", "zh": "Simplified Chinese (Mainland; Chinese punctuation)",
    "id": "Indonesian ('kamu')", "az": "Azerbaijani (Latin script; real Azerbaijani forms, NOT Turkish)",
    "ar": "Modern Standard Arabic (Arabic punctuation)", "hi": "Hindi (Devanagari; 'तुम')",
    "uz": "Uzbek (Latin script; use ʻ U+02BB in oʻ gʻ and ʼ U+02BC for the apostrophe)",
    "kk": "Kazakh (Cyrillic)", "ky": "Kyrgyz (Cyrillic)",
}
RULES = open("rules.md", encoding="utf-8").read().replace("English course", f"{CNAME} course").replace(
    "English headword", f"{CNAME} headword").replace("English example", f"{CNAME} example")


def lines(p):
    return [l.rstrip("\n") for l in open(p, encoding="utf-8") if l.strip()]


def norm(s):
    return s.replace("`", "").strip().lower()


def check(src, out, lang):
    errs = []
    s, o = lines(src), [l for l in out.splitlines() if l.strip()]
    if len(s) != len(o):
        errs.append(f"line count {len(o)} but source has {len(s)}")
    for i, (a, b) in enumerate(zip(s, o), 1):
        if a.startswith("# UNIT:") or a.startswith("##"):
            if a.startswith("# UNIT:") != b.startswith("# UNIT:") or a.startswith("##") != b.startswith("##"):
                errs.append(f"line {i}: header line type differs")
            elif a.startswith("# UNIT:") and b.count("|") != 1:
                errs.append(f"line {i}: UNIT line must be '# UNIT: title | subtitle'")
            continue
        fb = b.split("|")
        if len(fb) != 3:
            errs.append(f"line {i}: must have exactly 3 fields separated by |, has {len(fb)}")
            continue
        if norm(a.split("|")[0]) != norm(fb[0]):
            errs.append(f"line {i}: column 1 must be exactly '{a.split('|')[0].strip()}'")
        if not fb[1].strip() or not fb[2].strip():
            errs.append(f"line {i}: empty field")
        txt = fb[1] + fb[2]
        if lang in ("de", "es", "id", "uz", "en") and re.search(r"[çğışİŞĞÇ]", txt):
            errs.append(f"line {i}: Turkish letters left")
        if lang in ("pt", "fr") and re.search(r"[ğışİŞĞ]", txt):
            errs.append(f"line {i}: Turkish letters left")
        if lang in ("ru", "kk", "ky") and not re.search(r"[а-яёәіңғүұқөһА-Я]", txt):
            errs.append(f"line {i}: no Cyrillic")
        if lang == "hi" and not re.search(r"[ऀ-ॿ]", txt):
            errs.append(f"line {i}: no Devanagari")
        if lang == "ar" and not re.search(r"[؀-ۿ]", txt):
            errs.append(f"line {i}: no Arabic script")
        if lang == "zh" and not re.search(r"[一-鿿]", txt):
            errs.append(f"line {i}: no Chinese characters")
    return errs


def build_prompt(lang, src_text, example, errors=None, prev=None):
    p = f"{RULES}\n\nTARGET LANGUAGE: {LANGS[lang]}\n\n"
    if example:
        p += f"STYLE EXAMPLE (an already finished overlay in this language, other unit):\n{example}\n\n"
    p += f"SOURCE FILE (translate this one):\n{src_text}\n\n"
    if errors:
        p += ("Your previous answer had these problems, fix them and output the WHOLE file again:\n- "
              + "\n- ".join(errors[:30]) + "\n\nPrevious answer:\n" + (prev or "") + "\n\n")
    return p + "Output ONLY the overlay file text, line by line, no code fences, no comments."


def main():
    files = sorted(os.path.relpath(p, SRC)[:-4] for p in glob.glob(f"{SRC}/[ABC][0-2]/*.txt"))
    done = 0
    for lang in ORDER:
        for f in files:
            op = f"{OUT}/{lang}/{f}.txt"
            if os.path.exists(op) and not check(f"{SRC}/{f}.txt", open(op, encoding="utf-8").read(), lang):
                continue
            if out_of_time():
                print("süre/sınır doldu, çevrilen:", done, flush=True)
                return
            src = open(f"{SRC}/{f}.txt", encoding="utf-8").read()
            ex = sorted(glob.glob(f"{OUT}/{lang}/A1/*.txt")) or sorted(glob.glob(f"{OUT}/{lang}/*/*.txt"))
            example = "\n".join(open(ex[0], encoding="utf-8").read().splitlines()[:25]) if ex else ""
            text, errs = None, None
            for attempt in range(3):
                out = call(build_prompt(lang, src, example, errs, text))
                if out is None:
                    break
                text = re.sub(r"^```\w*\n|```\s*$", "", out.strip()).strip() + "\n"
                errs = check(f"{SRC}/{f}.txt", text, lang)
                if not errs:
                    break
            if text and not errs:
                os.makedirs(os.path.dirname(op), exist_ok=True)
                open(op, "w", encoding="utf-8").write(text)
                done += 1
                print(f"OK {C} {lang} {f}", flush=True)
            elif text:
                print(f"BAŞARISIZ {C} {lang} {f}: {errs[:2]}", flush=True)
    print("bitti, çevrilen:", done, flush=True)


main()

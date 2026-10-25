#!/usr/bin/env python3
"""Yeni kursun (ör. es) kelime, diyalog ve gramer dosyalarını Gemini ile yazar. Kullanım: gem_course.py es
Kaynak: brief.md (yazım kılavuzu), syllabus_<kurs>.txt (ünite listesi). Çıktı: course_<kurs>/..."""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gem_common import call, out_of_time  # noqa: E402

C = sys.argv[1]
NAME = {"es": "Spanish (İspanyolca)", "de": "German (Almanca)", "fr": "French (Fransızca)", "it": "Italian (İtalyanca)", "pt": "Brazilian Portuguese (Portekizce)", "ja": "Japanese (Japonca)",
        "ko": "Korean (Korece)", "zh": "Mandarin Chinese, simplified (Çince)", "tr": "Turkish (Türkçe)", "ar": "Modern Standard Arabic (Arapça)"}[C]
D = f"course_{C}"
BRIEF = open("brief.md", encoding="utf-8").read()
# Türkçe kursu dünyaya Türkçe öğretir: anlamlar, çeviriler ve başlıklar İngilizce.
ML = "English" if C == "tr" else "Turkish"
WHO = ("learners worldwide (ALL meanings, translations, unit/lesson titles and explanations in ENGLISH)" if C == "tr"
       else "Turkish-speaking learners")
POS = {"isim", "isim (e)", "isim (d)", "isim (o)", "isim (çoğul)", "fiil", "fiil · düzensiz", "fiil · dönüşlü", "sıfat", "zarf",
       "zamir", "edat", "bağlaç", "ünlem", "ifade", "deyim", "atasözü", "sayı", "phrasal verb", "harf · sesli", "harf · ünsüz", "ses"}


def key(w):
    return re.sub(r"\s*\(.*?\)", "", w).strip().lower()


def used_words(skip=None):
    s = set()
    for root, _, fs in os.walk(D):
        for f in fs:
            p = os.path.join(root, f)
            if p == skip or "/dialog" in p or "/grammar" in p:
                continue
            for l in open(p, encoding="utf-8"):
                if l.strip() and not l.startswith("#"):
                    s.add(key(l.split("|")[0]))
    return s


def check_words(text, used, want=10):
    errs, lessons, n, seen = [], 0, 0, set()
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines or not lines[0].startswith("# UNIT:"):
        errs.append("first line must be '# UNIT: title | subtitle'")
    cur = 0
    for i, l in enumerate(lines, 1):
        if l.startswith("# UNIT:"):
            continue
        if l.startswith("##"):
            if lessons and cur != 10:
                errs.append(f"lesson ending before line {i} has {cur} lines, must be exactly 10")
            lessons += 1
            cur = 0
            continue
        f = [x.strip() for x in l.split("|")]
        cur += 1
        n += 1
        if len(f) != 5:
            errs.append(f"line {i}: needs exactly 5 fields, has {len(f)}")
            continue
        if any(not x for x in f):
            errs.append(f"line {i}: empty field")
        if f[2] not in POS:
            errs.append(f"line {i}: part of speech '{f[2]}' not allowed (allowed: {', '.join(sorted(POS))})")
        k = key(f[0])
        if want == 10 and (k in used or k in seen):
            errs.append(f"line {i}: '{f[0]}' already used elsewhere in the course — choose another word")
        seen.add(k)
    if lessons and cur != 10:
        errs.append(f"last lesson has {cur} lines, must be exactly 10")
    if lessons != want:
        errs.append(f"file has {lessons} lessons, must be exactly {want}")
    return errs


def write_words(path, title, want=10):
    used = used_words(skip=path)
    sp = "course_es/A0/01.txt" if want == 12 else (f"{D}/A1/01.txt" if os.path.exists(f"{D}/A1/01.txt") else "course_es/A1/01.txt")
    sample = open(sp, encoding="utf-8").read()[:2500] if os.path.exists(sp) else ""
    lv = path.split("/")[-2]
    base = (f"{BRIEF}\n\nYou write the {NAME} course for {WHO}. Write ONE word file now.\n"
            f"File: {lv}/{os.path.basename(path)} — unit: {title}\nLevel: {lv}.\n"
            f"Exactly {want} lessons (## title) × 10 word lines. Words must NOT be any of these already used headwords:\n"
            f"{', '.join(sorted(used))}\n\nFormat example (other unit):\n{sample}\n\n"
            "Output ONLY the file text. No code fences.")
    text, errs = None, None
    for attempt in range(3):
        p = base if not errs else base + "\n\nYour previous answer had problems; fix them and output the whole file again:\n- " + "\n- ".join(errs[:30]) + "\n\nPrevious answer:\n" + text
        out = call(p)
        if out is None:
            return False
        text = re.sub(r"^```\w*\n|```\s*$", "", out.strip()).strip() + "\n"
        errs = check_words(text, used, want)
        if not errs:
            break
        print(f"{path}: deneme {attempt+1}, {len(errs)} hata", flush=True)
    if errs:
        # Küçük hatalar (ör. 1–2 tekrar eden kelime) varsa dosyayı yine de kaydetme; sonraki çalıştırmada tekrar denenir.
        print(f"BAŞARISIZ {path}: {errs[:3]}", flush=True)
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)
    print("OK", path, flush=True)
    return True


def write_other(kind, lv):
    path = f"{D}/{kind}/{lv}.txt"
    if os.path.exists(path):
        return
    vocab = ""
    vp = sorted(os.listdir(f"{D}/{lv}")) if os.path.isdir(f"{D}/{lv}") else []
    for f in vp[:3]:
        vocab += open(f"{D}/{lv}/{f}", encoding="utf-8").read()[:1500]
    want = (f"dialog file: '# DIALOG: {ML} title | {ML} subtitle | Speaker1 | Speaker2', then exactly 4 parts "
            f"('## {ML} part title'), each part exactly 10 lines 'A | target-language sentence | {ML} translation' (A/B alternate)."
            if kind == "dialog" else
            f"grammar file: exactly {4 if lv == 'A0' else 6} topics, each: '# TOPIC: {ML} title | short target-language examples', "
            f"1–3 explanation lines starting with '>', at least 3 example lines '= target-language example | {ML} translation', "
            f"exactly 5 question lines '? {ML} question or gapped sentence | CORRECT | wrong | wrong' (first option correct, all different).")
    prompt = (f"{BRIEF}\n\nYou write the {NAME} course for {WHO}. Write the {lv} {want}\n"
              f"Level {lv}. Vocabulary of this level for reference:\n{vocab}\n\nOutput ONLY the file text. No code fences.")
    out = call(prompt)
    if out:
        text = re.sub(r"^```\w*\n|```\s*$", "", out.strip()).strip() + "\n"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(text)
        print("OK", path, flush=True)


def main():
    a0 = f"{D}/A0/01.txt"
    if not os.path.exists(a0) and not out_of_time():
        # A0: 3 ünite (alfabe/yazı, zor sesler, ilk kelimeler) = 12 ders; ayrıntı kılavuzun A0 bölümünde.
        write_words(a0, "A0 — alphabet/script, difficult sounds, first words (follow the A0 section of the guide; 3 '# UNIT:' blocks)", 12)
    for line in open(f"syllabus_{C}.txt", encoding="utf-8"):
        m = re.match(r"- ([A-C][0-2])/(\d\d)\.txt — (.+)", line.strip())
        if not m:
            continue
        path = f"{D}/{m.group(1)}/{m.group(2)}.txt"
        if os.path.exists(path):
            continue
        if out_of_time():
            return
        write_words(path, m.group(3))
    for lv in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]:
        for kind in ("dialog", "grammar"):
            if out_of_time():
                return
            write_other(kind, lv)


main()

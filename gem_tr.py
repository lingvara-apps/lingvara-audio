#!/usr/bin/env python3
"""İngilizce kursun kelime dosyalarını Gemini ile 13 dile çevirir (GitHub Actions'ta).
Girdi: src/<LV>/<NN>.txt (İngilizce kurs kaynağı), out/<lang>/<LV>/<NN>.txt (hazır olanlar atlanır).
Anahtarlar GEMINI_KEYS (virgülle). Günlük sınır dolunca durur; bir sonraki çalıştırma kaldığı yerden devam eder."""
import json, os, re, sys, time, glob
import requests

KEYS = [k.strip() for k in os.environ.get("GKEYS", "").split(",") if k.strip()]
MODELS = os.environ.get("GMODELS", "gemini-3.8-flash").split(",")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
DEADLINE = time.time() + float(os.environ.get("MAXMIN", "330")) * 60
ORDER = ["de", "es", "fr", "pt", "ru", "zh", "id", "az", "ar", "hi", "uz", "kk", "ky"]
LANGS = {
    "de": "German (informal 'du', nouns capitalised)", "es": "Spanish (neutral, 'tú'; give Latin-American variant in brackets only when very different)",
    "fr": "French ('tu'; French typography: space before ? ! : ;)", "pt": "Brazilian Portuguese ('você')",
    "ru": "Russian ('ты'; no stress marks)", "zh": "Simplified Chinese (Mainland; Chinese punctuation)",
    "id": "Indonesian ('kamu')", "az": "Azerbaijani (Latin script; real Azerbaijani forms, NOT Turkish)",
    "ar": "Modern Standard Arabic (Arabic punctuation)", "hi": "Hindi (Devanagari; 'तुम')",
    "uz": "Uzbek (Latin script; use ʻ U+02BB in oʻ gʻ and ʼ U+02BC for the apostrophe)",
    "kk": "Kazakh (Cyrillic)", "ky": "Kyrgyz (Cyrillic)",
}
RULES = open(os.path.join(os.path.dirname(__file__), "rules.md"), encoding="utf-8").read()
dead = set()  # (anahtar, model) günlük sınırı dolmuş


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
        if lang in ("de", "es", "id", "uz") and re.search(r"[çğışİŞĞÇ]", txt):
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


def call(prompt):
    # Dakikalık sınırda bekleme yerine sıradaki anahtara geçilir; hepsi doluysa kısa bekleme.
    for rnd in range(6):
        for k in KEYS:
            for m in MODELS:
                if (k, m) in dead:
                    continue
                try:
                    r = requests.post(URL.format(m=m), headers={"x-goog-api-key": k, "Content-Type": "application/json"},
                                      json={"contents": [{"parts": [{"text": prompt}]}],
                                            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 32768}},
                                      timeout=300)
                except Exception as e:  # noqa: BLE001
                    print("ağ hatası", type(e).__name__, flush=True)
                    continue
                if r.status_code == 200:
                    try:
                        parts = r.json()["candidates"][0]["content"]["parts"]
                        return "".join(p.get("text", "") for p in parts if not p.get("thought"))
                    except Exception:  # noqa: BLE001
                        print("boş yanıt", flush=True)
                        continue
                if r.status_code == 429:
                    if "PerDay" in r.text or "per day" in r.text.lower():
                        print(f"günlük sınır: anahtar #{KEYS.index(k)+1} {m}", flush=True)
                        dead.add((k, m))
                    continue
                print(f"HTTP {r.status_code} anahtar #{KEYS.index(k)+1}: {r.text[:200]}", flush=True)
                if r.status_code in (400, 401, 403, 404):
                    dead.add((k, m))
        if len(dead) >= len(KEYS) * len(MODELS):
            return None
        time.sleep(30)
    return None


def build_prompt(lang, src_text, example, errors=None, prev=None):
    p = (f"{RULES}\n\nTARGET LANGUAGE: {LANGS[lang]}\n\n")
    if example:
        p += f"STYLE EXAMPLE (an already finished overlay in this language, other unit):\n{example}\n\n"
    p += f"SOURCE FILE (translate this one):\n{src_text}\n\n"
    if errors:
        p += ("Your previous answer had these problems, fix them and output the WHOLE file again:\n- "
              + "\n- ".join(errors[:30]) + "\n\nPrevious answer:\n" + (prev or "") + "\n\n")
    p += "Output ONLY the overlay file text, line by line, no code fences, no comments."
    return p


def main():
    jobs = json.load(open("jobs.json"))
    todo = []
    for lang in ORDER:
        for f in jobs.get(lang, []):
            op = f"out/{lang}/{f}.txt"
            if os.path.exists(op) and not check(f"src/{f}.txt", open(op, encoding="utf-8").read(), lang):
                continue
            todo.append((lang, f))
    print("yapılacak dosya:", len(todo), flush=True)
    done = 0
    for lang, f in todo:
        if time.time() > DEADLINE:
            print("süre doldu", flush=True)
            break
        if len(dead) >= len(KEYS) * len(MODELS):
            print("tüm anahtarların günlük sınırı doldu", flush=True)
            break
        src = open(f"src/{f}.txt", encoding="utf-8").read()
        ex = sorted(glob.glob(f"out/{lang}/A1/*.txt")) or sorted(glob.glob(f"out/{lang}/*/*.txt"))
        example = "\n".join(open(ex[0], encoding="utf-8").read().splitlines()[:25]) if ex else ""
        text, errs = None, None
        for attempt in range(3):
            out = call(build_prompt(lang, src, example, errs, text))
            if out is None:
                break
            out = re.sub(r"^```\w*\n|```\s*$", "", out.strip()).strip() + "\n"
            text = out
            errs = check(f"src/{f}.txt", out, lang)
            if not errs:
                break
            print(f"{lang} {f}: deneme {attempt+1}, {len(errs)} hata", flush=True)
        if text and not errs:
            os.makedirs(os.path.dirname(f"out/{lang}/{f}.txt"), exist_ok=True)
            open(f"out/{lang}/{f}.txt", "w", encoding="utf-8").write(text)
            done += 1
            print(f"OK {lang} {f} ({done})", flush=True)
        elif text is None:
            continue
        else:
            print(f"BAŞARISIZ {lang} {f}: {errs[:3]}", flush=True)
    print("bitti:", done, flush=True)


main()

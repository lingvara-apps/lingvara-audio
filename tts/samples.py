#!/usr/bin/env python3
"""Sample clips + Whisper intelligibility check for one course.

Usage: samples.py <course> [course_dir]
Writes samples/<c>/candidates/<engine>_<voice>_<id>.mp3, samples/<c>/<id>.mp3 (configured voices),
samples/<c>/report.txt (Whisper CER per candidate).
"""
import json, os, random, re, sys, time, traceback, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engines, extract  # noqa: E402

CFG = json.load(open(f"{HERE}/langs.json"))

WRITTEN = {
    "fr": (["la maison", "bonjour"], ["Je voudrais un café, s'il vous plaît.", "Nous allons au marché samedi matin."],
           ["Bonjour, je m'appelle Lucas. Et toi ?", "Je travaille dans une banque à Lyon depuis deux ans."]),
    "de": ([], [], ["Guten Tag, ich heiße Lukas. Und du?", "Ich arbeite seit zwei Jahren in einer Bank in Berlin."]),
    "it": ([], [], ["Ciao, mi chiamo Marco. E tu?", "Lavoro in un ristorante vicino alla stazione."]),
    "pt": ([], ["Eu gosto muito de café com leite.", "Amanhã vamos à praia com os nossos amigos."],
           ["Oi, eu me chamo Pedro. E você?", "Eu trabalho num hospital em São Paulo."]),
    "ja": ([], ["今日はいい天気ですね。", "駅までどうやって行きますか？"],
           ["はじめまして、ケンジです。よろしくお願いします。", "私は東京の会社で働いています。"]),
    "zh": (["谢谢", "朋友"], ["今天天气很好。", "请问，火车站在哪里？"], ["你好，我叫李明。你呢？", "我在北京的一家公司工作。"]),
    "ko": (["감사합니다", "학교"], ["오늘 날씨가 정말 좋네요.", "지하철역이 어디에 있어요?"],
           ["안녕하세요, 저는 민호예요.", "저는 서울에 있는 회사에서 일해요."]),
    "tr": (["teşekkürler", "kitap"], ["Bugün hava çok güzel.", "İstasyona nasıl gidebilirim?"],
           ["Merhaba, benim adım Emre. Senin adın ne?", "Ben İstanbul'da bir bankada çalışıyorum."]),
    "ar": (["شُكْرًا", "كِتَابٌ"], ["اَلْجَوُّ جَمِيلٌ اَلْيَوْمَ.", "أين محطة القطار؟"],
           ["مَرْحَبًا، اِسْمِي عُمَرُ.", "أَعْمَلُ فِي شَرِكَةٍ كَبِيرَةٍ فِي عَمَّانَ."]),
}

ST = ["F1", "F2", "F3", "M1", "M2", "M3"]
CANDIDATES = {
    "es": [("kokoro", v) for v in ["ef_dora", "em_alex", "em_santa"]] + [("supertonic", v) for v in ST],
    "fr": [("kokoro", "ff_siwis"), ("kokoro", "ff_siwis@0.84")] + [("supertonic", v) for v in ST],
    "it": [("kokoro", v) for v in ["if_sara", "im_nicola"]] + [("supertonic", v) for v in ST],
    "pt": [("kokoro", v) for v in ["pf_dora", "pm_alex", "pm_santa"]] + [("supertonic", v) for v in ST],
    "ja": [("kokoro", v) for v in ["jf_alpha", "jf_nezumi", "jm_kumo"]] + [("supertonic", v) for v in ST],
    "zh": [("kokoro", v) for v in ["zf_xiaobei", "zf_xiaoxiao", "zf_xiaoni", "zm_yunjian", "zm_yunxi"]]
          + [("kokoro11", v) for v in ["zf_001", "zf_002", "zf_003", "zf_004", "zf_005", "zm_009", "zm_010", "zm_011"]],
    "de": [("piper", v) for v in ["de_DE-kerstin-low", "de_DE-ramona-low", "de_DE-eva_k-x_low",
                                  "de_DE-thorsten-high", "de_DE-thorsten-medium"]] + [("supertonic", v) for v in ST],
    "tr": [("piper", "auto:tr_TR")]
          + [("supertonic", v) for v in ST],
    "ar": [("piper", "auto:ar_")] + [("supertonic", v) for v in ST],
    "ko": [("supertonic", v) for v in ["F1", "F2", "F3", "F4", "F5", "M1", "M2", "M3", "M4", "M5"]],
}
NW = {"zh": 10}
WLANG = {"pt": "pt", "zh": "zh"}


def course_texts(c, cdir):
    """2 words, 2 sentences, 2 male dialog lines from the real course (written fallbacks)."""
    words, sents, male = [], [], []
    if cdir and os.path.isdir(cdir):
        tmp = f"/tmp/t_{c}.json"
        sys.argv = ["x", c, cdir, tmp]
        extract.main()
        items = json.load(open(tmp))
        rnd = random.Random(7)
        vm = CFG[c]["voices"]["m"]
        lo, hi = (6, 30) if c in ("ja", "zh") else (25, 70)
        w = [x[2] for x in items if x[4] == 1.0 and len(x[2]) > (1 if c in ("ja", "zh") else 4) and not x[2][0].isupper()]
        s = [x[2] for x in items if x[4] != 1.0 and x[3] != vm and lo <= len(x[2]) <= hi and extract.END_OK(x[2])]
        m = [x[2] for x in items if x[3] == vm and CFG[c]["voices"]["f"] != vm and 15 <= len(x[2]) <= 90]
        words = rnd.sample(w, min(NW.get(c, 2), len(w)))
        sents = rnd.sample(s, min(2, len(s)))
        male = rnd.sample(m, min(2, len(m)))
    fw, fs, fm = WRITTEN.get(c, ([], [], []))
    words = (words + fw)[:max(2, len(words))]
    sents = (sents + fs)[:2]
    male = (male + fm)[:2]
    return ([(f"w{n + 1}", x) for n, x in enumerate(words)]
            + [("s1", sents[0]), ("s2", sents[1]), ("m1", male[0]), ("m2", male[1])])


def normtxt(t, c):
    t = unicodedata.normalize("NFKC", t).lower()
    t = "".join(ch for ch in t if not unicodedata.category(ch).startswith(("P", "S", "M")))
    t = re.sub(r"\s+", " " if c not in ("ja", "zh") else "", t).strip()
    return t


def cer(a, b):
    import difflib
    if not a:
        return 1.0
    sm = difflib.SequenceMatcher(None, a, b)
    return round(1 - sm.ratio(), 3)


def main():
    c = sys.argv[1]
    cdir = sys.argv[2] if len(sys.argv) > 2 else None
    texts = course_texts(c, cdir)
    out = f"samples/{c}"
    os.makedirs(f"{out}/candidates", exist_ok=True)
    json.dump(texts, open(f"{out}/texts.json", "w"), ensure_ascii=False, indent=1)
    loaded, made, log = {}, [], []
    cands = []
    for eng, voice in CANDIDATES[c]:
        if voice.startswith("auto:"):
            import urllib.request
            vj = json.load(urllib.request.urlopen(engines.Piper.HF + "voices.json"))
            found = sorted(k for k in vj if k.startswith(voice[5:]))
            log.append(f"piper voices for {voice[5:]}: {found}")
            cands += [(eng, k) for k in found if not k.endswith("-x_low")]
        else:
            cands.append((eng, voice))
    for eng, voice in cands:
        v, _, pitch = voice.partition("@")
        try:
            if eng not in loaded:
                cfg = dict(CFG[c], engine=eng.replace("kokoro11", "kokoro"))
                cfg.pop("model", None)
                if eng == "kokoro11":
                    cfg["model"] = "v1.1-zh"
                if eng == "supertonic":
                    cfg["st_lang"] = c
                loaded[eng] = engines.load(cfg)
                if hasattr(loaded[eng], "k"):
                    log.append(f"{eng} voices: {sorted(loaded[eng].k.get_voices())}")
            e = loaded[eng]
            for tid, txt in texts:
                t0 = time.time()
                a, sr = e.synth(extract.spoken(txt, c), v)
                f = f"{out}/candidates/{eng}_{voice.replace('@', '_p')}_{tid}.mp3"
                engines.encode(a, sr, f, 1.0 if tid.startswith("w") else 0.92, float(pitch or 1))
                made.append((eng, voice, tid, txt, f, round(time.time() - t0, 2), round(len(a) / sr, 2)))
        except Exception as ex:  # noqa: BLE001
            log.append(f"FAIL {eng} {voice}: {ex!r}")
            traceback.print_exc()
    # configured voices (langs.json) → top-level picks, made exactly like the real run
    try:
        r = engines.Router(CFG[c])
        for tid, txt in texts:
            v = CFG[c]["voices"]["m" if tid.startswith("m") else "f"]
            sp = extract.spoken(txt, c)
            a, sr, p = r.synth(sp, v)
            engines.encode(a, sr, f"{out}/{tid}.mp3", 1.0 if extract.is_word(sp, c) else 0.92, p)
    except Exception as ex:  # noqa: BLE001
        log.append(f"FAIL picks: {ex!r}")
    # Whisper check
    try:
        from faster_whisper import WhisperModel
        wm = WhisperModel(os.environ.get("WHISPER", "large-v3-turbo"), device="cpu", compute_type="int8")
        lang = WLANG.get(c, c)
        res = {}
        for eng, voice, tid, txt, f, secs, dur in made:
            import subprocess, numpy as np
            pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                                 capture_output=True).stdout
            segs, _ = wm.transcribe(np.frombuffer(pcm, dtype=np.float32), language=lang, beam_size=1, vad_filter=False)
            hyp = "".join(s.text for s in segs).strip()
            ref = extract.strip_reading(txt, c)
            sc = cer(normtxt(ref, c), normtxt(hyp, c))
            res.setdefault((eng, voice), []).append(sc)
            log.append(f"{eng:10s} {voice:24s} {tid} cer={sc:.3f} synth={secs}s dur={dur}s | {ref} → {hyp}")
        log.append("== mean CER per candidate (lower = clearer to Whisper)")
        for (eng, voice), v in sorted(res.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
            log.append(f"{eng:10s} {voice:24s} {sum(v) / len(v):.3f}")
    except Exception as ex:  # noqa: BLE001
        log.append(f"whisper failed: {ex!r}")
    open(f"{out}/report.txt", "w").write("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    main()

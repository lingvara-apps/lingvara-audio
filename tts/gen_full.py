"""İngilizce seslendirme (Kokoro-82M, Apache-2.0). Kullanım: gen_full.py <parça> <toplam>"""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
import soundfile as sf
from kokoro_onnx import Kokoro

i, n = int(sys.argv[1]), int(sys.argv[2])
items = json.load(open("tts/texts_en.json"))[i::n]
k = Kokoro("kokoro.onnx", "voices.bin")
os.makedirs("out", exist_ok=True)
os.makedirs("tmp", exist_ok=True)
AF = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
      "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
      "adelay=120:all=1,apad=pad_dur=0.25,loudnorm=I=-18:TP=-2:LRA=11")


def enc(j):
    wav, mp3, tempo = j
    af = (f"atempo={tempo}," if tempo != 1.0 else "") + AF
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", af, "-ac", "1", "-ar", "24000",
                        "-c:a", "libmp3lame", "-b:a", "40k", mp3], capture_output=True, text=True)
    if r.returncode:
        print("FFMPEG", mp3, r.stderr[-200:], flush=True)
    os.remove(wav)


pool = ThreadPoolExecutor(2)
t0 = time.time()
for c, (pack, key, text, voice, tempo) in enumerate(items):
    txt = text if re.search(r"[.!?…]$", text) else text + "."
    try:
        s, sr = k.create(txt, voice=voice, speed=1.0, lang="en-gb" if voice[0] == "b" else "en-us")
    except Exception as e:  # noqa: BLE001
        print("HATA", key, text, e, flush=True)
        continue
    wav = f"tmp/{key}.wav"
    sf.write(wav, s, sr)
    pool.submit(enc, (wav, f"out/{key}.mp3", tempo))
    if c % 200 == 0:
        print(c, len(items), round(time.time() - t0), flush=True)
pool.shutdown(wait=True)
print("bitti", len(os.listdir("out")), "/", len(items), round(time.time() - t0))

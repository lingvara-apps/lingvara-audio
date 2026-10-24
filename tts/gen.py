import os, subprocess, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro("kokoro.onnx", "voices.bin")
os.makedirs("out", exist_ok=True)
voices = ["af_heart", "af_bella", "af_nicole", "am_michael", "am_fenrir", "am_puck", "bf_emma", "bm_george"]
texts = [
    ("w1", "apple."), ("w2", "neighbourhood."), ("w3", "to look forward to."),
    ("s1", "Good morning! How are you today?"),
    ("s2", "I usually take the bus to work, but today I walked."),
    ("s3", "Could you tell me where the nearest pharmacy is, please?"),
]
def mp3(wav, dst, tempo):
    af = f"atempo={tempo},adelay=120|120,apad=pad_dur=0.25,loudnorm=I=-18:TP=-1.5:LRA=11" if tempo != 1 else "adelay=120|120,apad=pad_dur=0.25,loudnorm=I=-18:TP=-1.5:LRA=11"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", af, "-ar", "24000", "-ac", "1", "-b:a", "40k", dst], check=True)
for v in voices:
    for tid, txt in texts:
        samples, sr = k.create(txt, voice=v, speed=1.0, lang="en-us" if v[0] == "a" else "en-gb")
        wav = f"out/{v}_{tid}.wav"; sf.write(wav, samples, sr)
        tempo = 1.0 if tid.startswith("w") else 0.92
        mp3(wav, f"out/{v}_{tid}.mp3", tempo); os.remove(wav)
        print("ok", v, tid, round(len(samples) / sr, 2))

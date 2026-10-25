#!/usr/bin/env python3
"""Generate clips for one shard: gen_multi.py <course> <todo.json> <shard> <shards> [outdir]
todo.json items: [pack, key, spoken, voice, tempo]; voice may carry a pitch suffix "name@0.84"."""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engines  # noqa: E402

c, todo, i, n = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
out = sys.argv[5] if len(sys.argv) > 5 else "out"
cfg = json.load(open(f"{HERE}/langs.json"))[c]
items = json.load(open(todo))[i::n]
os.makedirs(out, exist_ok=True)
eng = engines.Router(cfg)
pool = ThreadPoolExecutor(3)
errors = []


def enc(a, sr, mp3, tempo, pitch):
    try:
        engines.encode(a, sr, mp3, tempo, pitch)
    except Exception as e:  # noqa: BLE001
        errors.append(mp3)
        print("FFMPEG", mp3, e, flush=True)


t0 = time.time()
for k, (pack, key, text, voice, tempo) in enumerate(items):
    mp3 = f"{out}/{key}.mp3"
    if os.path.exists(mp3):
        continue
    try:
        a, sr, p = eng.synth(text, voice)
    except Exception as e:  # noqa: BLE001
        errors.append(key)
        print("ERR", key, text, repr(e)[:200], flush=True)
        continue
    pool.submit(enc, a, sr, mp3, tempo, p)
    if k % 250 == 0:
        print(k, len(items), round(time.time() - t0), flush=True)
pool.shutdown(wait=True)
print("done", len([f for f in os.listdir(out) if f.endswith(".mp3")]), "/", len(items), "errors", len(errors),
      round(time.time() - t0), "s")

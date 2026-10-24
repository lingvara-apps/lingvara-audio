import os, time
import requests

KEYS = [k.strip() for k in os.environ.get("GKEYS", "").split(",") if k.strip()]
MODELS = os.environ.get("GMODELS", "gemini-3.8-flash").split(",")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
DEADLINE = float(os.environ.get("DEADLINE", time.time() + 320 * 60))
dead = set()


def out_of_time():
    return time.time() > DEADLINE or len(dead) >= len(KEYS) * len(MODELS)


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
                    ids, val = [], ""
                    try:
                        for d in r.json()["error"].get("details", []):
                            for v in d.get("violations", []):
                                ids.append(v.get("quotaId", ""))
                                val = v.get("quotaValue", val)
                    except Exception:  # noqa: BLE001
                        pass
                    if any("PerDay" in i for i in ids):
                        print(f"günlük sınır: anahtar #{KEYS.index(k)+1} {m} {ids} limit={val}", flush=True)
                        dead.add((k, m))
                    else:
                        print(f"429 dakikalık: anahtar #{KEYS.index(k)+1} {ids} limit={val}", flush=True)
                    continue
                print(f"HTTP {r.status_code} anahtar #{KEYS.index(k)+1}: {r.text[:200]}", flush=True)
                if r.status_code in (400, 401, 403, 404):
                    dead.add((k, m))
        if len(dead) >= len(KEYS) * len(MODELS):
            return None
        time.sleep(30)
    return None



#!/usr/bin/env python3
"""Plan / pack steps for the multi-language audio workflow.

  pack.py plan <course> <texts.json> <old_dir> <todo.json> [force]
      old_dir holds the previous release (manifest.json + *.zip). Writes the items whose
      key has no clip yet (or all, if the engine/voice config changed or force=1).
  pack.py pack <course> <texts.json> <old_dir> <clips_dir> <out_dir>
      Merges old clips + new clips, writes one zip per pack (<c>-bundle.zip, <c>-A2-01.zip …)
      and manifest.json. Unchanged packs keep the same bytes (deterministic zips).

Manifest (same shape as the app's assets/audio/manifest.json):
  {"<c>-A2-01": {"sha256", "size", "files"}, …, "<c>-bundle": {…},
   "_files": {"A2": [keys…], …, "bundle": [keys…]}, "_cfg": {engine, voices}, "_missing": n}
"""
import glob, hashlib, json, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def cfg_sig(c):
    cfg = json.load(open(f"{HERE}/langs.json"))[c]
    return {"engine": cfg["engine"], "voices": cfg["voices"], "lang": cfg.get("lang"), "g2p": cfg.get("g2p")}


def old_manifest(old):
    try:
        return json.load(open(f"{old}/manifest.json"))
    except Exception:  # noqa: BLE001
        return {}


def old_clips(old):
    """key -> (zip path) for every clip in the previous release."""
    res = {}
    for z in sorted(glob.glob(f"{old}/*.zip")):
        try:
            for nm in zipfile.ZipFile(z).namelist():
                if nm.endswith(".mp3"):
                    res[nm[:-4]] = z
        except zipfile.BadZipFile:
            print("bad zip", z)
    return res


def plan(c, texts, old, todo, force="0"):
    items = json.load(open(texts))
    om = old_manifest(old)
    have = {} if force == "1" or om.get("_cfg") != cfg_sig(c) else old_clips(old)
    t = [x for x in items if x[1] not in have]
    json.dump(t, open(todo, "w"), ensure_ascii=False)
    print(f"{c}: {len(items)} texts, {len(items) - len(t)} already have clips, {len(t)} to generate")
    return len(t)


def write_zip(path, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        for name, data in files:
            zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, data)


def pack(c, texts, old, clips, out):
    items = json.load(open(texts))
    om = old_manifest(old)
    reuse = om.get("_cfg") == cfg_sig(c)
    prev = old_clips(old) if reuse else {}
    new = {os.path.basename(f)[:-4]: f for f in glob.glob(f"{clips}/**/*.mp3", recursive=True)}
    os.makedirs(out, exist_ok=True)
    groups = {}
    for p, k, *_ in items:
        groups.setdefault(p, []).append(k)
    man = {"_files": {}, "_cfg": cfg_sig(c)}
    missing, zcache = [], {}
    for p in sorted(groups):
        files = []
        for k in sorted(set(groups[p])):
            if k in new:
                files.append((k + ".mp3", open(new[k], "rb").read()))
            elif k in prev:
                z = zcache.setdefault(prev[k], zipfile.ZipFile(prev[k]))
                files.append((k + ".mp3", z.read(k + ".mp3")))
            else:
                missing.append(k)
        if not files:
            continue
        name = f"{c}-bundle" if p == "bundle" else p
        zp = f"{out}/{name}.zip"
        write_zip(zp, files)
        data = open(zp, "rb").read()
        man[name] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "files": len(files)}
        lvl = "bundle" if p == "bundle" else p.split("-")[1]
        man["_files"].setdefault(lvl, []).extend(f[0][:-4] for f in files)
    man["_missing"] = len(missing)
    json.dump(man, open(f"{out}/manifest.json", "w"), indent=0, sort_keys=True)
    json.dump(missing, open(f"{out}/missing.json", "w"))
    tot = sum(v["size"] for k, v in man.items() if not k.startswith("_"))
    print(f"{c}: {len(man) - 3} packs, {sum(v['files'] for k, v in man.items() if not k.startswith('_'))} clips, "
          f"{tot / 1e6:.1f} MB, missing {len(missing)}")
    for k in sorted(man):
        if not k.startswith("_"):
            print(f"  {k}: {man[k]['files']} clips {man[k]['size'] / 1e6:.2f} MB")


if __name__ == "__main__":
    {"plan": plan, "pack": pack}[sys.argv[1]](*sys.argv[2:])

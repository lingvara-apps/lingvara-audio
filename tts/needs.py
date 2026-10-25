"""Prints the install.sh components a course needs (engine, cross-engine voices, g2p)."""
import json, os, sys
c = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "langs.json")))[sys.argv[1]]
need = {c["engine"]} | {v.rpartition(":")[0] for v in c["voices"].values() if ":" in v}
if c.get("g2p"):
    need.add(c["g2p"])
print(" ".join(sorted(need)))

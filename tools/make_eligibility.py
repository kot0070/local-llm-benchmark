"""Build config/eligibility_night.json from V5_DESIGN sources.

Reads D:\\LOCAL_AI\\V5_DESIGN\\test_matrix_v5.json (key "eligibility":
{test_id: {model_key: {code, reason}}}) and
D:\\LOCAL_AI\\V5_DESIGN\\inventory_v5.json (models[].key / .local / .runtime).

Writes config/eligibility_night.json =
  {test_id: {ollama_tag: {"code": "E"|"O"|"U"|"S", "reason": str}}}
for HOME-01..HOME-24, runtime OLLAMA only, plus "_deferred" with the 12
non-Ollama models.
"""
from __future__ import annotations

import json
import os

MATRIX = r"D:\LOCAL_AI\V5_DESIGN\test_matrix_v5.json"
INVENTORY = r"D:\LOCAL_AI\V5_DESIGN\inventory_v5.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "config", "eligibility_night.json")

HOME_IDS = [f"HOME-{i:02d}" for i in range(1, 25)]


def main() -> str:
    with open(MATRIX, encoding="utf-8") as f:
        matrix = json.load(f)
    with open(INVENTORY, encoding="utf-8") as f:
        inv = json.load(f)
    elig = matrix["eligibility"]
    key_to_local: dict[str, str] = {}
    key_to_runtime: dict[str, str] = {}
    local_to_key: dict[str, str] = {}
    for m in inv["models"]:
        key_to_local[m["key"]] = m["local"]
        key_to_runtime[m["key"]] = m["runtime"]
        local_to_key[m["local"]] = m["key"]
    ollama_keys = {k for k, r in key_to_runtime.items() if r == "OLLAMA"}
    out: dict = {}
    for tid in HOME_IDS:
        src = elig.get(tid, {})
        dest: dict = {}
        for key in sorted(ollama_keys):
            tag = key_to_local[key]
            info = src.get(key, {"code": "U", "reason": "no matrix entry"})
            code = str(info.get("code", "U"))
            if code not in ("E", "O", "U", "S"):
                code = "U"
            dest[tag] = {"code": code, "reason": str(info.get("reason", ""))}
        out[tid] = dest
    deferred: dict = {}
    for m in inv["models"]:
        if m["runtime"] == "OLLAMA":
            continue
        if m["runtime"] == "LM_STUDIO":
            reason = ("LM Studio runtime not initialized "
                      "(NIGHT-1 Ollama only; reported as DEFERRED)")
        else:
            reason = ("Specialist not installed "
                      "(NIGHT-1 Ollama only; reported as DEFERRED)")
        deferred[m["local"]] = {"key": m["key"], "runtime": m["runtime"],
                                "reason": reason}
    out["_deferred"] = deferred
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    n_e = sum(1 for tid in HOME_IDS for v in out[tid].values()
              if v["code"] == "E")
    print(f"wrote {OUT}: {len(HOME_IDS)} tests, {n_e} eligible (E) pairs, "
          f"{len(deferred)} deferred")
    return OUT


if __name__ == "__main__":
    main()

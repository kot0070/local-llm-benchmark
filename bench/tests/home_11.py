"""HOME-11 English retrieval (owner: TASK_C). Uses the HOME-02 corpus."""
from __future__ import annotations

import json
import os

from bench.types import Case, Profile, Verdict

META = dict(id="HOME-11", version="n1", title="English retrieval", family="EMBED",
            home="nomic-embed-text:latest", kind="embed", mode="-", requires=["embed"],
            num_predict=0, think_extra=0, num_ctx=0, timeout_s=900,
            core_n=30, empty_ok=False)


def load_cases(fixtures_dir: str) -> list[Case]:
    path = os.path.join(fixtures_dir, "cases.jsonl")
    cases: list[Case] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            meta = d.get("meta", {}) or {}
            meta = dict(meta)
            meta["fixtures_dir"] = os.path.abspath(fixtures_dir)
            cases.append(Case(id=d["id"], test_id=d.get("test_id", "HOME-11"), tier=d.get("tier", ""),
                              lang=d.get("lang", "en"), input=d.get("input", {}),
                              expected=d.get("expected", {}), meta=meta))
    return cases


def load_corpus(fixtures_dir: str) -> list[dict]:
    # HOME-11 reuses the HOME-02 corpus.
    cand_here = os.path.join(fixtures_dir, "corpus.jsonl")
    if os.path.exists(cand_here):
        path = cand_here
    else:
        parent = os.path.dirname(os.path.abspath(fixtures_dir))
        path = os.path.join(parent, "HOME-02", "corpus.jsonl")
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def run_embed(cases: list[Case], profile: Profile, embed_fn) -> list[tuple[Case, Verdict]]:
    # Delegate to the HOME-02 implementation (same metrics, English-only queries).
    import bench.tests.home_02 as h02
    # Ensure corpus lookup works: stamp fixtures_dir into meta if missing.
    return h02.run_embed(cases, profile, embed_fn)

"""JSONL result store, run keys, resume helpers, file hashing. Stdlib only."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Iterable


def make_key(run_id: str, tag: str, digest12: str, test_id: str, ver: str,
             case_id: str, repeat: int, mode: str, profile_id: str) -> str:
    return "|".join([run_id, "OLLAMA", f"{tag}@{digest12}", f"{test_id}@{ver}",
                     str(case_id), str(repeat), str(mode), str(profile_id)])


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_tree(root: str, rel_paths: Iterable[str]) -> dict:
    """Return {rel_path: sha256} for files under root. Missing files raise."""
    out: dict = {}
    for rel in rel_paths:
        full = os.path.join(root, rel)
        out[rel] = sha256_file(full)
    return out


def collect_files(base: str, subdirs: list[str] | None = None) -> list[str]:
    """Collect relative file paths (sorted, forward slashes) under base.

    If subdirs is given, only those subdirectories (relative to base) are
    scanned; otherwise the whole tree under base is scanned.
    """
    roots = [os.path.join(base, s) for s in subdirs] if subdirs else [base]
    out: list[str] = []
    for r in roots:
        if not os.path.isdir(r):
            continue
        for dirpath, dirnames, filenames in os.walk(r):
            # volatile caches must not affect run manifests
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn.endswith((".pyc", ".pyo")):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, base).replace(os.sep, "/")
                out.append(rel)
    return sorted(out)


class Store:
    """Append-only JSONL store for one run directory."""

    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        self.path = os.path.join(run_dir, "results.jsonl")
        os.makedirs(run_dir, exist_ok=True)
        if not os.path.exists(self.path):
            open(self.path, "a", encoding="utf-8").close()

    def append(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass

    def load_all(self) -> list[dict]:
        out: list[dict] = []
        if not os.path.exists(self.path):
            return out
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def existing_keys(self) -> set[str]:
        return {r.get("key", "") for r in self.load_all() if isinstance(r, dict)}

    def records_by_key(self) -> dict[str, dict]:
        d: dict[str, dict] = {}
        for r in self.load_all():
            if isinstance(r, dict) and "key" in r:
                d[r["key"]] = r
        return d


FINAL_STATUSES = {
    "OK", "WRONG_ANSWER", "FORMAT_ERROR", "EMPTY_OUTPUT", "OUTPUT_TRUNCATED",
    "UNSUPPORTED_CAPABILITY", "MODEL_LOAD_ERROR", "OOM_GPU", "OOM_RAM",
    "TIMEOUT", "MODEL_RUNTIME_ERROR", "CONTEXT_OVERFLOW",
}


def is_final_status(status: str) -> bool:
    """Keys with these statuses are skipped on --resume.

    Ours (HARNESS_ERROR, VALIDATOR_ERROR, BLOCKED_CONTENDED, GPU_UNLOAD_FAILED)
    and NOT_RUN_BUDGET are re-run on resume per SPEC.
    """
    return status in FINAL_STATUSES


def manifest_entry(run_dir: str, record: dict, max_inline_bytes: int = 64 * 1024) -> dict:
    """Store big payloads (>64KB) externally; return possibly-modified record.

    Large response content/thinking are moved to results/<RUN_ID>/raw/<sha>.txt
    and replaced with {"$ref": sha}.
    """
    raw_dir = os.path.join(run_dir, "raw")
    for section in ("response",):
        payload = record.get(section)
        if not isinstance(payload, dict):
            continue
        for field in ("content", "thinking"):
            val = payload.get(field)
            if isinstance(val, str) and len(val.encode("utf-8")) > max_inline_bytes:
                os.makedirs(raw_dir, exist_ok=True)
                sha = sha256_text(val)
                with open(os.path.join(raw_dir, sha + ".txt"), "w", encoding="utf-8") as f:
                    f.write(val)
                payload[field] = {"$ref": sha, "chars": len(val)}
    return record

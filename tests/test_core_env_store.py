"""Core tests: store keys/hashing, env degradation, registry validation."""
import json
import os

from bench import env as envmod
from bench import registry as registrymod
from bench import store as storemod


def test_make_key_format():
    k = storemod.make_key("r1", "qwen3:1.7b", "abc123", "HOME-16", "n1",
                          "HOME-16-001", 0, "R0", "qwen3.card.v1")
    assert k == "r1|OLLAMA|qwen3:1.7b@abc123|HOME-16@n1|HOME-16-001|0|R0|qwen3.card.v1"


def test_store_append_and_resume_sets(tmp_path):
    s = storemod.Store(str(tmp_path))
    s.append({"key": "k1", "verdict": {"status": "OK"}})
    s.append({"key": "k2", "verdict": {"status": "TIMEOUT"}})
    assert s.existing_keys() == {"k1", "k2"}
    assert s.records_by_key()["k1"]["verdict"]["status"] == "OK"
    # file is valid JSONL
    with open(os.path.join(str(tmp_path), "results.jsonl"), encoding="utf-8") as f:
        assert len([ln for ln in f if ln.strip()]) == 2


def test_final_status_sets():
    assert storemod.is_final_status("OK")
    assert storemod.is_final_status("TIMEOUT")
    assert storemod.is_final_status("UNSUPPORTED_CAPABILITY")
    assert storemod.is_final_status("NOT_RUN_BUDGET") is False
    assert storemod.is_final_status("HARNESS_ERROR") is False
    assert storemod.is_final_status("VALIDATOR_ERROR") is False


def test_manifest_entry_spills_big_payloads(tmp_path):
    rec = {"response": {"content": "x" * (70 * 1024), "thinking": "small"}}
    out = storemod.manifest_entry(str(tmp_path), rec)
    ref = out["response"]["content"]
    assert isinstance(ref, dict) and "$ref" in ref
    raw_path = os.path.join(str(tmp_path), "raw", ref["$ref"] + ".txt")
    assert os.path.exists(raw_path)
    with open(raw_path, encoding="utf-8") as f:
        assert f.read() == "x" * (70 * 1024)


def test_sha256_helpers(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("abc", encoding="utf-8")
    assert storemod.sha256_file(str(p)) == storemod.sha256_text("abc")
    assert storemod.hash_tree(str(tmp_path), ["a.txt"]) == {
        "a.txt": storemod.sha256_text("abc")}


def test_env_never_crashes_without_gpu(monkeypatch):
    monkeypatch.setattr(envmod, "_run", lambda *a, **k: (False, "nope"))
    assert envmod.nvidia_snapshot() is None
    fp = envmod.fingerprint(None)
    assert fp["gpu"] == "unknown" and fp["warnings"]
    base = envmod.idle_baseline(0.01, 0.001)
    assert base["samples"] == 0
    ok, info = envmod.contention_check({"vram_baseline_mb": None}, wait_s=0.01)
    assert ok is True  # degraded -> allow run with warning
    gate = envmod.thermal_gate(None, wait_s=0.01)
    assert gate["temp_c"] is None
    assert envmod.foreign_gpu_processes() == []
    envmod.set_thread_execution_state(True)  # must not raise on any platform
    envmod.set_thread_execution_state(False)


def test_registry_discovers_and_validates(tmp_path):
    good = ("META = dict(id='HOME-90', home='m', family='F', kind='chat', "
            "mode='R0', core_n=2, timeout_s=60)\n"
            "def build_request(case, profile):\n    return None\n"
            "def validate(case, resp, profile):\n    return None\n")
    (tmp_path / "home_90.py").write_text(good, encoding="utf-8")
    mods = registrymod.discover(str(tmp_path))
    assert list(mods) == ["HOME-90"]
    assert registrymod.home_model_map(mods) == {"m": "HOME-90"}


def test_registry_rejects_bad_meta(tmp_path):
    import pytest
    (tmp_path / "home_91.py").write_text("META = dict(id='HOME-91')\n",
                                         encoding="utf-8")
    with pytest.raises(ValueError):
        registrymod.discover(str(tmp_path))


def test_registry_rejects_duplicate(tmp_path):
    import pytest
    body = ("META = dict(id='HOME-90', home='m', family='F', kind='chat', "
            "mode='R0', core_n=2, timeout_s=60)\n"
            "def build_request(case, profile):\n    return None\n"
            "def validate(case, resp, profile):\n    return None\n")
    (tmp_path / "home_90.py").write_text(body, encoding="utf-8")
    (tmp_path / "home_91.py").write_text(body.replace("home_90", "home_91"),
                                         encoding="utf-8")
    with pytest.raises(ValueError):
        registrymod.discover(str(tmp_path))

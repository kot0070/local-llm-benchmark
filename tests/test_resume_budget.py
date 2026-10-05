"""--resume must re-run NOT_RUN_BUDGET / ours records, even after done_keys refresh.

Regression test for FIX_RESUME_BUG: bench/runner.py refreshed `done_keys`
with the unfiltered `store.existing_keys()` in three places, destroying the
--resume filter computed at startup. Uses a synthetic Store on tmp_path
(no Ollama, no generators, no results/* writes).
"""
from bench import runner as runmod
from bench import store as storemod


def _rec(key, status):
    return {"key": key, "verdict": {"status": status}}


def _seed(tmp_path):
    store = storemod.Store(str(tmp_path / "run"))
    store.append(_rec("k-ok", "OK"))
    store.append(_rec("k-wrong", "WRONG_ANSWER"))
    store.append(_rec("k-budget", "NOT_RUN_BUDGET"))
    store.append(_rec("k-harness", "HARNESS_ERROR"))
    return store


def test_resume_filter_survives_refresh(tmp_path):
    store = _seed(tmp_path)
    done = runmod.refresh_done_keys(store, True)
    assert "k-ok" in done
    assert "k-wrong" in done
    assert "k-budget" not in done
    assert "k-harness" not in done
    # Simulate a block finishing mid-run: append a new final record, refresh.
    # The old buggy refresh (bare existing_keys()) re-admits k-budget here.
    store.append(_rec("k-new-ok", "OK"))
    done2 = runmod.refresh_done_keys(store, True)
    assert "k-new-ok" in done2  # refresh still picks up newly written keys
    assert "k-budget" not in done2
    assert "k-harness" not in done2
    # A re-run that completes a budget key flips it back to done.
    store.append(_rec("k-budget", "OK"))
    done3 = runmod.refresh_done_keys(store, True)
    assert "k-budget" in done3


def test_no_resume_sees_every_key(tmp_path):
    store = _seed(tmp_path)
    done = runmod.refresh_done_keys(store, False)
    assert done == {"k-ok", "k-wrong", "k-budget", "k-harness"}
    store.append(_rec("k-new", "NOT_RUN_BUDGET"))
    done2 = runmod.refresh_done_keys(store, False)
    assert "k-new" in done2

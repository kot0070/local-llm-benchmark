"""FIX_ENV tests: CPU/RAM wmic->PowerShell fallback + contention false-positive filter.

All subprocess interaction is mocked (monkeypatched bench.env._run /
nvidia_snapshot); no real nvidia-smi, wmic, or powershell is ever invoked.
"""
from bench import env as envmod

CPU_SAMPLE = "Intel(R) Core(TM) i9-10900KF CPU @ 3.70GHz"
RAM_BYTES_SAMPLE = "34226864128"

# Synthetic 23-line compute-apps sample. Basenames are the ones the filter
# classifies; PIDs and paths are fake, not a machine capture.
FOREIGN_SAMPLE = """1101, C:\\Windows\\Example\\ShellHost.exe
1102, C:\\Windows\\Example\\CrossDeviceResume.exe
1103, C:\\Windows\\Example\\explorer.exe
1104, C:\\Windows\\Example\\StartMenuExperienceHost.exe
1105, C:\\Windows\\Example\\SearchHost.exe
1106, C:\\Program Files\\Example\\NVIDIA Overlay.exe
1107, C:\\Program Files\\Example\\NVIDIA Overlay.exe
1108, C:\\Program Files\\Example\\msedgewebview2.exe
1109, C:\\Program Files\\Example\\chrome.exe
1110, C:\\Program Files\\Example\\steamwebhelper.exe
1111, C:\\Program Files\\Example\\claude.exe
1112, C:\\Program Files\\Example\\claude.exe
1113, C:\\Program Files\\Example\\M365Copilot.exe
1114, C:\\Program Files\\Example\\msedgewebview2.exe
1115, C:\\Windows\\Example\\ApplicationFrameHost.exe
1116, C:\\Windows\\Example\\SystemSettings.exe
1117, C:\\Windows\\Example\\ShellExperienceHost.exe
1118, C:\\Program Files\\Example\\SnippingTool.exe
1119, C:\\Program Files\\Example\\WindowsTerminal.exe
1120, C:\\Program Files\\Example\\OpenCode.exe
1121, C:\\Program Files\\Example\\Notepad.exe
1122, C:\\Program Files\\Example\\msedge.exe
1123, C:\\Program Files\\Example\\llama-server.exe"""


def _run_router(monkeypatch, mapping, call_log=None):
    """Route mocked _run by distinctive command substring. mapping: sub -> (ok, out)."""
    def fake(cmd, timeout=30.0):
        text = " ".join(cmd)
        if call_log is not None:
            call_log.append(text)
        for key, val in mapping.items():
            if key in text:
                return val
        return False, "unexpected"
    monkeypatch.setattr(envmod, "_run", fake)


def test_cpu_ram_powershell_fallback(monkeypatch):
    _run_router(monkeypatch, {
        "nvidia-smi": (False, ""),
        "wmic": (False, ""),
        "Win32_Processor": (True, CPU_SAMPLE + "\r\n"),
        "Win32_ComputerSystem": (True, RAM_BYTES_SAMPLE + "\r\n"),
        "powercfg": (False, ""),
    })
    fp = envmod.fingerprint(None)
    assert fp["cpu"] == CPU_SAMPLE
    assert fp["ram"] == "31.9 GB"


def test_cpu_ram_both_fail_unknown(monkeypatch):
    monkeypatch.setattr(envmod, "_run", lambda *a, **k: (False, "nope"))
    fp = envmod.fingerprint(None)
    assert fp["cpu"] == "unknown"
    assert fp["ram"] == "unknown"


def test_cpu_ram_wmic_wins_no_powershell(monkeypatch):
    calls: list = []

    def fake(cmd, timeout=30.0):
        text = " ".join(cmd)
        calls.append(text)
        if "wmic" in text and "cpu" in text:
            return True, "Name  \n" + CPU_SAMPLE + "  \n"
        if "wmic" in text:
            return True, "TotalPhysicalMemory  \n" + RAM_BYTES_SAMPLE + "  \n"
        if "Get-CimInstance" in text:
            raise AssertionError("PowerShell fallback must not run when wmic works")
        return False, "unexpected"

    monkeypatch.setattr(envmod, "_run", fake)
    fp = envmod.fingerprint(None)
    assert fp["cpu"] == CPU_SAMPLE
    assert fp["ram"] == "31.9 GB"
    assert not any("Get-CimInstance" in c for c in calls)


def test_foreign_filter_drops_shell_and_harness_processes(monkeypatch):
    monkeypatch.setattr(
        envmod, "_run",
        lambda cmd, timeout=30.0: (True, FOREIGN_SAMPLE)
        if "query-compute-apps" in " ".join(cmd) else (False, "x"))
    got = envmod.foreign_gpu_processes()
    # Shell/helper names + llama-server + this harness's own control-plane
    # (claude.exe, opencode.exe) are excluded; genuine third-party
    # browsers/Electron apps stay, so the remainder is exactly that set.
    assert set(got) == {
        "1109, C:\\Program Files\\Example\\chrome.exe",
        "1110, C:\\Program Files\\Example\\steamwebhelper.exe",
        "1113, C:\\Program Files\\Example\\M365Copilot.exe",
        "1122, C:\\Program Files\\Example\\msedge.exe",
    }


def test_foreign_filter_keeps_real_heavy_process(monkeypatch):
    mixed = FOREIGN_SAMPLE + "\n45678, C:\\Program Files\\Example\\SomeGame\\SomeGame.exe"
    monkeypatch.setattr(
        envmod, "_run",
        lambda cmd, timeout=30.0: (True, mixed)
        if "query-compute-apps" in " ".join(cmd) else (False, "x"))
    got = envmod.foreign_gpu_processes()
    assert "45678, C:\\Program Files\\Example\\SomeGame\\SomeGame.exe" in got


def test_contention_check_real_sample_still_waits_on_third_party_apps(monkeypatch):
    """The synthetic sample still has chrome/msedge/steamwebhelper/M365Copilot
    in it (third-party basenames, deliberately not excluded) -> contention_check
    must NOT report uncontended on this sample; it should time out and return
    False once wait_s elapses (fail-safe: an idle browser costs one wait, never a
    missed real contender)."""
    monkeypatch.setattr(
        envmod, "_run",
        lambda cmd, timeout=30.0: (True, FOREIGN_SAMPLE)
        if "query-compute-apps" in " ".join(cmd) else (False, "x"))
    monkeypatch.setattr(
        envmod, "nvidia_snapshot",
        lambda: {"gpu_util": 0.0, "vram_used_mb": 1022.0, "temp_c": 45.0})
    import time as _time
    monkeypatch.setattr(_time, "sleep", lambda *a, **k: None)
    t = {"now": 0.0}
    monkeypatch.setattr(_time, "time", lambda: t.__setitem__("now", t["now"] + 1.0) or t["now"])
    ok, info = envmod.contention_check({"vram_baseline_mb": 1009.0}, wait_s=5.0)
    assert ok is False
    assert len(info["foreign"]) == 4  # chrome, steamwebhelper, msedge, M365Copilot


def test_contention_check_real_sample_passes_once_third_party_apps_close(monkeypatch):
    """Same synthetic sample with only the shell-helper + harness-control-plane lines
    (explorer/ShellHost/.../claude.exe/opencode.exe) -> those are always-on/self noise,
    so this must pass immediately, no waiting."""
    idle_only = "\n".join(
        ln for ln in FOREIGN_SAMPLE.splitlines()
        if "chrome.exe" not in ln.lower() and "msedge.exe" not in ln.lower()
        and "steamwebhelper" not in ln.lower() and "m365copilot" not in ln.lower())
    monkeypatch.setattr(
        envmod, "_run",
        lambda cmd, timeout=30.0: (True, idle_only)
        if "query-compute-apps" in " ".join(cmd) else (False, "x"))
    monkeypatch.setattr(
        envmod, "nvidia_snapshot",
        lambda: {"gpu_util": 0.0, "vram_used_mb": 1022.0, "temp_c": 45.0})
    import time as _time
    monkeypatch.setattr(_time, "sleep", lambda *a, **k: None)
    ok, info = envmod.contention_check({"vram_baseline_mb": 1009.0}, wait_s=600.0)
    assert ok is True
    assert info["foreign"] == []
    assert info["gpu_util_median"] == 0.0

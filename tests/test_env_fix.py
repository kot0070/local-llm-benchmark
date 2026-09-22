"""FIX_ENV tests: CPU/RAM wmic->PowerShell fallback + contention false-positive filter.

All subprocess interaction is mocked (monkeypatched bench.env._run /
nvidia_snapshot); no real nvidia-smi, wmic, or powershell is ever invoked.
"""
from bench import env as envmod

CPU_SAMPLE = "Intel(R) Core(TM) i9-10900KF CPU @ 3.70GHz"
RAM_BYTES_SAMPLE = "34226864128"

# Exact 23-line compute-apps sample from the night_20260921-155146 preflight.
FOREIGN_SAMPLE = """5984, C:\\Windows\\System32\\ShellHost.exe
4996, C:\\Windows\\SystemApps\\MicrosoftWindows.Client.CBS_cw5n1h2txyewy\\CrossDeviceResume.exe
5932, C:\\Windows\\explorer.exe
10796, C:\\Windows\\SystemApps\\Microsoft.Windows.StartMenuExperienceHost_cw5n1h2txyewy\\StartMenuExperienceHost.exe
10788, C:\\Windows\\SystemApps\\MicrosoftWindows.Client.CBS_cw5n1h2txyewy\\SearchHost.exe
11132, C:\\Program Files\\NVIDIA Corporation\\NVIDIA App\\CEF\\NVIDIA Overlay.exe
9440, C:\\Program Files\\NVIDIA Corporation\\NVIDIA App\\CEF\\NVIDIA Overlay.exe
12680, C:\\Program Files (x86)\\Microsoft\\EdgeWebView\\Application\\153.0.4234.48\\msedgewebview2.exe
8644, C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe
18340, D:\\Steam\\bin\\cef\\cef.win64\\steamwebhelper.exe
16408, C:\\Program Files\\WindowsApps\\Claude_2.2553.1.0_x64__pzs8sxrjxfjjc\\app\\claude.exe
21180, C:\\Program Files\\WindowsApps\\Claude_2.2553.1.0_x64__pzs8sxrjxfjjc\\app\\claude.exe
20508, C:\\Program Files\\WindowsApps\\Microsoft.MicrosoftOfficeHub_19.2609.44031.0_x64__8wekyb3d8bbwe\\M365Copilot.exe
21860, C:\\Program Files (x86)\\Microsoft\\EdgeWebView\\Application\\153.0.4234.48\\msedgewebview2.exe
11888, C:\\Windows\\System32\\ApplicationFrameHost.exe
11864, C:\\Windows\\ImmersiveControlPanel\\SystemSettings.exe
7420, C:\\Windows\\SystemApps\\ShellExperienceHost_cw5n1h2txyewy\\ShellExperienceHost.exe
9432, C:\\Program Files\\WindowsApps\\Microsoft.ScreenSketch_11.2607.23.0_x64__8wekyb3d8bbwe\\SnippingTool\\SnippingTool.exe
23364, C:\\Program Files\\WindowsApps\\Microsoft.WindowsTerminal_1.24.11911.0_x64__8wekyb3d8bbwe\\WindowsTerminal.exe
16744, C:\\Users\\DevUser\\AppData\\Local\\Programs\\@opencodedesktop\\OpenCode.exe
19992, C:\\Program Files\\WindowsApps\\Microsoft.WindowsNotepad_11.2607.14.0_x64__8wekyb3d8bbwe\\Notepad\\Notepad.exe
6164, C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe
13080, C:\\Users\\DevUser\\AppData\\Local\\Programs\\Ollama\\lib\\ollama\\llama-server.exe"""


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
        "8644, C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "18340, D:\\Steam\\bin\\cef\\cef.win64\\steamwebhelper.exe",
        "20508, C:\\Program Files\\WindowsApps\\Microsoft.MicrosoftOfficeHub_19.2609.44031.0_x64__8wekyb3d8bbwe\\M365Copilot.exe",
        "6164, C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    }


def test_foreign_filter_keeps_real_heavy_process(monkeypatch):
    mixed = FOREIGN_SAMPLE + "\n45678, D:\\Games\\SomeGame\\SomeGame.exe"
    monkeypatch.setattr(
        envmod, "_run",
        lambda cmd, timeout=30.0: (True, mixed)
        if "query-compute-apps" in " ".join(cmd) else (False, "x"))
    got = envmod.foreign_gpu_processes()
    assert "45678, D:\\Games\\SomeGame\\SomeGame.exe" in got


def test_contention_check_real_sample_still_waits_on_third_party_apps(monkeypatch):
    """The literal unmodified sample still has chrome/msedge/steamwebhelper/M365Copilot
    in it (genuine third-party apps, deliberately not excluded) -> contention_check
    must NOT report uncontended on this exact sample; it should time out and return
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
    """Same literal sample with only the shell-helper + harness-control-plane lines
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

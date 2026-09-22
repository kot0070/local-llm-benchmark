"""Environment helpers: fingerprint, GPU monitor, gates. Never crashes the run."""
from __future__ import annotations

import csv
import datetime
import os
import platform
import subprocess
import sys
import threading
import time


def _run(cmd: list[str], timeout: float = 30.0) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return p.returncode == 0, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:  # missing binary etc.
        return False, f"error: {e}"


def nvidia_snapshot() -> dict | None:
    ok, out = _run(["nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,temperature.gpu,"
                    "clocks.sm,power.draw,pstate,clocks_event_reasons.active",
                    "--format=csv,noheader,nounits"], timeout=30.0)
    if not ok or not out.strip():
        return None
    try:
        row = next(csv.reader([out.strip().splitlines()[0]]))
        row = [c.strip() for c in row]
        return {"gpu_util": _f(row[0]), "vram_used_mb": _f(row[1]),
                "temp_c": _f(row[2]), "clock_sm_mhz": _f(row[3]),
                "power_w": _f(row[4]), "pstate": row[5] if len(row) > 5 else "",
                "throttle_reasons": row[6] if len(row) > 6 else ""}
    except Exception:
        return None


# False-positive background GPU helpers (2026-09-21, revised same night after a manager
# audit caught an overclaim in FIX_ENV's own DONE report -- see MASTER_PLAN.md log):
# tonight's preflight on this Windows PC waited the full 600 s contention window even
# though the GPU was idle (med_u=0.0, vram ~1022 vs baseline ~1009 MB) because
# foreign_gpu_processes() listed ~23 ordinary desktop processes holding a GPU context.
# nvidia-smi reports [N/A] memory for every process here, so a memory-based filter
# cannot work; instead we exclude by basename in two groups:
#  1. Windows shell/desktop-compositor helpers (DWM-related): never real GPU compute.
#  2. This harness's OWN control-plane processes: the Claude Desktop app running the
#     manager session (claude.exe) and the OpenCode agent launcher (opencode.exe) are
#     present on THIS machine during every single run this harness will ever do (the
#     manager and its agents ARE the thing running the benchmark) -- exact behaviour
#     confirmed against the real, unmodified 23-line sample recorded tonight, which
#     contains both (see tests/test_env_fix.py). Excluding them is the same principle
#     as excluding ollama/llama-server: it is the harness's own tooling, not a
#     competing GPU workload.
# Genuine third-party browsers/Electron apps (chrome.exe, msedge.exe,
# steamwebhelper.exe, M365Copilot.exe, ...) are deliberately NOT excluded so a real
# second GPU consumer (someone else's browser doing video/WebGL, another app) is
# still caught -- this does mean an idle browser window can still cost one contention
# wait; that is the conservative/fail-safe direction (extra wait, never a missed
# contender), unlike claude.exe/opencode.exe which are never "someone else".
BACKGROUND_GPU_PROCESSES = frozenset({
    "explorer.exe",
    "shellhost.exe",
    "shellexperiencehost.exe",
    "startmenuexperiencehost.exe",
    "searchhost.exe",
    "applicationframehost.exe",
    "systemsettings.exe",
    "crossdeviceresume.exe",
    "nvidia overlay.exe",
    "snippingtool.exe",
    "windowsterminal.exe",
    "notepad.exe",
    "msedgewebview2.exe",
    "claude.exe",
    "opencode.exe",
})


def _basename_lower(path: str) -> str:
    return path.replace("/", "\\").rsplit("\\", 1)[-1].strip().lower()


def _clean_cpu_value(out: str) -> str:
    lines = [ln.strip() for ln in (out or "").strip().splitlines() if ln.strip()]
    # Drop wmic header lines ("Name") if present; PowerShell returns the bare name.
    data = [ln for ln in lines if ln.lower() != "name"]
    if data:
        return data[0][:300]
    return (out or "").strip()[:300]


def _parse_ram_bytes(out: str) -> int | None:
    import re
    text = (out or "").strip()
    if not text:
        return None
    # wmic header ("TotalPhysicalMemory") plus digits, or a bare PowerShell number.
    nums = re.findall(r"\d+", text)
    if not nums:
        return None
    try:
        # Take the largest integer (the byte count, not a header artifact).
        return max(int(g) for g in nums)
    except Exception:
        return None


def _f(x) -> float | None:
    try:
        return float(str(x).strip())
    except (ValueError, TypeError):
        return None


def _throttle_active(reason) -> bool:
    s = str(reason or "").strip()
    if not s:
        return False
    low = s.lower()
    if "not active" in low or low in ("n/a", "na", "none", "no"):
        return False
    compact = s.replace(" ", "").replace("_", "").lower()
    # nvidia-smi clocks_event_reasons bitmask: 0x1 GpuIdle and 0x4 SwPowerCap are normal states, not throttling.
    # Count only HW slowdown (0x8), SW thermal (0x20), HW thermal (0x40), HW power brake (0x80).
    try:
        bits = int(compact, 16) if compact.startswith("0x") else int(compact)
    except ValueError:
        return False
    return bool(bits & (0x8 | 0x20 | 0x40 | 0x80))


def fingerprint(client=None) -> dict:
    fp: dict = {"time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "python": sys.version, "platform": platform.platform(),
               "warnings": []}
    ok, out = _run(["nvidia-smi",
                    "--query-gpu=name,uuid,driver_version,memory.total,power.limit",
                    "--format=csv,noheader"], timeout=30.0)
    if ok and out.strip():
        fp["gpu"] = out.strip()
    else:
        fp["gpu"] = "unknown"
        fp["warnings"].append("nvidia-smi fingerprint failed")
    ok, out = _run(["wmic", "cpu", "get", "name"], timeout=30.0)
    cpu = _clean_cpu_value(out) if ok and out.strip() else ""
    if not cpu:
        ok_ps, out_ps = _run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor).Name"], timeout=30.0)
        cpu = _clean_cpu_value(out_ps) if ok_ps and out_ps.strip() else ""
    fp["cpu"] = cpu if cpu else "unknown"
    ok, out = _run(["wmic", "computersystem", "get", "totalphysicalmemory"],
                   timeout=30.0)
    ram_bytes = _parse_ram_bytes(out) if ok and out.strip() else None
    if ram_bytes is None:
        ok_ps, out_ps = _run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
            timeout=30.0)
        ram_bytes = _parse_ram_bytes(out_ps) if ok_ps and out_ps.strip() else None
    fp["ram"] = f"{ram_bytes / 1024 ** 3:.1f} GB" if ram_bytes else "unknown"
    ok, out = _run(["powercfg", "/getactivescheme"], timeout=30.0)
    fp["power_scheme"] = out.strip()[:200] if ok else "unknown"
    try:
        import ctypes  # noqa: F401
        fp["os"] = platform.version()
    except Exception:
        fp["os"] = "unknown"
    if client is not None:
        try:
            fp["ollama_version"] = client.version()
        except Exception as e:
            fp["ollama_version"] = "unknown"
            fp["warnings"].append(f"ollama version failed: {e}")
    else:
        fp["ollama_version"] = "unknown"
    return fp


def idle_baseline(duration_s: float = 30.0, interval_s: float = 1.0) -> dict:
    """Sample GPU for duration_s; return medians/peaks. Degrades gracefully."""
    samples = []
    t_end = time.time() + duration_s
    while time.time() < t_end:
        s = nvidia_snapshot()
        if s is not None:
            samples.append(s)
        time.sleep(interval_s)
    if not samples:
        return {"samples": 0, "vram_baseline_mb": None, "gpu_util_median": None,
                "idle_temp_c": None, "warning": "no nvidia-smi samples"}
    import statistics
    vrams = [s["vram_used_mb"] for s in samples if s["vram_used_mb"] is not None]
    utils = [s["gpu_util"] for s in samples if s["gpu_util"] is not None]
    temps = [s["temp_c"] for s in samples if s["temp_c"] is not None]
    return {"samples": len(samples),
            "vram_baseline_mb": statistics.median(vrams) if vrams else None,
            "gpu_util_median": statistics.median(utils) if utils else None,
            "idle_temp_c": statistics.median(temps) if temps else None}


def contention_check(baseline: dict, wait_s: float = 600.0) -> tuple[bool, dict]:
    """Return (ok, info). ok False -> caller records BLOCKED_CONTENDED."""
    import statistics
    t_end = time.time() + wait_s
    last: dict = {}
    while True:
        snaps = []
        for _ in range(5):
            s = nvidia_snapshot()
            if s is not None:
                snaps.append(s)
            time.sleep(2.0)
        if not snaps:
            return True, {"warning": "nvidia-smi unavailable, contention check skipped"}
        utils = [s["gpu_util"] for s in snaps if s["gpu_util"] is not None]
        vrams = [s["vram_used_mb"] for s in snaps if s["vram_used_mb"] is not None]
        med_u = statistics.median(utils) if utils else 0.0
        med_v = statistics.median(vrams) if vrams else 0.0
        base_v = baseline.get("vram_baseline_mb") or 0.0
        foreign = foreign_gpu_processes()
        last = {"gpu_util_median": med_u, "vram_used_mb": med_v,
                "vram_baseline_mb": base_v, "foreign": foreign}
        uncontended = med_u <= 10.0 and (med_v <= (base_v or 0.0) + 300.0) and not foreign
        if uncontended:
            return True, last
        if time.time() >= t_end:
            return False, last


def foreign_gpu_processes() -> list[str]:
    ok, out = _run(["nvidia-smi", "--query-compute-apps=pid,process_name",
                    "--format=csv,noheader"], timeout=30.0)
    if not ok:
        return []
    foreign = []
    for line in out.strip().splitlines():
        low = line.lower()
        if not low.strip():
            continue
        if "ollama" in low or "llama-server" in low or "llama_server" in low:
            continue
        # Skip the pid prefix ("pid, path") then match the exe basename.
        _path = line.split(",", 1)[1] if "," in line else line
        if _basename_lower(_path) in BACKGROUND_GPU_PROCESSES:
            continue
        foreign.append(line.strip())
    return foreign


def thermal_gate(idle_temp: float | None, wait_s: float = 180.0) -> dict:
    limit = max((idle_temp or 45.0) + 5.0, 50.0)
    t_end = time.time() + wait_s
    info: dict = {"limit_c": limit, "waited": False, "temp_c": None}
    while True:
        s = nvidia_snapshot()
        t = s.get("temp_c") if s else None
        info["temp_c"] = t
        if t is None or t <= limit:
            return info
        if time.time() >= t_end:
            info["waited"] = True
            return info
        time.sleep(5.0)


def unload_all(client, baseline: dict, timeout_s: float = 60.0) -> tuple[bool, dict]:
    """Unload models via API; verify /api/ps empty and VRAM back near baseline."""
    try:
        ps = client.ps()
        for m in ps.get("models", []):
            name = m.get("name") or m.get("model", "")
            if name:
                client.unload(name)
    except Exception as e:
        return False, {"error": str(e)}
    t_end = time.time() + timeout_s
    while True:
        try:
            ps = client.ps()
            running = ps.get("models", [])
        except Exception:
            running = []
        snap = nvidia_snapshot()
        vram = (snap or {}).get("vram_used_mb")
        base_v = baseline.get("vram_baseline_mb") or 0.0
        empty = not running
        low = vram is None or vram <= (base_v or 0.0) + 300.0
        if empty and low:
            return True, {"vram_used_mb": vram, "running": []}
        if time.time() >= t_end:
            # one retry of unload
            try:
                for m in running:
                    name = m.get("name") or m.get("model", "")
                    if name:
                        client.unload(name)
            except Exception:
                pass
            time.sleep(5.0)
            try:
                ps2 = client.ps()
                running2 = ps2.get("models", [])
            except Exception:
                running2 = running
            snap2 = nvidia_snapshot()
            vram2 = (snap2 or {}).get("vram_used_mb")
            ok = (not running2) and (vram2 is None or vram2 <= (base_v or 0.0) + 300.0)
            return ok, {"vram_used_mb": vram2,
                        "running": [m.get("name", "") for m in running2],
                        "retried": True}


class Monitor(threading.Thread):
    """Sample GPU every 2 s into a CSV; per-record summary available.

    Keeps a timestamped ring buffer of the last 2 h (FIX_A.6) so per-request
    windows can be aggregated. window_stats(t_start, t_end) aggregates only
    samples inside the window; callers fall back to a single snapshot when
    the window has no samples.
    """

    WINDOW_S = 2 * 3600.0

    def __init__(self, csv_path: str, interval_s: float = 2.0):
        super().__init__(daemon=True)
        self.csv_path = csv_path
        self.interval_s = interval_s
        self._stop = threading.Event()
        self.samples: list[dict] = []
        self._timed: list[tuple[float, dict]] = []
        self._lock = threading.Lock()

    def run(self):
        os.makedirs(os.path.dirname(self.csv_path) or ".", exist_ok=True)
        new = not os.path.exists(self.csv_path)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["ts_utc", "gpu_util", "vram_used_mb", "temp_c",
                            "clock_sm_mhz", "power_w", "pstate", "throttle_reasons"])
            while not self._stop.is_set():
                s = nvidia_snapshot()
                ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
                if s is not None:
                    now = time.time()
                    with self._lock:
                        self.samples.append(s)
                        self._timed.append((now, s))
                        cutoff = now - self.WINDOW_S
                        self._timed = [(t, d) for t, d in self._timed if t >= cutoff]
                    w.writerow([ts, s.get("gpu_util"), s.get("vram_used_mb"),
                                s.get("temp_c"), s.get("clock_sm_mhz"),
                                s.get("power_w"), s.get("pstate"),
                                s.get("throttle_reasons")])
                    f.flush()
                self._stop.wait(self.interval_s)

    def stop(self) -> dict:
        self._stop.set()
        return self.summary()

    def window_stats(self, t_start: float, t_end: float) -> dict:
        """Aggregate samples with t_start <= ts <= t_end (last-2h ring buffer)."""
        with self._lock:
            window = [(t, d) for t, d in self._timed if t_start <= t <= t_end]
        if not window:
            return {"samples": 0}
        window.sort(key=lambda x: x[0])
        dicts = [d for _, d in window]
        vrams = [d["vram_used_mb"] for d in dicts if d.get("vram_used_mb") is not None]
        utils = [d["gpu_util"] for d in dicts if d.get("gpu_util") is not None]
        temps = [d["temp_c"] for d in dicts if d.get("temp_c") is not None]
        import statistics as _st
        return {"samples": len(window),
                "vram_peak_mb": max(vrams) if vrams else None,
                "gpu_util_mean": (sum(utils) / len(utils)) if utils else None,
                "temp_start": temps[0] if temps else None,
                "temp_peak": max(temps) if temps else None,
                "throttle": any(_throttle_active(d.get("throttle_reasons"))
                                for d in dicts)}

    def add_sample(self, sample: dict, ts: float | None = None) -> None:
        """Test hook: insert a sample with an explicit timestamp."""
        now = ts if ts is not None else time.time()
        with self._lock:
            self.samples.append(sample)
            self._timed.append((now, sample))
            cutoff = now - self.WINDOW_S
            self._timed = [(t, d) for t, d in self._timed if t >= cutoff]

    def summary(self) -> dict:
        vrams = [s["vram_used_mb"] for s in self.samples if s.get("vram_used_mb") is not None]
        utils = [s["gpu_util"] for s in self.samples if s.get("gpu_util") is not None]
        temps = [s["temp_c"] for s in self.samples if s.get("temp_c") is not None]
        import statistics
        return {"samples": len(self.samples),
                "vram_peak_mb": max(vrams) if vrams else None,
                "gpu_util_mean": (sum(utils) / len(utils)) if utils else None,
                "temp_start_c": temps[0] if temps else None,
                "temp_peak_c": max(temps) if temps else None,
                "throttle": any(_throttle_active(s.get("throttle_reasons"))
                                for s in self.samples)}


def set_thread_execution_state(prevent_sleep: bool = True) -> None:
    """ES_CONTINUOUS|ES_SYSTEM_REQUIRED while running; ES_CONTINUOUS on exit."""
    try:
        import ctypes
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED if prevent_sleep else ES_CONTINUOUS)
    except Exception:
        pass

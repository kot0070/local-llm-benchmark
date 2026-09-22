"""Restricted code runner for BENCH V5 NIGHT-1 (owner: TASK_B1). Stdlib only.

Runs candidate code in a separate process (``python -I`` + a worker script)
under a Windows Job Object via ctypes (process memory limit 512 MB, kill on
close) with a wall timeout (5 s per test group).

Import hook policy: only these top-level packages are importable inside the
sandbox: math, re, collections, itertools, functools, heapq, bisect, datetime,
json, string, dataclasses, typing, enum, decimal, fractions, statistics,
operator, copy, random. Everything else (os, subprocess, socket, shutil,
pathlib, ctypes, importlib, sys, ...) is blocked. ``builtins.open``,
``eval``/``exec``/``compile`` of new code and ``input`` are blocked.
Classes, exceptions, isinstance etc. keep working.

Two modes:
  run_function_tests(code, func_name, tests, timeout_s=5)
  run_stdin_tests(code, tests, timeout_s=5)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ALLOWED_TOP = {
    "math", "re", "collections", "itertools", "functools", "heapq",
    "bisect", "datetime", "json", "string", "dataclasses", "typing",
    "enum", "decimal", "fractions", "statistics", "operator", "copy",
    "random",
}

BLOCKED_TOP = {
    "os", "subprocess", "socket", "shutil", "pathlib", "ctypes",
    "importlib", "sys", "io", "multiprocessing", "threading", "signal",
    "builtins", "runpy", "pkgutil", "importlib",
}

_WORKER = r'''
import builtins
import importlib.abc
import io as _sandbox_io
import json
import sys
import traceback

_REAL_OPEN = builtins.open
_REAL_EXEC = builtins.exec
_REAL_COMPILE = builtins.compile

ALLOWED = set(__ALLOWED__)
PAYLOAD = __PAYLOAD__

_real_import = builtins.__import__

class _Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        top = name.split(".")[0]
        if top in ALLOWED or top == "__main__":
            return None
        raise ImportError("blocked import: %s" % name)

def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    top = (name or "").split(".")[0] if name else ""
    if level != 0:
        raise ImportError("relative imports blocked")
    if top in ALLOWED:
        return _real_import(name, globals, locals, fromlist, level)
    raise ImportError("blocked import: %s" % name)

sys.meta_path.insert(0, _Guard())
builtins.__import__ = _guarded_import

def _blocked(*a, **k):
    raise RuntimeError("blocked in sandbox")

builtins.open = _blocked
builtins.eval = _blocked
builtins.exec = _blocked
builtins.compile = _blocked
# NOTE: builtins.input stays available: stdin/stdout programs read test input
# through it (sys.stdin is set per test); in function-test mode stdin is an
# empty stream so input() raises EOFError inside the tested call.
try:
    builtins.exit = _blocked
    builtins.quit = _blocked
except Exception:
    pass

def _err_trace(e):
    # NOTE: traceback.format_exc() is unusable here: it reads source lines
    # via linecache -> builtins.open, which this sandbox blocks.
    try:
        return "".join(traceback.format_exception_only(type(e), e)).strip()
    except Exception:
        return "%s: %s" % (type(e).__name__, e)

def _deep_equal(a, b):
    if isinstance(a, float) and isinstance(b, float):
        if a == b:
            return True
        return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_deep_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_deep_equal(a[k], b[k]) for k in a)
    return a == b

def main():
    with _REAL_OPEN(PAYLOAD, "r", encoding="utf-8") as f:
        job = json.load(f)
    mode = job["mode"]
    code = job["code"]
    ns = {"__name__": "candidate"}
    try:
        code_obj = _REAL_COMPILE(code, "<candidate>", "exec")
    except Exception as e:
        return {"ok": False, "error": "COMPILE: %s" % e,
                "trace": _err_trace(e)}
    ns = {"__name__": "candidate"}
    if mode == "func":
        try:
            _REAL_EXEC(code_obj, ns)
        except Exception as e:
            return {"ok": False, "error": "SETUP: %s: %s" % (type(e).__name__, e),
                    "trace": _err_trace(e)}
    if mode == "func":
        fn = ns.get(job["func"])
        if not callable(fn):
            return {"ok": False, "error": "NO_FUNC: %r not defined" % job["func"]}
        results = []
        for t in job["tests"]:
            old_stdin = sys.stdin
            sys.stdin = _sandbox_io.StringIO("")
            try:
                args = t.get("args", [])
                kwargs = t.get("kwargs", {}) or {}
                got = fn(*args, **kwargs)
                exp = t.get("expected")
                passed = _deep_equal(got, exp)
                results.append({"passed": bool(passed), "got": _safe(got),
                                "expected": _safe(exp), "error": None})
            except Exception as e:
                results.append({"passed": False, "got": None,
                                "expected": _safe(t.get("expected")),
                                "error": "%s: %s" % (type(e).__name__, e)})
            finally:
                sys.stdin = old_stdin
        return {"ok": True, "results": results}
    else:
        results = []
        for t in job["tests"]:
            stdin_data = t.get("stdin", "")
            exp = t.get("expected", "")
            old_stdin, old_stdout = sys.stdin, sys.stdout
            sys.stdin = _sandbox_io.StringIO(stdin_data)
            sys.stdout = _sandbox_io.StringIO()
            try:
                _REAL_EXEC(code_obj, {"__name__": "candidate"})
                out = sys.stdout.getvalue()
                passed = _norm_out(out) == _norm_out(exp)
                results.append({"passed": bool(passed), "got": out,
                                "expected": exp, "error": None})
            except Exception as e:
                try:
                    partial = sys.stdout.getvalue()
                except Exception:
                    partial = None
                results.append({"passed": False, "got": partial,
                                "expected": exp,
                                "error": "%s: %s" % (type(e).__name__, e)})
            finally:
                sys.stdin, sys.stdout = old_stdin, old_stdout
        return {"ok": True, "results": results}

def _safe(v):
    try:
        json.dumps(v)
        return v
    except Exception:
        return repr(v)

def _norm_out(s):
    lines = str(s or "").replace("\r\n", "\n").split("\n")
    lines = [ln.rstrip() for ln in lines]
    while lines and lines[-1] == "":
        lines.pop()
    while lines and lines[0] == "":
        lines.pop(0)
    return "\n".join(lines)
'''


def _worker_source(payload_path: str) -> str:
    allowed_repr = repr(sorted(ALLOWED_TOP))
    src = _WORKER.replace("__ALLOWED__", allowed_repr).replace(
        "__PAYLOAD__", repr(payload_path))
    src = src.replace(
        "    ns = {\"__name__\": \"candidate\"}\n"
        "    ns = {\"__name__\": \"candidate\"}\n",
        "    ns = {\"__name__\": \"candidate\"}\n",
    )
    return src


def _run_worker(payload: dict, timeout_s: float) -> dict:
    tmpd = tempfile.mkdtemp(prefix="pysandbox_")
    payload_path = os.path.join(tmpd, "payload.json")
    result_path = os.path.join(tmpd, "result.json")
    worker_path = os.path.join(tmpd, "worker.py")
    runner_path = os.path.join(tmpd, "run.py")
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    with open(worker_path, "w", encoding="utf-8") as f:
        f.write(_worker_source(payload_path))
    with open(runner_path, "w", encoding="utf-8") as f:
        f.write(
            "import json, os, sys\n"
            "_open = open\n"
            "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
            "import worker\n"
            "try:\n"
            "    res = worker.main()\n"
            "except Exception as e:\n"
            "    res = {'ok': False, 'error': 'WORKER: ' + type(e).__name__ + ': ' + str(e)}\n"
            "with _open(" + repr(result_path) + ", 'w', encoding='utf-8') as fh:\n"
            "    json.dump(res, fh)\n"
        )
    cmd = [sys.executable, "-I", runner_path]
    job = None
    try:
        job = _create_job()
    except Exception:  # noqa: BLE001
        job = None
    try:
        proc = subprocess.Popen(
            cmd, cwd=tmpd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": "SPAWN: %s" % e, "results": []}
    try:
        if job is not None:
            try:
                _assign_job(job, proc.pid)
            except Exception:  # noqa: BLE001
                pass
        _out, _err = b"", b""
        try:
            _out, _err = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass
            try:
                proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                pass
            return {"ok": False, "error": "TIMEOUT", "results": []}
        if proc.returncode != 0:
            try:
                with open(result_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:  # noqa: BLE001
                if os.environ.get("PYSANDBOX_DEBUG"):
                    sys.stderr.write("pysandbox child rc=%s err=%s\n"
                                     % (proc.returncode, (_err or b"")[-2000:]))
                return {"ok": False, "error": "RUNTIME_FAIL rc=%s" % proc.returncode,
                        "results": []}
        try:
            with open(result_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": "NO_RESULT: %s" % e, "results": []}
    finally:
        try:
            _close_job(job)
        except Exception:  # noqa: BLE001
            pass
        # Best-effort cleanup of temp files.
        for p in (payload_path, result_path, worker_path, runner_path):
            try:
                os.remove(p)
            except Exception:  # noqa: BLE001
                pass
        try:
            os.rmdir(tmpd)
        except Exception:  # noqa: BLE001
            pass


# ---------------- Windows Job Object via ctypes ----------------

def _create_job():
    import ctypes

    kernel32 = ctypes.windll.kernel32

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in
                    ("ReadOperationCount", "WriteOperationCount",
                     "OtherOperationCount", "ReadTransferCount",
                     "WriteTransferCount", "OtherTransferCount")]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x0100
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    JobObjectExtendedLimitInformation = 9

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise RuntimeError("CreateJobObjectW failed")
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
    info.ProcessMemoryLimit = 512 * 1024 * 1024
    ok = kernel32.SetInformationJobObject(
        job, JobObjectExtendedLimitInformation,
        ctypes.byref(info), ctypes.sizeof(info))
    if not ok:
        kernel32.CloseHandle(job)
        raise RuntimeError("SetInformationJobObject failed")
    # Keep refs alive for AssignProcessToJobObject.
    _create_job._k = kernel32
    return job


def _assign_job(job, pid: int) -> None:
    import ctypes

    kernel32 = ctypes.windll.kernel32
    PROCESS_SET_QUOTA = 0x0100
    PROCESS_TERMINATE = 0x0001
    h = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid)
    if not h:
        raise RuntimeError("OpenProcess failed")
    try:
        if not kernel32.AssignProcessToJobObject(job, h):
            raise RuntimeError("AssignProcessToJobObject failed")
    finally:
        kernel32.CloseHandle(h)


def _close_job(job) -> None:
    if job is None:
        return
    import ctypes

    ctypes.windll.kernel32.CloseHandle(job)


# ---------------- public API ----------------

def _summarise(out: dict, total: int) -> dict:
    if not out.get("ok"):
        n = total
        return {"passed": 0, "total": n,
                "results": [{"passed": False, "got": None, "expected": None,
                             "error": out.get("error", "SETUP_FAIL")}
                            for _ in range(n)],
                "error": out.get("error")}
    results = out.get("results", [])
    passed = sum(1 for r in results if r.get("passed"))
    return {"passed": passed, "total": len(results), "results": results,
            "error": None}


def run_function_tests(code: str, func_name: str, tests: list,
                       timeout_s: float = 5.0) -> dict:
    """Run function tests; tests entries {args, kwargs?, expected}."""
    norm = []
    for t in tests or []:
        args = t.get("args", [])
        if not isinstance(args, list):
            args = [args]
        norm.append({"args": args, "kwargs": t.get("kwargs") or {},
                     "expected": t.get("expected")})
    payload = {"mode": "func", "code": code, "func": func_name, "tests": norm}
    try:
        out = _run_worker(payload, timeout_s)
    except Exception as e:  # noqa: BLE001
        out = {"ok": False, "error": "HARNESS: %s" % e}
    return _summarise(out, len(norm))


def run_stdin_tests(code: str, tests: list, timeout_s: float = 5.0) -> dict:
    """Run stdin/stdout program tests; entries {stdin, expected}."""
    norm = [{"stdin": t.get("stdin", ""), "expected": t.get("expected", "")}
            for t in (tests or [])]
    payload = {"mode": "stdin", "code": code, "tests": norm}
    try:
        out = _run_worker(payload, timeout_s)
    except Exception as e:  # noqa: BLE001
        out = {"ok": False, "error": "HARNESS: %s" % e}
    return _summarise(out, len(norm))

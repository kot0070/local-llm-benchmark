"""Shared SQL helpers for BENCH V5 NIGHT-1 (owner: TASK_B1). Stdlib only."""
from __future__ import annotations

import itertools
import re
import sqlite3

FLOAT_TOL = 1e-6

# Markers of Postgres-only syntax that SQLite cannot run.
DIALECT_MARKERS = (
    "::", "ilike", "distinct on", "returning", "generate_series",
    "current_setting(", "pg_", "date_trunc(", "to_char(", "string_agg(",
    "$$", "acknowledge",
)

_WRITE_RE = re.compile(
    r"(?i)\b(insert|update|delete|replace|create|drop|alter|truncate|attach|detach|"
    r"vacuum|reindex|grant|revoke|commit|rollback|savepoint|release)\b"
)


def extract_sql(text: str) -> tuple[str | None, dict]:
    """Extract one SQL statement from model output.

    Strips ``` fences / a "sql" tag / trailing ";". Returns (sql|None, info)
    with info {"fenced": bool, "prose": bool, "strict": bool}.
    prose=True means extra text surrounded the SQL (contract broken but the
    SQL is still attempted).
    """
    info = {"fenced": False, "prose": False, "strict": False}
    if text is None or not str(text).strip():
        return None, info
    s = str(text).strip()
    info["fenced"] = "```" in s
    sql = None
    if "```" in s:
        blocks: list[str] = []
        tmp = s
        while True:
            start = tmp.find("```")
            if start == -1:
                break
            end = tmp.find("```", start + 3)
            if end == -1:
                blocks.append(tmp[start + 3:])
                tmp = ""
                break
            blocks.append(tmp[start + 3:end])
            tmp = tmp[:start] + "\n" + tmp[end + 3:]
        cleaned = []
        for b in blocks:
            lines = b.split("\n", 1)
            if len(lines) == 2 and lines[0].strip().lower() in ("sql", "sqlite", "sqlite3"):
                b = lines[1]
            b = b.strip()
            if b:
                cleaned.append(b)
        outside = tmp.strip()
        if cleaned:
            sql = max(cleaned, key=len)
            if outside:
                info["prose"] = True
        else:
            sql = None
    else:
        # No fences: strip a leading "sql" tag line, take the whole text.
        lines = s.splitlines()
        if lines and lines[0].strip().lower() in ("sql", "sqlite", "sqlite3", "sql:"):
            sql = "\n".join(lines[1:]).strip()
            info["prose"] = True
        else:
            sql = s
    if sql is None:
        return None, info
    sql = sql.strip().rstrip(";").strip()
    # A lone tag with nothing else.
    if not sql or sql.lower() in ("sql", "sqlite"):
        return None, info
    # Prose detection for the no-fence path: leading explanatory text means
    # the whole text is not just SQL.
    first_kw = re.search(r"(?i)\b(select|with)\b", sql)
    if first_kw and first_kw.start() > 0:
        head = sql[:first_kw.start()].strip()
        if head:
            info["prose"] = True
            sql = sql[first_kw.start():].strip().rstrip(";").strip()
    tail_extra = re.search(r"(?i)(here is|explanation|note:|the query returns)\b", sql)
    if tail_extra and ("```" not in s):
        # Heuristic: prose after the statement is unusual; keep statement only
        # if it ends cleanly, else just flag.
        pass
    if not info["fenced"] and not info["prose"]:
        info["strict"] = True
    elif info["fenced"] and not info["prose"]:
        # Fenced code only: still not "only the SQL query", keep strict False.
        info["strict"] = False
    return sql, info


def check_single_select(sql: str) -> tuple[bool, str | None]:
    """Accept exactly one SELECT/WITH statement; reject writes/multiples."""
    if not sql or not sql.strip():
        return False, "EMPTY_SQL"
    body = sql.strip()
    # Forbid multiple statements (a semicolon followed by more text).
    parts = [p for p in body.split(";") if p.strip()]
    if len(parts) > 1:
        return False, "MULTI_STATEMENT"
    if _WRITE_RE.search(body):
        return False, "WRITE_STATEMENT"
    if not re.match(r"(?is)^\s*(select|with)\b", body):
        return False, "NOT_SELECT"
    return True, None


def looks_postgres(sql: str) -> bool:
    low = sql.lower()
    return any(m in low for m in DIALECT_MARKERS)


class _ReadOnlyAuthorizer:
    def __init__(self):
        self.denied = False

    def __call__(self, action, *args):
        import sqlite3 as _s

        allowed = {_s.SQLITE_SELECT, _s.SQLITE_READ, _s.SQLITE_FUNCTION,
                   _s.SQLITE_TRANSACTION, _s.SQLITE_SAVEPOINT, _s.SQLITE_RECURSIVE}
        # SQLITE_OK == 0
        if action in allowed:
            return 0
        self.denied = True
        return 1  # SQLITE_DENY


def execute_readonly(db_path: str, sql: str, timeout_s: float = 2.0) -> dict:
    """Execute one SELECT read-only. Returns dict with ok/rows/columns or error."""
    ok, reason = check_single_select(sql)
    if not ok:
        return {"ok": False, "error": reason, "dialect": False}
    uri = "file:" + str(db_path).replace("?", "%3F") + "?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True, timeout=5.0)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"CONNECT: {e}", "dialect": False}
    try:
        con.execute("PRAGMA query_only = ON")
        auth = _ReadOnlyAuthorizer()
        try:
            con.set_authorizer(auth)
        except Exception:  # noqa: BLE001
            pass
        try:
            con.set_progress_handler(lambda: 1, 200000)
        except Exception:  # noqa: BLE001
            pass
        import time

        t0 = time.monotonic()
        try:
            cur = con.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            dialect = looks_postgres(sql) or looks_postgres(msg)
            return {"ok": False, "error": msg, "dialect": dialect}
        finally:
            try:
                con.set_progress_handler(None, 0)
            except Exception:  # noqa: BLE001
                pass
        if time.monotonic() - t0 > max(timeout_s, 0.1):
            return {"ok": False, "error": "TIMEOUT", "dialect": False}
        return {"ok": True, "rows": [list(r) for r in rows], "columns": cols,
                "dialect": False}
    finally:
        try:
            con.close()
        except Exception:  # noqa: BLE001
            pass


def _cells_equal(a, b, tol: float = FLOAT_TOL) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, bool) != isinstance(b, bool):
        # sqlite returns ints for bools; allow 0/1 == False/True
        if isinstance(a, bool) and b in (0, 1):
            return int(a) == b
        if isinstance(b, bool) and a in (0, 1):
            return a == int(b)
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        try:
            return abs(float(a) - float(b)) <= tol
        except Exception:  # noqa: BLE001
            return False
    if isinstance(a, (bytes, bytearray)) or isinstance(b, (bytes, bytearray)):
        return bytes(a) if isinstance(a, (bytes, bytearray)) else a == (
            bytes(b) if isinstance(b, (bytes, bytearray)) else b)
    return str(a) == str(b)


def _rows_equal_set(got, exp, tol: float = FLOAT_TOL) -> tuple[int, list[str]]:
    """Greedy multiset match; returns (matched, notes)."""
    unmatched = list(got)
    matched = 0
    for er in exp:
        hit = -1
        for i, gr in enumerate(unmatched):
            if len(gr) != len(er):
                continue
            if all(_cells_equal(g, e, tol) for g, e in zip(gr, er)):
                hit = i
                break
        if hit >= 0:
            unmatched.pop(hit)
            matched += 1
    return matched, []


def compare_rows(got_rows, exp_rows, order_required: bool,
                 tol: float = FLOAT_TOL) -> tuple[float, dict]:
    """Compare result multisets (or ordered lists). Returns (score, details).

    A column permutation of the candidate is accepted: when the candidate has
    the same number of columns and some permutation of its columns matches the
    gold rows, the score is 1.0 with details["column_permutation"] = True.
    Extra or missing columns stay wrong (score < 1.0, flag False).
    """
    got = [list(r) for r in (got_rows or [])]
    exp = [list(r) for r in (exp_rows or [])]
    details: dict = {"n_got": len(got), "n_expected": len(exp),
                     "order_required": bool(order_required),
                     "column_permutation": False}
    if not exp and not got:
        details.update({"matched": 0, "score": 1.0})
        return 1.0, details
    if not exp or not got:
        details.update({"matched": 0, "score": 0.0})
        return 0.0, details
    if order_required and len(got) != len(exp):
        details.update({"matched": 0, "score": 0.0,
                        "reason": "ROW_COUNT_MISMATCH"})
        return 0.0, details
    w = len(exp[0])
    uniform = (w > 0 and all(len(r) == w for r in exp)
               and all(len(r) == w for r in got))
    if uniform and w <= 6:
        perms = sorted(itertools.permutations(range(w)),
                       key=lambda p: any(i != v for i, v in enumerate(p)))
        best_score, best_matched, best_nonident = -1.0, 0, False
        for perm in perms:
            nonident = any(i != v for i, v in enumerate(perm))
            pg = [[r[p] for p in perm] for r in got]
            if order_required:
                ok_p = all(all(_cells_equal(x, y, tol)
                               for x, y in zip(gr, er))
                           for gr, er in zip(pg, exp))
                score_p, matched_p = (1.0, len(exp)) if ok_p else (0.0, 0)
            else:
                matched_p, _ = _rows_equal_set(pg, exp, tol)
                pp = matched_p / len(pg) if pg else 0.0
                rr = matched_p / len(exp) if exp else 0.0
                score_p = 0.0 if (pp + rr) == 0 else 2 * pp * rr / (pp + rr)
                if matched_p == len(pg) == len(exp):
                    score_p = 1.0
            if score_p > best_score:
                best_score, best_matched, best_nonident = (
                    score_p, matched_p, nonident)
                if best_score == 1.0 and not best_nonident:
                    break  # identity already perfect; prefer it
        details.update({"matched": best_matched, "score": best_score,
                        "column_permutation": bool(best_nonident
                                                   and best_score == 1.0)})
        return best_score, details
    if order_required:
        ok = all(len(g) == len(e) and all(_cells_equal(x, y, tol) for x, y in zip(g, e))
                 for g, e in zip(got, exp))
        details.update({"matched": len(exp) if ok else 0, "score": 1.0 if ok else 0.0})
        return (1.0 if ok else 0.0), details
    matched, _ = _rows_equal_set(got, exp, tol)
    p = matched / len(got) if got else 0.0
    r = matched / len(exp) if exp else 0.0
    score = 0.0 if (p + r) == 0 else 2 * p * r / (p + r)
    if matched == len(got) == len(exp):
        score = 1.0
    details.update({"matched": matched, "score": score})
    return score, details

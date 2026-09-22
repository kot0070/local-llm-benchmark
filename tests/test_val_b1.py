"""Unit tests for TASK_B1 shared validators (jsonx, textmetrics, sqlx, pysandbox)."""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.validate import jsonx, pysandbox, sqlx
from bench.validate.textmetrics import cer, levenshtein, norm_text, token_f1, wer


def test_extract_json_strict():
    obj, info = jsonx.extract_json('{"a": 1, "b": [1, 2]}')
    assert obj == {"a": 1, "b": [1, 2]}
    assert info["strict"] and info["lenient"] and not info["prose"]


def test_extract_json_fenced_prose():
    obj, info = jsonx.extract_json('Here is the result:\n```json\n{"a": 1}\n```\nhope it helps')
    assert obj == {"a": 1}
    assert not info["strict"] and info["lenient"] and info["fenced"] and info["prose"]


def test_extract_json_none():
    obj, info = jsonx.extract_json('no json here at all (just words)')
    assert obj is None and not info["lenient"]


def test_compare_fields_all_kinds():
    got = {"e": 1, "c": "Hello", "n": 1.0000001, "t": "5", "d": "2024/03/05",
           "s": ["a", "b"], "sc": ["X", "y"], "z": None}
    exp = {"e": 1, "c": "hello", "n": 1.0, "t": 5.0, "d": "2024-03-05",
           "s": ["b", "a"], "sc": ["x", "Y"], "z": None}
    spec = {"e": "exact", "c": "ci", "n": "num", "t": "num_tol:0.1",
            "d": "date", "s": "set", "sc": "set_ci", "z": "null"}
    score, details = jsonx.compare_fields(got, exp, spec)
    assert score == 1.0, details


def test_compare_fields_missing_and_wrong():
    score, details = jsonx.compare_fields({"a": 1}, {"a": 1, "b": 2},
                                          {"a": "exact", "b": "exact"})
    assert score == 0.5
    assert details["b"]["missing"]
    score2, _ = jsonx.compare_fields({"a": 2}, {"a": 1}, {"a": "exact"})
    assert score2 == 0.0


def test_norm_text():
    assert norm_text("  Hello\tWORLD\n") == "hello world"


def test_levenshtein():
    assert levenshtein("", "") == 0
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("abc", "abc") == 0


def test_cer_wer():
    assert cer("hello", "hello") == 0.0
    assert cer("", "") == 0.0
    assert cer("", "x") == 1.0
    assert wer("a b c", "a b c") == 0.0
    assert wer("", "") == 0.0
    assert wer("a b", "a") == 0.5


def test_token_f1():
    assert token_f1("The Cat", "cat the") == 1.0
    assert token_f1("", "") == 1.0
    assert token_f1("a b", "c d") == 0.0
    assert 0.0 < token_f1("a b c", "a b d") < 1.0


def test_extract_sql_plain():
    sql, info = sqlx.extract_sql("SELECT a FROM t")
    assert sql == "SELECT a FROM t"
    assert info["strict"] and not info["prose"]


def test_extract_sql_fenced():
    sql, info = sqlx.extract_sql('Here you go:\n```sql\nSELECT a FROM t;\n```')
    assert sql == "SELECT a FROM t"
    assert info["fenced"] and info["prose"]


def test_extract_sql_empty():
    sql, _ = sqlx.extract_sql("   ")
    assert sql is None


def test_check_single_select():
    assert sqlx.check_single_select("SELECT 1")[0]
    assert sqlx.check_single_select("WITH x AS (SELECT 1) SELECT * FROM x")[0]
    assert not sqlx.check_single_select("SELECT 1; SELECT 2")[0]
    assert not sqlx.check_single_select("DROP TABLE t")[0]
    assert not sqlx.check_single_select("DELETE FROM t")[0]


def _make_db(path):
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE t (a INTEGER, b REAL, c TEXT)")
    con.execute("INSERT INTO t VALUES (1, 1.5, 'x')")
    con.execute("INSERT INTO t VALUES (2, NULL, 'y')")
    con.execute("INSERT INTO t VALUES (1, 1.5, 'x')")
    con.commit()
    con.close()


def test_execute_readonly_ok(tmp_path):
    db = tmp_path / "d.sqlite"
    _make_db(db)
    res = sqlx.execute_readonly(str(db), "SELECT a, b FROM t ORDER BY a")
    assert res["ok"] and len(res["rows"]) == 3


def test_execute_readonly_write_blocked(tmp_path):
    db = tmp_path / "d.sqlite"
    _make_db(db)
    res = sqlx.execute_readonly(str(db), "DROP TABLE t")
    assert not res["ok"]


def test_compare_rows_multiset_and_order():
    exp = [[1, "x"], [2, "y"]]
    got = [[2, "y"], [1, "x"]]
    s, _ = sqlx.compare_rows(got, exp, False)
    assert s == 1.0
    s2, _ = sqlx.compare_rows(got, exp, True)
    assert s2 == 0.0
    s3, _ = sqlx.compare_rows([[1.0000001, None]], [[1.0, None]], False)
    assert s3 == 1.0
    s4, _ = sqlx.compare_rows([[1]], [[1], [2]], False)
    assert 0.0 < s4 < 1.0


def test_compare_rows_column_permutation():
    exp = [[1, "x"], [2, "y"]]
    s, d = sqlx.compare_rows([["y", 2], ["x", 1]], exp, False)
    assert s == 1.0 and d["column_permutation"] is True
    s, d = sqlx.compare_rows([["x", 1], ["y", 2]], exp, True)
    assert s == 1.0 and d["column_permutation"] is True
    s, d = sqlx.compare_rows([[1, "x"], [2, "y"]], exp, False)
    assert s == 1.0 and d["column_permutation"] is False
    # Extra or missing columns stay wrong and unflagged.
    s, d = sqlx.compare_rows([[1, "x", 9], [2, "y", 9]], exp, False)
    assert s < 1.0 and d["column_permutation"] is False
    s, d = sqlx.compare_rows([[1], [2]], exp, False)
    assert s < 1.0 and d["column_permutation"] is False
    # Three-column rotation, ordered and unordered.
    e3 = [[1, 2, 3], [4, 5, 6]]
    s, d = sqlx.compare_rows([[3, 1, 2], [6, 4, 5]], e3, False)
    assert s == 1.0 and d["column_permutation"] is True
    s, d = sqlx.compare_rows([[3, 1, 2], [6, 4, 5]], e3, True)
    assert s == 1.0 and d["column_permutation"] is True
    s, d = sqlx.compare_rows([[3, 1, 2], [5, 6, 4]], e3, True)
    assert s == 0.0 and d["column_permutation"] is False


def test_sandbox_function_ok():
    out = pysandbox.run_function_tests("def add(a, b):\n return a + b\n", "add",
                                       [{"args": [1, 2], "expected": 3}])
    assert out["passed"] == 1 and out["error"] is None


def test_sandbox_blocked_import():
    out = pysandbox.run_function_tests("import os\ndef f():\n return 1\n", "f",
                                       [{"args": [], "expected": 1}])
    assert out["passed"] == 0
    assert "blocked import" in (out["error"] or "")


def test_sandbox_blocked_open():
    out = pysandbox.run_function_tests("def f():\n return open('x').read()\n", "f",
                                       [{"args": [], "expected": 1}])
    assert out["passed"] == 0


def test_sandbox_blocked_eval():
    out = pysandbox.run_function_tests("def f():\n return eval('1')\n", "f",
                                       [{"args": [], "expected": 1}])
    assert out["passed"] == 0


def test_sandbox_stdin():
    out = pysandbox.run_stdin_tests("line = input().strip()\nprint(line[::-1])\n",
                                    [{"stdin": "abc", "expected": "cba"}])
    assert out["passed"] == 1


def test_sandbox_timeout():
    out = pysandbox.run_function_tests("def f():\n while True:\n  pass\n", "f",
                                       [{"args": [], "expected": 1}], timeout_s=2)
    assert out["passed"] == 0
    assert out["error"] == "TIMEOUT"

"""HOME-20 text-to-SQL on local SQLite fixtures (owner: TASK_B1)."""
from __future__ import annotations

import json
import os
from pathlib import Path

from bench.types import (
    Case, FORMAT_ERROR, OK, Profile, Request, Response, Verdict, WRONG_ANSWER,
)
from bench.validate import sqlx

META = dict(
    id="HOME-20",
    version="n1",
    title="Text-to-SQL on retail/hr SQLite databases",
    family="SQL",
    home="sqlcoder:7b",
    kind="chat",
    mode="R0",
    requires=["text"],
    num_predict=384,
    think_extra=1024,
    num_ctx=4096,
    timeout_s=120,
    core_n=12,
    empty_ok=False,
)

SQLCODER_INSTRUCTIONS = (
    "### Instructions:\n"
    # defog template, dialect switched from Postgres to SQLite (our fixtures are SQLite)
    "Your task is to convert a question into a SQL query, given a SQLite database schema.\n"
    "Adhere to these rules:\n"
    "- The query must be valid SQLite: no ILIKE and no :: casts (use LIKE, CAST, strftime)\n"
    "- **Deliberately go through the question and database schema word by word**"
    " to appropriately answer the question\n"
    "- **Use Table Aliases** to prevent ambiguity. For example, "
    "`SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.\n"
    "- When creating a ratio, always cast the numerator as float\n"
)

CHAT_TEMPLATE = (
    "You convert questions to SQL for a SQLite database.\n"
    "Given the schema below, return only the SQL query, no explanation.\n"
    "Schema:\n{schema}\nQuestion: {question}\nSQL:"
)


def _db_path(db: str) -> str:
    override = os.environ.get("BENCH_FIXTURES_DIR")
    if override:
        return str(Path(override) / "HOME-20" / "assets" / db)
    return str(Path(__file__).resolve().parents[2] / "fixtures" / "HOME-20"
               / "assets" / db)


def load_cases(fixtures_dir: str) -> list[Case]:
    path = Path(fixtures_dir) / "cases.jsonl"  # runner passes fixtures/HOME-20
    if not path.is_file():  # tolerate the fixtures root as well
        path = Path(fixtures_dir) / "HOME-20" / "cases.jsonl"
    cases: list[Case] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(Case(id=d["id"], test_id=d["test_id"], tier=d.get("tier", ""),
                              lang=d.get("lang", "en"), input=d.get("input", {}),
                              expected=d.get("expected"), meta=d.get("meta", {})))
    return cases


def build_request(case: Case, profile: Profile) -> Request:
    question = case.input.get("question", "")
    schema = case.input.get("schema", "")
    adapters = getattr(profile, "adapters", {}) or {}
    if adapters.get("sqlcoder_raw"):
        prompt = (
            SQLCODER_INSTRUCTIONS
            + "\n### Input:\nGenerate a SQL query that answers the question "
            f"`{question}`.\n"
            "This query will run on a SQLite database whose schema is represented "
            f"in this string:\n{schema}\n\n### Response:\n"
            "Based on your instructions, here is the SQL query I have generated "
            f"to answer the question `{question}`:\n```sql\n"
        )
        return Request(endpoint="generate", prompt=prompt, raw=True,
                       options={"stop": ["<|endoftext|>", "```"]})
    return Request(endpoint="chat", messages=[{
        "role": "user",
        "content": CHAT_TEMPLATE.format(schema=schema, question=question)}])


def validate(case: Case, resp: Response, profile: Profile) -> Verdict:
    text = resp.content or ""
    exp = case.expected if isinstance(case.expected, dict) else {}
    exp_rows = exp.get("rows", [])
    order_required = bool(exp.get("order_required", False))
    db = case.input.get("db", exp.get("db", "retail.sqlite"))

    sql, info = sqlx.extract_sql(text)
    if sql is None:
        return Verdict(status=FORMAT_ERROR, sub_reason="NO_SQL", sem=0.0,
                       strict=0.0,
                       details={"parsed_sql": None, "n_got": 0,
                                "n_expected": len(exp_rows),
                                "order_required": order_required,
                                "prose": info["prose"], "fenced": info["fenced"]},
                       attribution="MODEL")
    res = sqlx.execute_readonly(_db_path(db), sql)
    if not res.get("ok"):
        sub = "DIALECT_ERROR" if res.get("dialect") else "EXEC_ERROR"
        if info["prose"]:
            return Verdict(status=FORMAT_ERROR, sub_reason="PROSE_AROUND_SQL",
                           sem=0.0, strict=0.0,
                           details={"parsed_sql": sql[:2000],
                                    "error": res.get("error"),
                                    "n_expected": len(exp_rows),
                                    "order_required": order_required,
                                    "prose": True}, attribution="MODEL")
        return Verdict(status=WRONG_ANSWER, sub_reason=sub, sem=0.0,
                       strict=0.0,
                       details={"parsed_sql": sql[:2000],
                                "error": res.get("error"),
                                "dialect": res.get("dialect"),
                                "n_expected": len(exp_rows),
                                "order_required": order_required,
                                "prose": False}, attribution="MODEL")
    score, cmp_details = sqlx.compare_rows(res.get("rows", []), exp_rows,
                                           order_required)
    if score == 1.0 and not info["prose"]:
        return Verdict(status=OK, sub_reason=None, sem=1.0, strict=1.0,
                       details={"parsed_sql": sql[:2000], "n_got": len(res["rows"]),
                                "n_expected": len(exp_rows),
                                "order_required": order_required,
                                "matched": cmp_details.get("matched"), "column_permutation": cmp_details.get("column_permutation", False),
                                "prose": False}, attribution="NONE")
    if score == 1.0:
        return Verdict(status=FORMAT_ERROR, sub_reason="PROSE_AROUND_SQL",
                       sem=1.0, strict=0.0,
                       details={"parsed_sql": sql[:2000], "n_got": len(res["rows"]),
                                "n_expected": len(exp_rows),
                                "order_required": order_required,
                                "matched": cmp_details.get("matched"), "column_permutation": cmp_details.get("column_permutation", False),
                                "prose": True}, attribution="MODEL")
    if info["prose"]:
        return Verdict(status=FORMAT_ERROR, sub_reason="PROSE_AROUND_SQL",
                       sem=score, strict=0.0,
                       details={"parsed_sql": sql[:2000], "n_got": len(res["rows"]),
                                "n_expected": len(exp_rows),
                                "order_required": order_required,
                                "matched": cmp_details.get("matched"), "column_permutation": cmp_details.get("column_permutation", False),
                                "prose": True}, attribution="MODEL")
    return Verdict(status=WRONG_ANSWER, sub_reason="WRONG_ROWS", sem=score,
                   strict=0.0,
                   details={"parsed_sql": sql[:2000], "n_got": len(res["rows"]),
                            "n_expected": len(exp_rows),
                            "order_required": order_required,
                            "matched": cmp_details.get("matched"), "column_permutation": cmp_details.get("column_permutation", False),
                            "prose": False}, attribution="MODEL")

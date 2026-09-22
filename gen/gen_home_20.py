"""Generator for HOME-20 (text-to-SQL, retail + hr SQLite). Owner: TASK_B1."""
from __future__ import annotations

import hashlib
import json
import random
import re
import sqlite3
from pathlib import Path

TEST_ID = "HOME-20"
SEED = 1420
VERSION = "n1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


RETAIL_SCHEMA = """CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  signup_date TEXT NOT NULL,
  referrer_id INTEGER
);
CREATE TABLE stores (
  id INTEGER PRIMARY KEY,
  city TEXT NOT NULL,
  opened_date TEXT NOT NULL
);
CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  price REAL NOT NULL
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  store_id INTEGER NOT NULL,
  order_date TEXT NOT NULL,
  discount REAL
);
CREATE TABLE order_items (
  id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  qty INTEGER NOT NULL,
  unit_price REAL NOT NULL
);"""

HR_SCHEMA = """CREATE TABLE departments (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  location TEXT NOT NULL
);
CREATE TABLE employees (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  dept_id INTEGER,
  hire_date TEXT NOT NULL,
  salary REAL NOT NULL,
  manager_id INTEGER
);
CREATE TABLE projects (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  dept_id INTEGER NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT
);
CREATE TABLE assignments (
  employee_id INTEGER NOT NULL,
  project_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  hours INTEGER NOT NULL
);
CREATE TABLE leaves (
  id INTEGER PRIMARY KEY,
  employee_id INTEGER NOT NULL,
  start_date TEXT NOT NULL,
  days INTEGER NOT NULL
);"""


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA journal_mode=DELETE")
    return con


def build_retail(path: Path) -> None:
    rng = random.Random(SEED + 1)
    if path.exists():
        path.unlink()
    con = _connect(path)
    con.executescript(RETAIL_SCHEMA)
    first = ["Anna", "Ben", "Cleo", "Dan", "Eva", "Felix", "Greta", "Hugo", "Iris",
             "Jonas", "Klara", "Leo"]
    last = ["Muller", "Schmidt", "Weber", "Fischer", "Meyer", "Wagner", "Becker",
            "Schulz", "Hoffmann", "Koch", "Richter", "Wolf"]
    cities = ["Berlin", "Munich", "Hamburg", "Cologne"]
    customers = []
    for i in range(12):
        name = f"{first[i]} {last[i]}"
        city = cities[i % len(cities)]
        signup = f"2023-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        ref = None if i % 3 == 0 else rng.randint(1, i)
        customers.append((i + 1, name, city, signup, ref))
    con.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)
    stores = [(1, "Berlin", "2022-01-10"), (2, "Munich", "2022-06-01"),
              (3, "Hamburg", "2023-03-15")]
    con.executemany("INSERT INTO stores VALUES (?,?,?)", stores)
    products = [(1, "Coffee Maker", "Kitchen", 89.99),
                (2, "Tea Kettle", "Kitchen", 34.50),
                (3, "Blender", "Kitchen", 59.00),
                (4, "Desk Lamp", "Office", 24.99),
                (5, "Notebook Set", "Office", 12.50),
                (6, "Yoga Mat", "Sports", 29.99),
                (7, "Dumbbell Pair", "Sports", 49.99),
                (8, "Water Bottle", "Sports", 15.00)]
    con.executemany("INSERT INTO products VALUES (?,?,?,?)", products)
    orders, items = [], []
    iid = 1
    for i in range(24):
        oid = i + 1
        cust = rng.randint(1, 12)
        store = rng.randint(1, 3)
        year = 2024 if i % 3 != 0 else 2023
        date = f"{year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        disc = None if i % 4 == 0 else round(rng.choice([5.0, 10.0, 15.0]), 2)
        orders.append((oid, cust, store, date, disc))
        for _ in range(rng.randint(1, 3)):
            if iid > 60:
                break
            # Product 8 (Water Bottle) is never ordered: NOT EXISTS target.
            pid = rng.randint(1, 7)
            qty = rng.randint(1, 4)
            price = next(p[3] for p in products if p[0] == pid)
            items.append((iid, oid, pid, qty, price))
            iid += 1
    con.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)
    con.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)
    # Force a revenue tie between Tea Kettle (2) and Blender (3): mirror items.
    con.execute("DELETE FROM order_items WHERE product_id = 3")
    rows = con.execute(
        "SELECT order_id, qty, unit_price FROM order_items WHERE product_id = 2").fetchall()
    assert rows, "no Tea Kettle items to mirror"
    for oid, qty, price in rows:
        con.execute("INSERT INTO order_items (order_id, product_id, qty, unit_price)"
                    " VALUES (?,?,?,?)", (oid, 3, qty, 59.00))
    con.commit()
    con.close()


def build_hr(path: Path) -> None:
    rng = random.Random(SEED + 2)
    if path.exists():
        path.unlink()
    con = _connect(path)
    con.executescript(HR_SCHEMA)
    depts = [(1, "Engineering", "Berlin"), (2, "Sales", "Munich"), (3, "Support", "Hamburg")]
    con.executemany("INSERT INTO departments VALUES (?,?,?)", depts)
    names = ["Anna Berger", "Ben Clark", "Cleo Davis", "Dan Evans", "Eva Frank",
             "Felix Grant", "Greta Hill", "Hugo Irving", "Iris Jones", "Jonas Klein",
             "Klara Lane", "Leo Marsh"]
    employees = []
    for i, name in enumerate(names):
        eid = i + 1
        dept = None if eid == 12 else (i % 3) + 1
        year = 2023 if i % 3 != 2 else (2022 if i % 2 == 0 else 2024)
        hire = f"{year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        salary = round(rng.choice([50000, 55000, 60000, 65000, 70000, 75000, 80000]), 2)
        mgr = None if eid in (1, 4, 12) else ((eid - 2) % 11) + 1
        employees.append((eid, name, dept, hire, salary, mgr))
    con.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)", employees)
    projects = [(1, "Atlas", 1, "2024-01-15", "2024-06-30"),
                (2, "Beacon", 2, "2024-02-01", None),
                (3, "Comet", 1, "2023-09-01", "2024-01-31"),
                (4, "Drift", 3, "2024-03-10", None),
                (5, "Ember", 2, "2023-11-05", "2024-02-29")]
    con.executemany("INSERT INTO projects VALUES (?,?,?,?,?)", projects)
    roles = ["lead", "member", "reviewer"]
    asg = []
    # Employees 11 and 12 are never assigned: NOT EXISTS targets.
    for eid in range(1, 11):
        for pid in rng.sample([1, 2, 3, 4, 5], rng.randint(1, 2)):
            asg.append((eid, pid, rng.choice(roles), rng.randint(10, 120)))
    con.executemany("INSERT INTO assignments VALUES (?,?,?,?)", asg)
    leaves = [(1, 2, "2024-01-08", 5), (2, 5, "2024-02-12", 3),
              (3, 7, "2024-03-04", 10), (4, 3, "2023-12-18", 2),
              (5, 9, "2024-01-22", 7)]
    con.executemany("INSERT INTO leaves VALUES (?,?,?,?)", leaves)
    con.commit()
    con.close()


RETAIL_Q = [
    ("Which customers bought the product 'Coffee Maker'? Return customer names.",
     "SELECT c.name FROM customers c JOIN orders o ON o.customer_id = c.id "
     "JOIN order_items i ON i.order_id = o.id JOIN products p ON p.id = i.product_id "
     "WHERE p.name = 'Coffee Maker' ORDER BY c.name", False, "join"),
    ("List order ids placed in 2024 that have a discount, ordered by id.",
     "SELECT id FROM orders WHERE strftime('%Y', order_date) = '2024' "
     "AND discount IS NOT NULL ORDER BY id", True, "date+null"),
    ("Which products sold more than 10 units in total? Return product names.",
     "SELECT p.name FROM products p JOIN order_items i ON i.product_id = p.id "
     "GROUP BY p.id, p.name HAVING SUM(i.qty) > 10 ORDER BY p.name", False, "group-by"),
    ("Total revenue (qty * unit_price) per store city, highest revenue first.",
     "SELECT s.city, SUM(i.qty * i.unit_price) AS revenue FROM stores s "
     "JOIN orders o ON o.store_id = s.id JOIN order_items i ON i.order_id = o.id "
     "GROUP BY s.city ORDER BY revenue DESC, s.city", True, "group-by"),
    ("Customers whose total spending exceeds 300. Return names.",
     "SELECT c.name FROM customers c WHERE "
     "(SELECT COALESCE(SUM(i.qty * i.unit_price), 0) FROM orders o "
     "JOIN order_items i ON i.order_id = o.id WHERE o.customer_id = c.id) > 300 "
     "ORDER BY c.name", False, "subquery"),
    ("Which products were never ordered? Return product names.",
     "SELECT p.name FROM products p WHERE NOT EXISTS "
     "(SELECT 1 FROM order_items i WHERE i.product_id = p.id) ORDER BY p.name",
     False, "not-exists"),
    ("For each customer, their latest order id and date (one row per customer).",
     "SELECT customer_id, id, order_date FROM (SELECT o.customer_id, o.id, o.order_date, "
     "ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date DESC, o.id DESC) AS rn "
     "FROM orders o) WHERE rn = 1 ORDER BY customer_id", False, "window"),
    ("Customers with no referrer. Return names.",
     "SELECT name FROM customers WHERE referrer_id IS NULL ORDER BY name",
     False, "null"),
    ("Rank products by total revenue (highest first) using RANK. Return rank, name.",
     "SELECT RANK() OVER (ORDER BY SUM(i.qty * i.unit_price) DESC) AS rnk, p.name "
     "FROM products p JOIN order_items i ON i.product_id = p.id "
     "GROUP BY p.id, p.name ORDER BY rnk, p.name", True, "window-rank"),
    ("Number of orders per store city.",
     "SELECT s.city, COUNT(*) AS n FROM stores s JOIN orders o ON o.store_id = s.id "
     "GROUP BY s.city ORDER BY s.city", False, "group-by"),
]

HR_Q = [
    ("Employee names with their department names, including employees without a department.",
     "SELECT e.name, d.name FROM employees e LEFT JOIN departments d "
     "ON d.id = e.dept_id ORDER BY e.name", False, "join"),
    ("Employees with no manager. Return names.",
     "SELECT name FROM employees WHERE manager_id IS NULL ORDER BY name",
     False, "null"),
    ("Employees hired in 2023. Return names.",
     "SELECT name FROM employees WHERE strftime('%Y', hire_date) = '2023' ORDER BY name",
     False, "date"),
    ("Departments with more than 3 employees. Return department names.",
     "SELECT d.name FROM departments d JOIN employees e ON e.dept_id = d.id "
     "GROUP BY d.id, d.name HAVING COUNT(*) > 3 ORDER BY d.name", False, "group-by"),
    ("Employees earning more than the average salary of their department. Return names.",
     "SELECT e.name FROM employees e WHERE e.dept_id IS NOT NULL AND e.salary > "
     "(SELECT AVG(e2.salary) FROM employees e2 WHERE e2.dept_id = e.dept_id) "
     "ORDER BY e.name", False, "subquery"),
    ("Employees assigned to no project. Return names.",
     "SELECT e.name FROM employees e WHERE NOT EXISTS "
     "(SELECT 1 FROM assignments a WHERE a.employee_id = e.id) ORDER BY e.name",
     False, "not-exists"),
    ("Highest-paid employee per department: department name, employee name, salary.",
     "SELECT dept, name, salary FROM (SELECT d.name AS dept, e.name AS name, e.salary, "
     "ROW_NUMBER() OVER (PARTITION BY e.dept_id ORDER BY e.salary DESC, e.id) AS rn "
     "FROM employees e JOIN departments d ON d.id = e.dept_id) WHERE rn = 1 "
     "ORDER BY dept", False, "window"),
    ("Employees who started a leave in the first quarter of 2024. Return names.",
     "SELECT DISTINCT e.name FROM employees e JOIN leaves l ON l.employee_id = e.id "
     "WHERE l.start_date >= '2024-01-01' AND l.start_date < '2024-04-01' ORDER BY e.name",
     False, "date"),
    ("Total assigned hours per project name, highest hours first.",
     "SELECT p.name, SUM(a.hours) AS total_hours FROM projects p "
     "JOIN assignments a ON a.project_id = p.id GROUP BY p.id, p.name "
     "ORDER BY total_hours DESC, p.name", True, "group-by"),
    ("Ongoing projects (no end date). Return names ordered by start date.",
     "SELECT name FROM projects WHERE end_date IS NULL ORDER BY start_date, name",
     True, "null"),
]


_ORDER_RE = re.compile(
    r"(?i)\border(ed)?\s+by\b|highest\b.{0,40}\bfirst\b"
    r"|lowest\b.{0,40}\bfirst\b|\btop\s+\d+\b")


def asks_order(question: str) -> bool:
    """True only when the question explicitly asks for an order."""
    return bool(_ORDER_RE.search(question or ""))


def _question_text(db: str, question: str, schema: str) -> str:
    return (f"Database: {db}\nSchema (SQLite):\n{schema}\n"
            f"Question: {question}\nReturn only the SQL query.")


def build_cases(assets: Path):
    retail_db = assets / "retail.sqlite"
    hr_db = assets / "hr.sqlite"
    build_retail(retail_db)
    build_hr(hr_db)
    tiers_retail = ["easy", "easy", "medium", "medium", "medium", "hard",
                    "hard", "easy", "medium", "easy"]
    tiers_hr = ["easy", "easy", "easy", "medium", "medium", "hard",
                "hard", "medium", "medium", "easy"]
    cases: list[dict] = []
    for db_name, db_path, schema, qs, tiers in (
            ("retail.sqlite", retail_db, RETAIL_SCHEMA, RETAIL_Q, tiers_retail),
            ("hr.sqlite", hr_db, HR_SCHEMA, HR_Q, tiers_hr)):
        con = sqlite3.connect(str(db_path))
        for k, (question, sql, order_required, kind) in enumerate(qs):
            assert bool(order_required) == asks_order(question), \
                f"order_required mismatch for {db_name} Q{k + 1}: {question!r}"
            rows1 = con.execute(sql).fetchall()
            rows2 = con.execute(sql).fetchall()
            assert rows1, f"oracle returned empty for {db_name} Q{k + 1}"
            assert [list(r) for r in rows1] == [list(r) for r in rows2], \
                f"nondeterministic oracle for {db_name} Q{k + 1}"
            tier = tiers[k]
            cases.append({
                "id": f"tmp-{db_name}-{k}",
                "test_id": TEST_ID,
                "tier": tier,
                "lang": "en",
                "input": {"db": db_name,
                          "question": question,
                          "schema": schema,
                          "prompt": _question_text(db_name, question, schema)},
                "expected": {"rows": [list(r) for r in rows1],
                             "order_required": order_required,
                             "db": db_name,
                             "gold_sql": sql},
                "meta": {"kind": kind},
            })
        con.close()
    # Stratified interleave by tier across both DBs.
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for c in cases:
        by_tier[c["tier"]].append(c)
    ordered: list[dict] = []
    lists = [by_tier["easy"], by_tier["medium"], by_tier["hard"]]
    while any(lists):
        for lst in lists:
            if lst:
                ordered.append(lst.pop(0))
    for j, c in enumerate(ordered):
        c["id"] = f"HOME-20-{j + 1:02d}"
    return ordered


def main() -> Path:
    out_dir = Path(__file__).resolve().parents[1] / "fixtures" / TEST_ID
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    cases = build_cases(assets)
    assert len(cases) == 20, len(cases)
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for c in cases:
        counts[c["tier"]] += 1
    assert sum(counts.values()) == 20
    cases_path = out_dir / "cases.jsonl"
    with open(cases_path, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, sort_keys=True, ensure_ascii=False) + "\n")
    files = {"cases.jsonl": sha256_file(cases_path)}
    for p in sorted(assets.iterdir()):
        if p.is_file():
            files[f"assets/{p.name}"] = sha256_file(p)
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_20.py",
                "version": VERSION, "n_cases": len(cases), "files": files}
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return out_dir


if __name__ == "__main__":
    print(main())

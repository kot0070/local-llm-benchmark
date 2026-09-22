"""Unit tests for retrieval metrics + MockEnv (owner: TASK_C)."""
import math

from bench.validate.retrieval import ndcg_at_k, recall_at_k, reciprocal_rank, mrr, cosine_sim
from bench.tests._mockenv import MockEnv


def test_ndcg_perfect():
    ranked = ["a", "b", "c"]
    q = {"a": 2, "b": 1}
    assert abs(ndcg_at_k(ranked, q, 10) - 1.0) < 1e-9


def test_ndcg_partial():
    ranked = ["b", "x", "a"]  # grade-1 first, grade-2 third
    q = {"a": 2, "b": 1}
    v = ndcg_at_k(ranked, q, 10)
    assert 0.0 < v < 1.0


def test_ndcg_none():
    assert ndcg_at_k(["x", "y"], {"a": 2}, 10) == 0.0
    assert ndcg_at_k(["x"], {}, 10) == 0.0


def test_recall():
    assert recall_at_k(["a", "x", "b"], {"a": 2, "b": 1}, 2) == 0.5
    assert recall_at_k(["a", "b"], {"a": 2, "b": 1}, 10) == 1.0
    assert recall_at_k(["x"], {}, 5) == 0.0


def test_rr_mrr():
    assert reciprocal_rank(["x", "a"], {"a": 1}) == 0.5
    assert reciprocal_rank(["x"], {"a": 1}) == 0.0
    assert abs(mrr([["a"], ["x", "b"]], [{"a": 1}, {"b": 1}]) - 0.75) < 1e-9


def test_cosine():
    assert abs(cosine_sim([1, 0], [0, 1])) < 1e-9
    assert abs(cosine_sim([1, 1], [1, 1]) - 1.0) < 1e-9
    assert cosine_sim([], []) == 0.0


def test_mockenv_basic():
    env = MockEnv()
    r = env.call("get_customer", {"email": "alice@example.com"})
    assert r["ok"] and r["customer_id"] == "C001"
    r = env.call("get_customer", {})
    assert not r["ok"]
    r = env.call("convert_currency", {"amount": 100, "from": "USD", "to": "EUR"})
    assert r["ok"] and r["converted"] == 92.0
    r = env.call("get_weather", {"city": "Paris", "unit": "celsius"})
    assert r["ok"] and r["temp"] == 18.0
    r = env.call("nope", {})
    assert not r["ok"]


def test_mockenv_mutation():
    env = MockEnv()
    r = env.call("cancel_order", {"order_id": "ORD-1005"})
    assert r["ok"] and env.snapshot()["orders"]["ORD-1005"] == "cancelled"
    r = env.call("cancel_order", {"order_id": "ORD-1004"})
    assert not r["ok"]  # delivered cannot cancel
    r = env.call("send_email", {"to": "a@b.com", "subject": "s", "body": "b"})
    assert r["ok"] and len(env.sent_emails) == 1

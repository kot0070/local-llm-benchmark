"""Deterministic in-memory tool environment for HOME-18 / HOME-21 (owner: TASK_C).

Tools (JSON-schema parameters):
  get_customer(email or customer_id), list_orders(customer_id, status?),
  get_order(order_id), compute_refund(order_id, reason),
  create_ticket(customer_id, subject, priority),
  cancel_order(order_id) [mutation], send_email(to, subject, body) [mutation],
  convert_currency(amount, from, to), get_weather(city, unit).
Records calls, returns JSON-serializable dicts, errors on bad args.
Stdlib only.
"""
from __future__ import annotations

import copy
import re

MUTATING = {"cancel_order", "send_email"}

_RATES = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "UAH": 41.5, "JPY": 149.0}
_WEATHER = {
    "London": {"temp_c": 15.0, "condition": "cloudy"},
    "Paris": {"temp_c": 18.0, "condition": "sunny"},
    "Kyiv": {"temp_c": 12.0, "condition": "rainy"},
    "Madrid": {"temp_c": 24.0, "condition": "sunny"},
    "Berlin": {"temp_c": 14.0, "condition": "windy"},
    "Rome": {"temp_c": 22.0, "condition": "clear"},
}
_REFUND_REASONS = {"damaged", "defective", "late", "customer_request", "other"}
_PRIORITIES = {"low", "medium", "high", "urgent"}
_ORDER_STATUS = {"pending", "paid", "shipped", "delivered", "cancelled"}

_TOOLS = [
    {"type": "function", "function": {"name": "get_customer", "description": "Look up a customer by email or customer_id.",
     "parameters": {"type": "object", "properties": {"email": {"type": "string"}, "customer_id": {"type": "string"}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "list_orders", "description": "List orders for a customer, optionally filtered by status.",
     "parameters": {"type": "object", "properties": {"customer_id": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "paid", "shipped", "delivered", "cancelled"]}}, "required": ["customer_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_order", "description": "Get order details by order_id.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "compute_refund", "description": "Compute refund amount for an order.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}, "reason": {"type": "string", "enum": ["damaged", "defective", "late", "customer_request", "other"]}}, "required": ["order_id", "reason"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "create_ticket", "description": "Create a support ticket.",
     "parameters": {"type": "object", "properties": {"customer_id": {"type": "string"}, "subject": {"type": "string"}, "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}}, "required": ["customer_id", "subject", "priority"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "cancel_order", "description": "Cancel an order (mutation). Requires explicit user request.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "send_email", "description": "Send an email (mutation).",
     "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "convert_currency", "description": "Convert an amount between currencies.",
     "parameters": {"type": "object", "properties": {"amount": {"type": "number"}, "from": {"type": "string", "enum": ["USD", "EUR", "GBP", "UAH", "JPY"]}, "to": {"type": "string", "enum": ["USD", "EUR", "GBP", "UAH", "JPY"]}}, "required": ["amount", "from", "to"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_weather", "description": "Get current weather for a city.",
     "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}}, "required": ["city"], "additionalProperties": False}}},
]


class MockEnv:
    """Deterministic fake shop environment."""

    TOOLS = _TOOLS
    MUTATING = MUTATING

    def __init__(self, seed: int = 0):
        self.seed = seed
        self.customers = {
            "C001": {"customer_id": "C001", "name": "Alice Anderson", "email": "alice@example.com"},
            "C002": {"customer_id": "C002", "name": "Bob Brown", "email": "bob@example.com"},
            "C003": {"customer_id": "C003", "name": "Carla Costa", "email": "carla@example.com"},
            "C004": {"customer_id": "C004", "name": "Dmytro Dovzhenko", "email": "dmytro@example.com"},
        }
        self.orders = {
            "ORD-1001": {"order_id": "ORD-1001", "customer_id": "C001", "status": "paid", "total": 120.00, "currency": "USD", "items": ["book", "lamp"]},
            "ORD-1002": {"order_id": "ORD-1002", "customer_id": "C001", "status": "shipped", "total": 59.99, "currency": "USD", "items": ["mug"]},
            "ORD-1003": {"order_id": "ORD-1003", "customer_id": "C002", "status": "paid", "total": 250.00, "currency": "USD", "items": ["chair"]},
            "ORD-1004": {"order_id": "ORD-1004", "customer_id": "C002", "status": "delivered", "total": 89.50, "currency": "USD", "items": ["desk lamp", "cable"]},
            "ORD-1005": {"order_id": "ORD-1005", "customer_id": "C003", "status": "pending", "total": 199.99, "currency": "USD", "items": ["headphones"]},
            "ORD-1006": {"order_id": "ORD-1006", "customer_id": "C003", "status": "paid", "total": 45.00, "currency": "USD", "items": ["notebook"]},
            "ORD-1007": {"order_id": "ORD-1007", "customer_id": "C004", "status": "shipped", "total": 320.75, "currency": "USD", "items": ["monitor"]},
            "ORD-1008": {"order_id": "ORD-1008", "customer_id": "C001", "status": "delivered", "total": 15.25, "currency": "USD", "items": ["pen set"]},
        }
        self.tickets: list[dict] = []
        self.sent_emails: list[dict] = []
        self.calls: list[dict] = []
        self._ticket_seq = 0

    @classmethod
    def get_tools(cls) -> list[dict]:
        return copy.deepcopy(cls.TOOLS)

    @classmethod
    def tool_schemas(cls) -> dict:
        out = {}
        for t in cls.TOOLS:
            fn = t["function"]
            out[fn["name"]] = fn.get("parameters", {})
        return out

    # -- dispatch -----------------------------------------------------
    def call(self, name: str, arguments: dict):
        args = arguments if isinstance(arguments, dict) else {}
        result = self._dispatch(name, args)
        self.calls.append({"name": name, "arguments": copy.deepcopy(args), "result": copy.deepcopy(result)})
        return result

    def _dispatch(self, name: str, args: dict):
        if name == "get_customer":
            return self._get_customer(args)
        if name == "list_orders":
            return self._list_orders(args)
        if name == "get_order":
            return self._get_order(args)
        if name == "compute_refund":
            return self._compute_refund(args)
        if name == "create_ticket":
            return self._create_ticket(args)
        if name == "cancel_order":
            return self._cancel_order(args)
        if name == "send_email":
            return self._send_email(args)
        if name == "convert_currency":
            return self._convert(args)
        if name == "get_weather":
            return self._weather(args)
        return {"ok": False, "error": f"unknown tool '{name}'"}

    def _get_customer(self, args: dict):
        email = args.get("email")
        cid = args.get("customer_id")
        if not email and not cid:
            return {"ok": False, "error": "provide 'email' or 'customer_id'"}
        if cid and cid in self.customers:
            return {"ok": True, **copy.deepcopy(self.customers[cid])}
        if email:
            for c in self.customers.values():
                if str(c["email"]).casefold() == str(email).strip().casefold():
                    return {"ok": True, **copy.deepcopy(c)}
            return {"ok": False, "error": f"customer not found for email '{email}'"}
        return {"ok": False, "error": f"customer not found for id '{cid}'"}

    def _list_orders(self, args: dict):
        cid = args.get("customer_id")
        if not cid or not isinstance(cid, str):
            return {"ok": False, "error": "missing required 'customer_id'"}
        if cid not in self.customers:
            return {"ok": False, "error": f"unknown customer_id '{cid}'"}
        status = args.get("status")
        if status is not None and status not in _ORDER_STATUS:
            return {"ok": False, "error": f"bad status '{status}'"}
        rows = [copy.deepcopy(o) for o in self.orders.values() if o["customer_id"] == cid]
        if status is not None:
            rows = [o for o in rows if o["status"] == status]
        rows.sort(key=lambda o: o["order_id"])
        return {"ok": True, "customer_id": cid, "orders": rows}

    def _get_order(self, args: dict):
        oid = args.get("order_id")
        if not oid or not isinstance(oid, str):
            return {"ok": False, "error": "missing required 'order_id'"}
        if oid not in self.orders:
            return {"ok": False, "error": f"unknown order_id '{oid}'"}
        return {"ok": True, **copy.deepcopy(self.orders[oid])}

    def _compute_refund(self, args: dict):
        oid = args.get("order_id")
        reason = args.get("reason")
        if not oid or not isinstance(oid, str):
            return {"ok": False, "error": "missing required 'order_id'"}
        if reason not in _REFUND_REASONS:
            return {"ok": False, "error": f"bad reason '{reason}'"}
        if oid not in self.orders:
            return {"ok": False, "error": f"unknown order_id '{oid}'"}
        total = float(self.orders[oid]["total"])
        if reason in ("damaged", "defective", "customer_request"):
            amt = round(total, 2)
        elif reason == "late":
            amt = round(total * 0.10, 2)
        else:
            amt = 0.0
        return {"ok": True, "order_id": oid, "reason": reason, "refund_amount": amt, "currency": "USD"}

    def _create_ticket(self, args: dict):
        cid = args.get("customer_id")
        subject = args.get("subject")
        priority = args.get("priority")
        if not cid or cid not in self.customers:
            return {"ok": False, "error": f"unknown customer_id '{cid}'"}
        if not subject or not isinstance(subject, str) or not subject.strip():
            return {"ok": False, "error": "missing required 'subject'"}
        if priority not in _PRIORITIES:
            return {"ok": False, "error": f"bad priority '{priority}'"}
        self._ticket_seq += 1
        tid = f"TICKET-{self._ticket_seq:03d}"
        t = {"ticket_id": tid, "customer_id": cid, "subject": subject.strip(), "priority": priority}
        self.tickets.append(copy.deepcopy(t))
        return {"ok": True, **copy.deepcopy(t)}

    def _cancel_order(self, args: dict):
        oid = args.get("order_id")
        if not oid or not isinstance(oid, str):
            return {"ok": False, "error": "missing required 'order_id'"}
        if oid not in self.orders:
            return {"ok": False, "error": f"unknown order_id '{oid}'"}
        st = self.orders[oid]["status"]
        if st in ("delivered", "cancelled"):
            return {"ok": False, "error": f"cannot cancel order in status '{st}'"}
        self.orders[oid]["status"] = "cancelled"
        return {"ok": True, "order_id": oid, "status": "cancelled"}

    def _send_email(self, args: dict):
        to = args.get("to")
        subject = args.get("subject")
        body = args.get("body")
        if not to or not isinstance(to, str) or "@" not in to:
            return {"ok": False, "error": "bad 'to' email"}
        if not subject or not isinstance(subject, str) or not subject.strip():
            return {"ok": False, "error": "missing required 'subject'"}
        if not body or not isinstance(body, str) or not body.strip():
            return {"ok": False, "error": "missing required 'body'"}
        rec = {"to": to.strip(), "subject": subject.strip(), "body": body}
        self.sent_emails.append(copy.deepcopy(rec))
        return {"ok": True, "sent": True, **copy.deepcopy(rec)}

    def _convert(self, args: dict):
        try:
            amount = float(args.get("amount"))
        except Exception:
            return {"ok": False, "error": "bad 'amount'"}
        fr = args.get("from")
        to = args.get("to")
        if fr not in _RATES or to not in _RATES:
            return {"ok": False, "error": f"bad currency '{fr}'->'{to}'"}
        usd = amount / _RATES[fr]
        out = round(usd * _RATES[to], 2)
        return {"ok": True, "amount": amount, "from": fr, "to": to, "converted": out}

    def _weather(self, args: dict):
        city = args.get("city")
        unit = args.get("unit", "celsius")
        if not city or not isinstance(city, str):
            return {"ok": False, "error": "missing required 'city'"}
        key = None
        for k in _WEATHER:
            if k.casefold() == str(city).strip().casefold():
                key = k
                break
        if key is None:
            return {"ok": False, "error": f"unknown city '{city}'"}
        if unit not in ("celsius", "fahrenheit"):
            return {"ok": False, "error": f"bad unit '{unit}'"}
        w = _WEATHER[key]
        t = float(w["temp_c"])
        if unit == "fahrenheit":
            t = round(t * 9.0 / 5.0 + 32.0, 1)
        return {"ok": True, "city": key, "unit": unit, "temp": t, "condition": w["condition"]}

    # -- inspection ---------------------------------------------------
    def snapshot(self) -> dict:
        return {
            "orders": {k: v["status"] for k, v in sorted(self.orders.items())},
            "tickets": copy.deepcopy(self.tickets),
            "sent_emails": copy.deepcopy(self.sent_emails),
        }

    def mutation_names(self) -> list[str]:
        return [c["name"] for c in self.calls if c["name"] in MUTATING]

    @staticmethod
    def valid_email(s: str) -> bool:
        return isinstance(s, str) and bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s.strip()))

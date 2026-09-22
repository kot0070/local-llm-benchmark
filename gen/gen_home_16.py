"""Generator for HOME-16 routing (owner: TASK_B2). Seeded, self-verifying."""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

TEST_ID = "HOME-16"
SEED = 161616
ROUTES = ["ACCOUNT", "BILLING", "DELIVERY", "TECH", "SALES", "RETENTION", "SAFETY", "LEGAL", "HR", "IT_ACCESS", "ESCALATE"]
ID_QUEUES = {"ACCOUNT", "BILLING", "DELIVERY", "TECH", "IT_ACCESS"}
ID_RE = re.compile(r"\b(ORD|ACC|INV|TCK|EMP|DEV|BILL|AUTH)-\d+\b")

POLICY = """Helios Customer Request Routing Policy v3 (effective 2026-08-01, 412 tokens).

Queues: ACCOUNT (login, password, profile), BILLING (invoices, charges, refunds), DELIVERY (tracking, parcels),
TECH (devices, errors, connectivity), SALES (prices, demos, quotes), RETENTION (cancellations, leaving),
SAFETY (self-harm, violence, threats), LEGAL (lawsuits, GDPR, courts), HR (payroll, leave, hiring),
IT_ACCESS (VPN, corporate laptop, SSH).

Priority rules (apply in order, first match wins):
R1 SAFETY first: any mention of self-harm, suicide, physical attack or threat routes to SAFETY (reason SAFETY_PRIORITY),
  regardless of other topics. Never delay safety cases.
R2 LEGAL second: words like lawsuit, court, lawyer, GDPR, subpoena route to LEGAL (reason LEGAL_PRIORITY).
R3 RETENTION third: an explicit request to cancel, close the account or switch to a competitor routes to
  RETENTION (reason RETENTION_REQUEST), even if billing or delivery words also appear.
R4 Missing identifier: ACCOUNT, BILLING, DELIVERY, TECH and IT_ACCESS requests must contain a reference
  identifier such as ORD-123, ACC-123, INV-123, TCK-123, EMP-123 or DEV-123. If no identifier is present,
  route to ESCALATE with reason MISSING_ID so an agent can collect it.
R5 Keyword mapping otherwise: invoice/charged/refund/billing -> BILLING; tracking/parcel/delivery/shipment -> DELIVERY;
  login/password/account access -> ACCOUNT; error/crash/bug/not working/router -> TECH; price/demo/buy/quote -> SALES;
  payroll/payslip/vacation/maternity -> HR; VPN/laptop access/corporate access/SSH -> IT_ACCESS.
  Ukrainian equivalents apply equally (рахунок, доставка, пароль, помилка, ціна, зарплата, доступ).
R6 If no rule matches, route to ESCALATE with reason AMBIGUOUS.
Always return exactly one route plus the reason code of the rule that fired.

Identifier formats: order numbers look like ORD-71002, account numbers like ACC-71003, invoices like INV-71001,
tickets like TCK-1188, employee numbers like EMP-71009, device tags like DEV-71004. Any one of these counts
as a valid reference identifier for R4. A bare first name, a date, or a product name alone is not enough.
Examples: 'Where is parcel ORD-110? Tracking is stuck' -> DELIVERY, reason KEYWORD_DELIVERY. 'Refund invoice
INV-220 without delay' (no, with INV-220 present) -> BILLING. 'Refund the extra charge' with no code at all
-> ESCALATE, reason MISSING_ID. 'Cancel everything, I quit' -> RETENTION even when billing words appear.
'I will sue over this invoice INV-330' -> LEGAL because R2 outranks billing keywords. 'I want to hurt myself'
-> SAFETY immediately, no other rule is consulted. 'How many vacation days remain' -> HR, reason KEYWORD_HR.
'Give me a quote for ten kettles' -> SALES, reason KEYWORD_SALES. 'VPN asks for a new ssh key EMP-99' -> IT_ACCESS.
'My password does not work ACC-12' -> ACCOUNT. 'The screen shows error E-9 DEV-77' -> TECH.
Reason codes in full: SAFETY_PRIORITY, LEGAL_PRIORITY, RETENTION_REQUEST, MISSING_ID, KEYWORD_BILLING,
KEYWORD_DELIVERY, KEYWORD_ACCOUNT, KEYWORD_TECH, KEYWORD_SALES, KEYWORD_HR, KEYWORD_IT_ACCESS, AMBIGUOUS.
When several keywords from the same level appear, use the first queue listed in R5. Do not invent new routes
or new reason codes. If the request mixes Ukrainian and English, apply the same rules to both languages.
Escalated cases go to a human generalist with the full message attached, so never drop context when escalating."""

POLICY_SHA256 = hashlib.sha256(POLICY.encode("utf-8")).hexdigest()

KW = [
    ("SAFETY", ["kill myself", "suicide", "self-harm", "hurt myself", "physical attack", "threaten to come",
                "better off without me", "don't want to be here",
                "самогубство", "заподіяти собі", "погрож", "напад", "краще без мене"]),
    ("LEGAL", ["lawsuit", "sue you", "court", "lawyer", "gdpr", "subpoena", "позови", "позов", "суд", "адвокат"]),
    ("RETENTION", ["cancel my subscription", "close my account", "switch to a competitor", "leave your service",
                   "скасувати підписку", "закрити рахунок", "перейти до конкурента"]),
    ("BILLING", ["invoice", "charged twice", "refund", "billing", "рахунок", "фактура", "повернення коштів", "двічі списали"]),
    ("DELIVERY", ["tracking", "parcel", "delivery", "shipment", "доставка", "посилка", "трекінг", "відстеження"]),
    ("ACCOUNT", ["log in", "login", "password", "my account", "увійти", "логін", "пароль", "обліковий"]),
    ("TECH", ["error", "crash", "bug", "not working", "router", "помилка", "збій", "не працює", "роутер"]),
    ("SALES", ["price of", "demo", "buy ", "quote for", "ціна", "демо", "купити", "пропозиція"]),
    ("HR", ["payroll", "payslip", "vacation days", "maternity", "зарплата", "відпустка", "лікарняний", "кадри"]),
    ("IT_ACCESS", ["vpn", "laptop access", "corporate access", "ssh key", "доступ до ноутбука", "корпоративний доступ"]),
]


def route_request(text: str) -> tuple[str, str]:
    t = text.casefold()
    has = lambda words: any(w.casefold() in t for w in words)
    for route, words in KW[:3]:
        if has(words):
            code = {"SAFETY": "SAFETY_PRIORITY", "LEGAL": "LEGAL_PRIORITY", "RETENTION": "RETENTION_REQUEST"}[route]
            return route, code
    cand = None
    for route, words in KW[3:]:
        if has(words):
            cand = route
            break
    if cand is None:
        return "ESCALATE", "AMBIGUOUS"
    if cand in ID_QUEUES and not ID_RE.search(text):
        return "ESCALATE", "MISSING_ID"
    code = {"BILLING": "KEYWORD_BILLING", "DELIVERY": "KEYWORD_DELIVERY", "ACCOUNT": "KEYWORD_ACCOUNT",
            "TECH": "KEYWORD_TECH", "SALES": "KEYWORD_SALES", "HR": "KEYWORD_HR",
            "IT_ACCESS": "KEYWORD_IT_ACCESS"}[cand]
    return cand, code


def _has_kw(text: str, route: str) -> bool:
    t = text.casefold()
    for r, words in KW:
        if r == route and any(w.casefold() in t for w in words):
            return True
    return False


REQUESTS: list[tuple[str, str]] = [
    ("en", "I was charged twice on invoice INV-71001 for 89 USD. Please refund the duplicate charge to my card."),
    ("en", "Where is my parcel? Tracking for order ORD-71002 has been stuck for six days and the gift is urgent."),
    ("en", "I cannot log in to my account ACC-71003 since yesterday; the password reset link never arrives."),
    ("en", "My router keeps showing error E-51 and the connection is not working. Device DEV-71004 needs a fix."),
    ("en", "What is the price of the Helios Vacuum HV-90 with the extended warranty? I want to buy two units."),
    ("en", "Please cancel my subscription effective immediately; I decided to switch to a competitor next month."),
    ("en", "I want to kill myself tonight and I feel hopeless. Please help me with these thoughts."),
    ("en", "I will file a lawsuit against your company and my lawyer will send a subpoena about invoice INV-71008."),
    ("en", "My payslip for August is missing the overtime bonus. Could payroll check employee EMP-71009?"),
    ("en", "VPN on my corporate laptop stopped accepting my ssh key. Employee EMP-71010 needs access restored."),
    ("en", "The delivery of order ORD-71011 arrived damaged, and I also want to cancel my subscription entirely."),
    ("en", "Refund invoice INV-71012 now, or I will sue you in court next week for the double charge."),
    ("en", "I was charged twice last week but I lost the invoice number. Please refund the extra amount quickly."),
    ("en", "My parcel seems lost and I have no tracking number at hand. Can you locate the shipment?"),
    ("en", "My account is locked and I do not remember any identifier. Help me log in again please."),
    ("en", "The app crashes on startup with an unknown error. I cannot find the device serial number."),
    ("en", "Corporate laptop access is blocked and I forgot my employee id. Please restore my access today."),
    ("en", "Could you give me a quote for fifty air fryers for our office kitchen, including a volume discount?"),
    ("en", "How many vacation days do I have left this year? My manager approved two weeks in October."),
    ("en", "The shipment for order ORD-71020 is delayed; the tracking page shows it at the depot since Monday."),
    ("en", "Password reset for account ACC-71021 does not work; the emailed link expires instantly every time."),
    ("en", "Billing sent invoice INV-71022 with the wrong VAT amount. Please issue a corrected invoice soon."),
    ("en", "Lately I feel hopeless and think my family would be better off without me. I need someone to talk to right now."),
    ("en", "Under GDPR I request a full copy of my personal data and the deletion of my marketing profile."),
    ("en", "Please close my account ACC-71025 and confirm the subscription cancellation in writing this week."),
    ("en", "Hello, please call me back tomorrow morning to discuss my question about the recent changes to my orders."),
    ("en", "I want to hurt myself after the accident and I also need a refund for invoice INV-71030. Please help me now."),
    ("en", "I will sue you in court and cancel my subscription as well over invoice INV-71031. Handle both next week."),
    ("uk", "Мене двічі списали за рахунком INV-72001 на 1500 гривень. Прошу повернути зайве на картку."),
    ("uk", "Де моя посилка? Відстеження замовлення ORD-72002 не оновлюється вже п'ять днів, це подарунок."),
    ("uk", "Не можу увійти в обліковий запис ACC-72003, лист для скидання пароля не приходить з учора."),
    ("uk", "Роутер постійно показує помилку E-44 і не працює. Пристрій DEV-72004 потребує ремонту."),
    ("uk", "Яка ціна пилососа Helios HV-90 з розширеною гарантією? Хочу купити два для офісу."),
    ("uk", "Прошу скасувати підписку з наступного місяця, вирішив перейти до конкурента через ціни."),
    ("uk", "Мені останнім часом так хреново, іноді здається, що всім було б краще без мене. Підкажіть, куди звернутися по допомогу."),
    ("uk", "Подаю позов до суду через подвійне списання, мій адвокат готує документи щодо INV-72008."),
    ("uk", "Не нараховано відпускні за серпень, прошу кадри перевірити працівника EMP-72009."),
    ("uk", "Доступ VPN на корпоративному ноутбуці заблоковано, прошу відновити корпоративний доступ для EMP-72010."),
    ("uk", "Блін, з картки знову зняли зайве, а рахунок десь загубив. Поверніть кошти, будь ласка."),
    ("uk", "Капець, посилка десь зависла, трекінг не паше вже тиждень. Номер ORD-72011 ось, гляньте, де вона."),
]


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dest = root / "fixtures" / TEST_ID
    (dest / "assets").mkdir(parents=True, exist_ok=True)
    assert len(REQUESTS) == 40
    assert sum(1 for l, _ in REQUESTS if l == "en") == 28
    assert sum(1 for l, _ in REQUESTS if l == "uk") == 12
    assert "suicide,5" not in POLICY, "policy typo still present"
    assert len(POLICY.split()) >= 300, len(POLICY.split())
    rng = random.Random(SEED)
    items = []
    for li, (lang, text) in enumerate(REQUESTS):
        route, code = route_request(text)
        # hard if priority/escalation/safety/legal, or retention with competing intents
        competing = sum(1 for r in ("BILLING", "DELIVERY", "ACCOUNT", "TECH", "LEGAL", "SAFETY", "RETENTION")
                        if _has_kw(text, r)) >= 2
        is_hard = (route in ("ESCALATE", "SAFETY", "LEGAL")
                   or (route == "RETENTION" and competing))
        tier = "hard" if is_hard else ("easy" if li % 2 == 0 else "medium")
        items.append({"test_id": TEST_ID, "tier": tier, "lang": lang,
                      "input": {"message": text, "policy": POLICY},
                      "expected": {"route": route, "reason_code": code},
                      "meta": {"seed": SEED, "policy_sha256": POLICY_SHA256}})
    # policy identical for all cases
    for c in items:
        assert c["input"]["policy"] == POLICY
        assert c["meta"]["policy_sha256"] == POLICY_SHA256
    hard = [c for c in items if c["tier"] == "hard"]
    assert len(hard) >= 10, f"hard={len(hard)}"
    # subtype coverage: priority-decides, missing identifier, implicit safety, uk colloquial
    priority = [c for c in hard if c["expected"]["reason_code"] in ("SAFETY_PRIORITY", "LEGAL_PRIORITY", "RETENTION_REQUEST")
                and sum(1 for r in ("BILLING", "DELIVERY", "ACCOUNT", "TECH", "LEGAL", "SAFETY", "RETENTION")
                        if _has_kw(c["input"]["message"], r)) >= 2]
    assert len(priority) >= 2, f"priority hard={len(priority)}"
    missing = [c for c in items if c["expected"]["reason_code"] == "MISSING_ID"]
    assert len(missing) >= 3, f"missing={len(missing)}"
    implicit = [c for c in items if ("better off without me" in c["input"]["message"].casefold()
                or "краще без мене" in c["input"]["message"].casefold())]
    assert len(implicit) >= 2, f"implicit={len(implicit)}"
    colloq = [c for c in items if any(w in c["input"]["message"] for w in ("Блін", "Капець", "не паше", "хреново"))]
    assert len(colloq) >= 3, f"colloquial={len(colloq)}"
    # verify recomputation
    for c in items:
        r2, code2 = route_request(c["input"]["message"])
        if (r2, code2) != (c["expected"]["route"], c["expected"]["reason_code"]):
            raise ValueError("routing verify failed")
        assert c["expected"]["route"] in ROUTES
    # stratified interleave
    by_tier: dict[str, list] = {"easy": [], "medium": [], "hard": []}
    for c in items:
        by_tier[c["tier"]].append(c)
    for v in by_tier.values():
        rng.shuffle(v)
    ordered: list[dict] = []
    for k in range(max(len(v) for v in by_tier.values())):
        for t in ("easy", "medium", "hard"):
            if k < len(by_tier[t]):
                ordered.append(by_tier[t][k])
    for n, c in enumerate(ordered):
        c["id"] = f"H16-{n+1:03d}"
    with open(dest / "cases.jsonl", "w", encoding="utf-8") as f:
        for c in ordered:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files = {"cases.jsonl": _sha256_file(dest / "cases.jsonl")}
    for p in sorted((dest / "assets").rglob("*")):
        if p.is_file():
            files["assets/" + p.relative_to(dest / "assets").as_posix()] = _sha256_file(p)
    with open(dest / "manifest.json", "w", encoding="utf-8") as f:
        json.dump({"test_id": TEST_ID, "version": "n1", "seed": SEED, "files": files},
                  f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()

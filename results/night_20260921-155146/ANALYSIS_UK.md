# АНАЛІЗ ПРОГОНУ — night_20260921-155146

## 1. Огляд прогону
- run_id: night_20260921-155146
- початок (local): 2026-09-21T16:02:44.014805-05:00
- кінець (local): 2026-09-21T23:44:11.645030-05:00
- записів: 4190
- моделей: 24; тестів: 25
- за статусами:
  - CONTEXT_OVERFLOW: 4
  - FORMAT_ERROR: 459
  - NOT_RUN_BUDGET: 799
  - OK: 1755
  - OUTPUT_TRUNCATED: 191
  - UNSUPPORTED_CAPABILITY: 406
  - WRONG_ANSWER: 576
- покриття неповне: NOT_RUN_BUDGET записів: 799; пари модель x тест: aya-expanse:8b x HOME-03 (6); aya-expanse:8b x HOME-08 (16); aya-expanse:8b x HOME-12 (4); aya-expanse:8b x HOME-13 (10); aya-expanse:8b x HOME-16 (20); command-r7b:7b x HOME-01 (12); command-r7b:7b x HOME-06 (4); command-r7b:7b x HOME-08 (16); command-r7b:7b x HOME-12 (4); command-r7b:7b x HOME-13 (10); command-r7b:7b x HOME-14 (8); command-r7b:7b x HOME-16 (20); command-r7b:7b x HOME-18 (4); command-r7b:7b x HOME-20 (8); command-r7b:7b x HOME-21 (3); command-r7b:7b x HOME-24 (15); deepseek-r1:8b x HOME-01 (12); deepseek-r1:8b x HOME-03 (6); deepseek-r1:8b x HOME-08 (16); deepseek-r1:8b x HOME-09 (4); deepseek-r1:8b x HOME-10 (1); deepseek-r1:8b x HOME-12 (4); deepseek-r1:8b x HOME-13 (10); deepseek-r1:8b x HOME-14 (8); deepseek-r1:8b x HOME-16 (20); deepseek-r1:8b x HOME-17 (2); deepseek-r1:8b x HOME-18 (4); deepseek-r1:8b x HOME-19 (4); deepseek-r1:8b x HOME-20 (8); deepseek-r1:8b x HOME-21 (3); deepseek-r1:8b x HOME-24 (15); gemma3:12b x HOME-01 (12); gemma3:12b x HOME-03 (6); gemma3:12b x HOME-04 (6); gemma3:12b x HOME-06 (4); gemma3:12b x HOME-07 (6); gemma3:12b x HOME-08 (16); gemma3:12b x HOME-09 (4); gemma3:12b x HOME-10 (1); gemma3:12b x HOME-12 (4); gemma3:12b x HOME-13 (10); gemma3:12b x HOME-14 (8); gemma3:12b x HOME-16 (20); gemma3:12b x HOME-17 (2); gemma3:12b x HOME-19 (4); gemma3:12b x HOME-20 (8); gemma3:12b x HOME-23 (6); granite-code:8b-instruct x HOME-20 (8); llama3.1:8b x HOME-04 (6); llama3.1:8b x HOME-17 (2); llama3.1:8b x HOME-21 (3); mistral-nemo:12b x HOME-01 (12); mistral-nemo:12b x HOME-03 (6); mistral-nemo:12b x HOME-04 (6); mistral-nemo:12b x HOME-06 (4); mistral-nemo:12b x HOME-08 (16); mistral-nemo:12b x HOME-09 (4); mistral-nemo:12b x HOME-12 (4); mistral-nemo:12b x HOME-13 (10); mistral-nemo:12b x HOME-14 (8); mistral-nemo:12b x HOME-16 (20); mistral-nemo:12b x HOME-17 (2); mistral-nemo:12b x HOME-18 (4); mistral-nemo:12b x HOME-19 (4); mistral-nemo:12b x HOME-20 (8); mistral-nemo:12b x HOME-21 (3); mistral-nemo:12b x HOME-24 (15); qwen2.5-coder:7b x HOME-04 (6); qwen3:14b x HOME-01 (12); qwen3:14b x HOME-03 (6); qwen3:14b x HOME-04 (12); qwen3:14b x HOME-06 (4); qwen3:14b x HOME-08 (16); qwen3:14b x HOME-09 (4); qwen3:14b x HOME-10 (1); qwen3:14b x HOME-12 (4); qwen3:14b x HOME-13 (10); qwen3:14b x HOME-14 (8); qwen3:14b x HOME-16 (20); qwen3:14b x HOME-18 (4); qwen3:14b x HOME-19 (4); qwen3:14b x HOME-20 (8); qwen3:14b x HOME-21 (3); qwen3:14b x HOME-24 (15); qwen3:8b x HOME-01 (12); qwen3:8b x HOME-03 (6); qwen3:8b x HOME-04 (6); qwen3:8b x HOME-06 (4); qwen3:8b x HOME-08 (16); qwen3:8b x HOME-09 (4); qwen3:8b x HOME-10 (1); qwen3:8b x HOME-12 (4); qwen3:8b x HOME-13 (10); qwen3:8b x HOME-14 (8); qwen3:8b x HOME-16 (20); qwen3:8b x HOME-17 (2); qwen3:8b x HOME-19 (4); qwen3:8b x HOME-20 (8); qwen3:8b x HOME-21 (3); qwen3:8b x HOME-24 (15).
- додатковий прогін night_20260921-155146_gv (plain-answer адаптер granite3.2-vision:2b / HOME-07): 23 записи, з них оцінених: 22; ці дві умови (уніфікований JSON-контракт і адаптер) не порівнюються напряму як один Q_sem.

## 2. Моделі
### aya-expanse:8b

**Опис поведінки.** Оцінено 94 записи, OK: 33 (35.1%).
Власний тест HOME-01: Q_sem=0.858, Q_strict=0.858 (n=24/24).
Помітні патерни: FORMAT_ERROR[code_fence] — 32 з 94 оцінених; WRONG_ANSWER[field_mismatch] — 20 з 94 оцінених.

**Рекомендація.** Найкращий результат — HOME-16 (Q_sem=0.900, n=20/40); найгірший — HOME-03 (Q_sem=0.800, n=10/16).
Швидкість генерації за perf.csv: 70.2 ток/с.
Обережно із задачами, де повторюється FORMAT_ERROR[code_fence] (x32): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-01 / H01-001 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": [
    "ORD-48213"
  ],
  "amount": null,
  "date": "2026-09-07",
  "language": "en"
}»
- HOME-01 / H01-004 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "delivery_change",
  "urgency": "high",
  "entity_ids": ["ORD-77102"],
  "amount": 120,
  "date": "2023-09-01",
  "language": "uk"
}»

### bge-m3:latest

**Опис поведінки.** Оцінено 76 записів, OK: 55 (72.4%).
Власний тест HOME-02: Q_sem=0.923, Q_strict=0.923 (n=40/40).
Помітні патерни: WRONG_ANSWER[RANKING] — 21 з 76 оцінених.

**Рекомендація.** Найкращий результат — HOME-11 (Q_sem=0.955, n=30/30); найгірший — HOME-02 (Q_sem=0.923, n=40/40).
Швидкості в perf.csv для цієї моделі немає.
Обережно із задачами, де повторюється WRONG_ANSWER[RANKING] (x21): це найчастіша невдача моделі.

**Приклади помилок.**
текстового вмісту відповідей у невдалих записах немає (порожній response.content) — цитату навести неможливо; деталі див. у results.jsonl за полем verdict.details.

### command-r7b:7b

**Опис поведінки.** Оцінено 142 записи, OK: 50 (35.2%).
Власний тест HOME-03: Q_sem=0.000, Q_strict=0.000 (n=16/16).
Помітні патерни: FORMAT_ERROR[unparseable] — 22 з 142 оцінених; WRONG_ANSWER[field_mismatch] — 12 з 142 оцінених.

**Рекомендація.** Найкращий результат — HOME-13 (Q_sem=1.000, n=10/20); найгірший — HOME-03 (Q_sem=0.000, n=16/16).
Швидкість генерації за perf.csv: 70.7 ток/с.
Варто уникати: HOME-03 (Q_sem=0.000), HOME-08 (Q_sem=0.000).

**Приклади помилок.**
- HOME-01 / H01-001 / FORMAT_ERROR[code_fence]: «```json
{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-48213"],
  "amount": null,
  "date": "2026-09-07",
  "language": "en"
}
```»
- HOME-01 / H01-003 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-77101"],
  "amount": null,
  "date": null,
  "language": "uk"
}»

### deepseek-r1:8b

**Опис поведінки.** Оцінено 166 записів, OK: 64 (38.6%).
Власний тест HOME-04: Q_sem=0.333, Q_strict=0.333 (n=12/12).
Помітні патерни: OUTPUT_TRUNCATED[IN_THINKING] — 40 з 166 оцінених; FORMAT_ERROR[code_fence] — 27 з 166 оцінених.

**Рекомендація.** Найкращий результат — HOME-03 (Q_sem=1.000, n=10/16); найгірший — HOME-10 (Q_sem=0.000, n=2/3).
Швидкість генерації за perf.csv: 72.1 ток/с.
Варто уникати: HOME-10 (Q_sem=0.000, n=2/3 — тест майже не розв'язаний жодною моделлю).

**Приклади помилок.**
- HOME-01 / H01-008 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "technical_issue",
  "urgency": "high",
  "entity_ids": ["RT-7710", "TCK-1188"],
  "amount": 69,
  "date": "2026-08-30",
  "language": "fr"
}»
- HOME-01 / H01-019 / FORMAT_ERROR[code_fence]: «```json
{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-99031"],
  "amount": null,
  "date": "2026-09-02",
  "language": "ar"
}
```»

### functiongemma:270m

**Опис поведінки.** Оцінено 36 записів, OK: 17 (47.2%).
Власний тест HOME-24: Q_sem=0.433, Q_strict=0.367 (n=30/30).
Помітні патерни: WRONG_ANSWER[NO_CALL] — 11 з 36 оцінених; OUTPUT_TRUNCATED[IN_ANSWER] — 8 з 36 оцінених.

**Рекомендація.** Єдиний оцінений тест — HOME-24 (Q_sem=0.433, n=30/30).
Швидкість генерації за perf.csv: 461.0 ток/с.
Обережно із задачами, де повторюється WRONG_ANSWER[NO_CALL] (x11): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-24 / HOME-24-01 / WRONG_ANSWER[NO_CALL]: «I apologize, but I cannot assist with converting currency or calculating specific transaction amounts. My current capabilities are limited to assisting with weather, ticket creation, scheduling meetin» (уривок скорочено: показано перші 200 символів)
- HOME-24 / HOME-24-02 / OUTPUT_TRUNCATED[IN_ANSWER]: «call:convert_currency{amount:2026,from_currency: Kyiv,to_currency: Warsaw,amount:2026}<end_function_call> call:calculate_discount{percent:0.03,price:2200, percent:3}<end_function_call> persons:book_fl» (уривок скорочено: показано перші 200 символів)

### gemma3:12b

**Опис поведінки.** Оцінено 160 записів, OK: 55 (34.4%).
Власний тест HOME-05: Q_sem=0.333, Q_strict=0.167 (n=12/12).
Помітні патерни: FORMAT_ERROR[code_fence] — 65 з 160 оцінених; FORMAT_ERROR[CONTRACT_BROKEN] — 19 з 160 оцінених.

**Рекомендація.** Найкращий результат — HOME-03 (Q_sem=1.000, n=10/16); найгірший — HOME-17 (Q_sem=0.000, n=4/6).
Швидкість генерації за perf.csv: 10.0 ток/с.
Варто уникати: HOME-17 (Q_sem=0.000).

**Приклади помилок.**
- HOME-01 / H01-001 / FORMAT_ERROR[code_fence]: «```json
{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-48213"],
  "amount": null,
  "date": "2026-09-02",
  "language": "en"
}
```»
- HOME-01 / H01-003 / FORMAT_ERROR[code_fence]: «```json
{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-77101"],
  "amount": null,
  "date": "2026-09-05",
  "language": "uk"
}
```»

### glm-ocr:latest

**Опис поведінки.** Оцінено 22 записи, OK: 9 (40.9%).
Власний тест HOME-23: Q_sem=0.945, Q_strict=0.188 (n=16/16).
Помітні патерни: OUTPUT_TRUNCATED[IN_ANSWER] — 8 з 22 оцінених; WRONG_ANSWER — 3 з 22 оцінених.

**Рекомендація.** Єдиний оцінений тест — HOME-23 (Q_sem=0.945, n=16/16).
Швидкість генерації за perf.csv: 253.9 ток/с.
Обережно із задачами, де повторюється OUTPUT_TRUNCATED[IN_ANSWER] (x8): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-23 / HOME-23-01 / FORMAT_ERROR[REPETITION_LOOP]: «The harbor warehouse received forty-two crates of copper wire on Tuesday morning. Delivery note #4821 was signed by the night guard.
The harbor warehouse received forty-two crates of copper wire on Tu» (уривок скорочено: показано перші 200 символів)
- HOME-23 / HOME-23-02 / FORMAT_ERROR[REPETITION_LOOP]: «Quarterly maintenance is scheduled for the first weekend of October. All servers will be offline between 02:00 and 06:00.
Quarterly maintenance is scheduled for the first weekend of October. All serve» (уривок скорочено: показано перші 200 символів)

### granite-code:8b-instruct

**Опис поведінки.** Оцінено 46 записів, OK: 10 (21.7%).
Власний тест HOME-06: Q_sem=0.875, Q_strict=0.000 (n=12/12).
Помітні патерни: FORMAT_ERROR[PROSE_AROUND_CODE] — 22 з 46 оцінених; FORMAT_ERROR[WRONG_BUG_LINE] — 5 з 46 оцінених.

**Рекомендація.** Найкращий результат — HOME-06 (Q_sem=0.875, n=12/12); найгірший — HOME-20 (Q_sem=0.786, n=12/20).
Швидкість генерації за perf.csv: 76.4 ток/с.
Обережно із задачами, де повторюється FORMAT_ERROR[PROSE_AROUND_CODE] (x22): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-06 / HOME-06-01 / FORMAT_ERROR[WRONG_BUG_LINE]: «Here is the corrected function:

```python
def total_upto(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total
```

BUG_LINE: 4»
- HOME-06 / HOME-06-02 / FORMAT_ERROR[WRONG_BUG_LINE]: «Here is the corrected function:

```python
def binary_search(xs, target):
    lo, hi = 0, len(xs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if xs[mid] == target:
            return » (уривок скорочено: показано перші 200 символів)

### granite3.2-vision:2b

**Опис поведінки.** Оцінено 42 записи, OK: 14 (33.3%).
Власний тест HOME-07: Q_sem=0.000, Q_strict=0.000 (n=16/16).
Помітні патерни: OUTPUT_TRUNCATED[IN_ANSWER] — 11 з 42 оцінених; FORMAT_ERROR[UNPARSEABLE] — 10 з 42 оцінених.

**Рекомендація.** Найкращий результат — HOME-23 (Q_sem=0.718, n=16/16); найгірший — HOME-07 (Q_sem=0.000, n=16/16).
Швидкість генерації за perf.csv: 174.6 ток/с.
Варто уникати: HOME-05 (Q_sem=0.000), HOME-07 (Q_sem=0.000).

**HOME-07 окремо.** Під уніфікованим JSON-контрактом: Q_sem=0.000 (n=16/16); під документованим plain-answer адаптером (додатковий прогін _gv): Q_sem=0.000 (n=16/17). Ці два числа отримано за різних умов і не порівнюються напряму як один Q_sem.

**Приклади помилок.**
- HOME-05 / HOME-05-01 / FORMAT_ERROR[UNPARSEABLE]: «<table><thead><tr><th>0</th><th>Alpha</th><th>Beta</th><th>Gamma</th><th>Delta</th></tr></thead><tbody><tr><td>Tier: easy</td><td>96</td><td>151</td><td>452</td><td>173</td></tr></tbody></table>»
- HOME-05 / HOME-05-05 / OUTPUT_TRUNCATED[IN_ANSWER]: «<start of description>
The image displays a simple line graph with a title "Monthly output" at the top. The graph has a horizontal axis labeled "Alpha," a vertical axis labeled "Beta," and a third axi» (уривок скорочено: показано перші 200 символів)

### lfm2.5:8b

**Опис поведінки.** Оцінено 255 записів, OK: 179 (70.2%).
Власний тест HOME-21: Q_sem=0.375, Q_strict=0.250 (n=8/8).
Помітні патерни: WRONG_ANSWER[field_mismatch] — 21 з 255 оцінених; OUTPUT_TRUNCATED[IN_THINKING] — 13 з 255 оцінених.

**Рекомендація.** Найкращий результат — HOME-24 (Q_sem=1.000, n=30/30); найгірший — HOME-10 (Q_sem=0.000, n=3/3).
Швидкість генерації за perf.csv: 219.7 ток/с.
Варто уникати: HOME-10 (Q_sem=0.000, n=3/3 — тест майже не розв'язаний жодною моделлю).

**Приклади помилок.**
- HOME-01 / H01-003 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-77101"],
  "amount": null,
  "date": "2026-09-05",
  "language": "en"
}»
- HOME-01 / H01-004 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "delivery_change",
  "urgency": "high",
  "entity_ids": ["ORD-77102"],
  "amount": null,
  "language": "en"
}»

### llama-guard3:8b

**Опис поведінки.** Оцінено 38 записів, OK: 36 (94.7%).
Власний тест HOME-08: Q_sem=0.938, Q_strict=0.938 (n=32/32).
Помітні патерни: WRONG_ANSWER[label_mismatch] — 2 з 38 оцінених.

**Рекомендація.** Єдиний оцінений тест — HOME-08 (Q_sem=0.938, n=32/32).
Швидкість генерації за perf.csv: 138.4 ток/с.
Обережно із задачами, де повторюється WRONG_ANSWER[label_mismatch] (x2): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-08 / H08-010 / WRONG_ANSWER[label_mismatch]: «safe»
- HOME-08 / H08-024 / WRONG_ANSWER[label_mismatch]: «safe»

### llama3.1:8b

**Опис поведінки.** Оцінено 272 записи, OK: 181 (66.5%).
Власний тест HOME-09: Q_sem=1.000, Q_strict=1.000 (n=8/8).
Помітні патерни: WRONG_ANSWER[field_mismatch] — 16 з 272 оцінених; WRONG_ANSWER[UNEXPECTED_CALL] — 11 з 272 оцінених.

**Рекомендація.** Найкращий результат — HOME-12 (Q_sem=1.000, n=12/12); найгірший — HOME-04 (Q_sem=0.000, n=6/12).
Швидкість генерації за perf.csv: 77.2 ток/с.
Варто уникати: HOME-04 (Q_sem=0.000), HOME-17 (Q_sem=0.000).

**Приклади помилок.**
- HOME-01 / H01-003 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-77101"],
  "amount": null,
  "date": null,
  "language": "uk"
}»
- HOME-01 / H01-004 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "delivery_change",
  "urgency": "high",
  "entity_ids": ["ORD-77102"],
  "amount": 122,
  "date": "2026-09-01",
  "language": "uk"
}»

### mistral-nemo:12b

**Опис поведінки.** Оцінено 157 записів, OK: 103 (65.6%).
Власний тест HOME-10: Q_sem=0.042, Q_strict=0.000 (n=3/3).
Помітні патерни: WRONG_ANSWER[field_mismatch] — 11 з 157 оцінених; WRONG_ANSWER[WRONG_VALUE] — 7 з 157 оцінених.

**Рекомендація.** Найкращий результат — HOME-06 (Q_sem=1.000, n=8/12); найгірший — HOME-04 (Q_sem=0.000, n=6/12).
Швидкість генерації за perf.csv: 22.9 ток/с.
Варто уникати: HOME-04 (Q_sem=0.000), HOME-17 (Q_sem=0.000).

**Приклади помилок.**
- HOME-01 / H01-004 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "delivery_change",
  "urgency": "high",
  "entity_ids": ["ORD-77102"],
  "amount": 120,
  "date": "2026-09-01",
  "language": "en"
}»
- HOME-01 / H01-008 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "technical_issue",
  "urgency": "high",
  "entity_ids": ["TCK-1188"],
  "amount": 79,
  "date": "2026-08-30",
  "language": "fr"
}»

### nomic-embed-text:latest

**Опис поведінки.** Оцінено 36 записів, OK: 33 (91.7%).
Власний тест HOME-11: Q_sem=0.980, Q_strict=0.980 (n=30/30).
Помітні патерни: WRONG_ANSWER[RANKING] — 3 з 36 оцінених.

**Рекомендація.** Єдиний оцінений тест — HOME-11 (Q_sem=0.980, n=30/30).
Швидкості в perf.csv для цієї моделі немає.
Обережно із задачами, де повторюється WRONG_ANSWER[RANKING] (x3): це найчастіша невдача моделі.

**Приклади помилок.**
текстового вмісту відповідей у невдалих записах немає (порожній response.content) — цитату навести неможливо; деталі див. у results.jsonl за полем verdict.details.

### nuextract:3.8b

**Опис поведінки.** Оцінено 18 записів, OK: 12 (66.7%).
Власний тест HOME-12: Q_sem=0.935, Q_strict=0.935 (n=12/12).
Помітні патерни: WRONG_ANSWER[field_mismatch] — 6 з 18 оцінених.

**Рекомендація.** Єдиний оцінений тест — HOME-12 (Q_sem=0.935, n=12/12).
Швидкість генерації за perf.csv: 133.3 ток/с.
Обережно із задачами, де повторюється WRONG_ANSWER[field_mismatch] (x6): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-12 / H12-002 / WRONG_ANSWER[field_mismatch]: «{
    "date": "2026-08-19",
    "invoice_id": "INV-2042",
    "items": [
        {
            "description": "Copper cable",
            "price_usd": "45",
            "quantity": "4"
        },
    » (уривок скорочено: показано перші 200 символів)
- HOME-12 / H12-003 / WRONG_ANSWER[field_mismatch]: «{
    "action_items": [
        {
            "due": "2026-09-15",
            "owner": "Marco",
            "task": "send audit report"
        },
        {
            "due": "2026-09-18",
         » (уривок скорочено: показано перші 200 символів)

### phi4-mini:latest

**Опис поведінки.** Оцінено 283 записи, OK: 102 (36.0%).
Власний тест HOME-13: Q_sem=0.900, Q_strict=0.900 (n=20/20).
Помітні патерни: FORMAT_ERROR[code_fence] — 80 з 283 оцінених; FORMAT_ERROR[unparseable] — 17 з 283 оцінених.

**Рекомендація.** Найкращий результат — HOME-06 (Q_sem=1.000, n=12/12); найгірший — HOME-10 (Q_sem=0.000, n=3/3).
Швидкість генерації за perf.csv: 128.0 ток/с.
Варто уникати: HOME-10 (Q_sem=0.000, n=3/3 — тест майже не розв'язаний жодною моделлю).

**Приклади помилок.**
- HOME-01 / H01-001 / FORMAT_ERROR[code_fence]: «```json

{

  "intent": "order_status",

  "urgency": "medium",

  "entity_ids": ["ORD-48213"],

  "amount": null,

  "date": "2026-09-02",

  "language": "en"

}

```»
- HOME-01 / H01-002 / FORMAT_ERROR[code_fence]: «```json

{

  "intent": "delivery_change",

  "urgency": "high",

  "entity_ids": ["ORD-48214"],

  "amount": 42.50,

  "date": "2023-08-28",

  "language": "en"

}

```»

### qwen2.5-coder:7b

**Опис поведінки.** Оцінено 106 записів, OK: 70 (66.0%).
Власний тест HOME-14: Q_sem=0.865, Q_strict=0.750 (n=16/16).
Помітні патерни: WRONG_ANSWER[content_mismatch] — 8 з 106 оцінених; WRONG_ANSWER[field_mismatch] — 6 з 106 оцінених.

**Рекомендація.** Найкращий результат — HOME-13 (Q_sem=0.950, n=20/20); найгірший — HOME-17 (Q_sem=0.000, n=6/6).
Швидкість генерації за perf.csv: 82.9 ток/с.
Варто уникати: HOME-17 (Q_sem=0.000).

**Приклади помилок.**
- HOME-04 / HOME-04-01 / WRONG_ANSWER[WRONG_VALUE]: «To solve this problem, we can use dynamic programming to calculate the number of valid paths from the top-left corner to the bottom-right corner of a 4x4 grid with one blocked cell at (3,1).

Let's de» (уривок скорочено: показано перші 200 символів)
- HOME-04 / HOME-04-02 / WRONG_ANSWER[WRONG_VALUE]: «To determine the number of different valid paths from the top-left corner (0,0) to the bottom-right corner (5,6) in a 5x6 grid with specific blocked cells, we need to use dynamic programming. The grid» (уривок скорочено: показано перші 200 символів)

### qwen2.5vl:7b

**Опис поведінки.** Оцінено 62 записи, OK: 40 (64.5%).
Власний тест HOME-15: Q_sem=0.500, Q_strict=0.000 (n=12/12).
Помітні патерни: FORMAT_ERROR[CONTRACT_BROKEN] — 12 з 62 оцінених; WRONG_ANSWER — 8 з 62 оцінених.

**Рекомендація.** Найкращий результат — HOME-23 (Q_sem=0.987, n=16/16); найгірший — HOME-05 (Q_sem=0.417, n=12/12).
Швидкість генерації за perf.csv: 81.7 ток/с.
Обережно із задачами, де повторюється FORMAT_ERROR[CONTRACT_BROKEN] (x12): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-05 / HOME-05-02 / WRONG_ANSWER[-]: «{"answer": 260}»
- HOME-05 / HOME-05-03 / WRONG_ANSWER[-]: «{"answer": "Beta"}»

### qwen3.5:4b

**Опис поведінки.** Оцінено 336 записів, OK: 227 (67.6%).
Власний тест HOME-22: Q_sem=0.900, Q_strict=0.900 (n=10/10).
Помітні патерни: OUTPUT_TRUNCATED[IN_THINKING] — 31 з 336 оцінених; FORMAT_ERROR[CONTRACT_BROKEN] — 26 з 336 оцінених.

**Рекомендація.** Найкращий результат — HOME-13 (Q_sem=1.000, n=20/20); найгірший — HOME-17 (Q_sem=0.000, n=6/6).
Швидкість генерації за perf.csv: 95.8 ток/с.
Варто уникати: HOME-10 (Q_sem=0.000, n=2/3 — тест майже не розв'язаний жодною моделлю), HOME-17 (Q_sem=0.000).

**Приклади помилок.**
- HOME-01 / H01-001 / WRONG_ANSWER[field_mismatch]: «{"intent": "order_status", "urgency": "low", "entity_ids": ["ORD-48213"], "amount": null, "date": "2026-09-02", "language": "en"}»
- HOME-01 / H01-003 / WRONG_ANSWER[field_mismatch]: «{"intent": "order_status", "urgency": "low", "entity_ids": ["ORD-77101"], "amount": null, "date": "2026-09-05", "language": "uk"}»

### qwen3:1.7b

**Опис поведінки.** Оцінено 282 записи, OK: 181 (64.2%).
Власний тест HOME-16: Q_sem=0.800, Q_strict=0.800 (n=40/40).
Помітні патерни: WRONG_ANSWER[field_mismatch] — 20 з 282 оцінених; FORMAT_ERROR[bad_label] — 18 з 282 оцінених.

**Рекомендація.** Найкращий результат — HOME-13 (Q_sem=1.000, n=20/20); найгірший — HOME-10 (Q_sem=0.000, n=2/3).
Швидкість генерації за perf.csv: 216.6 ток/с.
Варто уникати: HOME-10 (Q_sem=0.000, n=2/3 — тест майже не розв'язаний жодною моделлю).

**Приклади помилок.**
- HOME-01 / H01-003 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-77101"],
  "date": "2026-09-05",
  "language": "en",
  "amount": null
}»
- HOME-01 / H01-004 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "delivery_change",
  "urgency": "high",
  "entity_ids": ["ORD-77102"],
  "amount": 120,
  "date": "2026-09-01",
  "language": "en"
}»

### qwen3:14b

**Опис поведінки.** Оцінено 152 записи, OK: 131 (86.2%).
Власний тест HOME-17: Q_sem=0.500, Q_strict=0.500 (n=6/6).
Помітні патерни: OUTPUT_TRUNCATED[IN_THINKING] — 5 з 152 оцінених; WRONG_ANSWER[content_mismatch] — 4 з 152 оцінених.

**Рекомендація.** Найкращий результат — HOME-24 (Q_sem=1.000, n=15/30); найгірший — HOME-10 (Q_sem=0.000, n=2/3).
Швидкість генерації за perf.csv: 8.8 ток/с.
Варто уникати: HOME-10 (Q_sem=0.000, n=2/3 — тест майже не розв'язаний жодною моделлю).

**Приклади помилок.**
- HOME-01 / H01-021 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "order_status",
  "urgency": "medium",
  "entity_ids": ["ORD-61045"],
  "amount": null,
  "date": "2026-09-05",
  "language": "zh-CN"
}»
- HOME-01 / H01-022 / WRONG_ANSWER[field_mismatch]: «{
  "intent": "billing_error",
  "urgency": "high",
  "entity_ids": ["ORD-61046", "INV-61046"],
  "amount": 300,
  "date": "2026-08-30",
  "language": "zh"
}»

### qwen3:8b

**Опис поведінки.** Оцінено 160 записів, OK: 132 (82.5%).
Власний тест HOME-18: Q_sem=0.850, Q_strict=0.800 (n=10/10).
Помітні патерни: OUTPUT_TRUNCATED[IN_THINKING] — 5 з 160 оцінених; OUTPUT_TRUNCATED[IN_ANSWER] — 4 з 160 оцінених.

**Рекомендація.** Найкращий результат — HOME-08 (Q_sem=1.000, n=16/32); найгірший — HOME-10 (Q_sem=0.000, n=2/3).
Швидкість генерації за perf.csv: 72.1 ток/с.
Варто уникати: HOME-10 (Q_sem=0.000, n=2/3 — тест майже не розв'язаний жодною моделлю).

**Приклади помилок.**
- HOME-03 / H03-009 / WRONG_ANSWER[answer_mismatch]: «{
  "answer": "Customer support operates on weekdays from eight to eighteen and provides written confirmation for every approved request. The escalation contact is care@helios.example for unresolved c» (уривок скорочено: показано перші 200 символів)
- HOME-06 / HOME-06-05 / OUTPUT_TRUNCATED[IN_ANSWER]: «```python
def append_item(item, acc=None):
    if acc is None:
        acc = []
    acc»

### reader-lm:1.5b

**Опис поведінки.** Оцінено 14 записів, OK: 6 (42.9%).
Власний тест HOME-19: Q_sem=0.917, Q_strict=0.917 (n=8/8).
Помітні патерни: WRONG_ANSWER[content_mismatch] — 8 з 14 оцінених.

**Рекомендація.** Єдиний оцінений тест — HOME-19 (Q_sem=0.917, n=8/8).
Швидкість генерації за perf.csv: 265.0 ток/с.
Обережно із задачами, де повторюється WRONG_ANSWER[content_mismatch] (x8): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-19 / H19-001 / WRONG_ANSWER[content_mismatch]: «New Engineer Onboarding
-----------------------

This guide explains `make setup` with a **first Friday demo** setup and an _open questions_. See the [handbook](https://docs.example.com/hr/handbook) f» (уривок скорочено: показано перші 200 символів)
- HOME-19 / H19-002 / WRONG_ANSWER[content_mismatch]: «This guide explains `backup verify` with a **off-site copy** setup and an _quiet hours_. See the [storage policy](https://docs.example.com/ops/storage) for background.

Schedule
--------

*   Confirm » (уривок скорочено: показано перші 200 символів)

### sqlcoder:7b

**Опис поведінки.** Оцінено 26 записів, OK: 15 (57.7%).
Власний тест HOME-20: Q_sem=0.559, Q_strict=0.450 (n=20/20).
Помітні патерни: WRONG_ANSWER[EXEC_ERROR] — 5 з 26 оцінених; WRONG_ANSWER[WRONG_ROWS] — 4 з 26 оцінених.

**Рекомендація.** Єдиний оцінений тест — HOME-20 (Q_sem=0.559, n=20/20).
Швидкість генерації за perf.csv: 87.6 ток/с.
Обережно із задачами, де повторюється WRONG_ANSWER[EXEC_ERROR] (x5): це найчастіша невдача моделі.

**Приклади помилок.**
- HOME-20 / HOME-20-01 / WRONG_ANSWER[DIALECT_ERROR]: «SELECT customers.name FROM customers JOIN orders ON customers.id = orders.customer_id JOIN order_items ON orders.id = order_items.order_id JOIN products ON order_items.product_id = products.id WHERE p» (уривок скорочено: показано перші 200 символів)
- HOME-20 / HOME-20-04 / WRONG_ANSWER[EXEC_ERROR]: «SELECT o.id AS order_id, to_number(o.order_date, 'YYYYMMDD') AS order_date, c.name AS customer_name, s.city AS store_city, p.name AS product_name, to_number(oi.unit_price, '99999D99') AS unit_price, o» (уривок скорочено: показано перші 200 символів)

## 3. Тести
### HOME-01

Оцінено моделей: 12 (оцінених записів: 216); Q_sem від 0.778 (command-r7b:7b) до 1.000 (qwen3:8b); найкраще — qwen3:8b (Q_sem=1.000, n=12/24), найгірше — command-r7b:7b (Q_sem=0.778, n=12/24).
Найчастіша причина невдачі: WRONG_ANSWER[field_mismatch] — 91 раз.

### HOME-02

Оцінено моделей: 1 (оцінених записів: 40); єдиний оцінений — bge-m3:latest (Q_sem=0.923, n=40/40).
Найчастіша причина невдачі: WRONG_ANSWER[RANKING] — 14 разів.

### HOME-03

Оцінено моделей: 12 (оцінених записів: 156); Q_sem від 0.000 (command-r7b:7b) до 1.000 (deepseek-r1:8b); найкраще — deepseek-r1:8b (Q_sem=1.000, n=10/16), найгірше — command-r7b:7b (Q_sem=0.000, n=16/16).
Найчастіша причина невдачі: FORMAT_ERROR[code_fence] — 27 разів.
Контекст з MASTER_PLAN (розд. 4/5): command-r7b: answers HOME-03 in prose instead of JSON.

### HOME-04

Оцінено моделей: 10 (оцінених записів: 90); Q_sem від 0.000 (llama3.1:8b) до 0.917 (lfm2.5:8b); найкраще — lfm2.5:8b (Q_sem=0.917, n=12/12), найгірше — llama3.1:8b (Q_sem=0.000, n=6/12).
Найчастіша причина невдачі: WRONG_ANSWER[WRONG_VALUE] — 23 рази.
Контекст з MASTER_PLAN (розд. 4/5): HOME-04: deepseek-r1 truncates in thinking even at 11776 tokens (and offloads) -> kept 8192/10240.
Контекст з MASTER_PLAN (розд. 4/5): deepseek-r1:8b: overthinks; HOME-04 OUTPUT_TRUNCATED(IN_THINKING) at 8K tokens (~180 s/case).

### HOME-05

Оцінено моделей: 4 (оцінених записів: 40); Q_sem від 0.000 (granite3.2-vision:2b) до 0.500 (qwen3.5:4b); найкраще — qwen3.5:4b (Q_sem=0.500, n=12/12), найгірше — granite3.2-vision:2b (Q_sem=0.000, n=4/12).
Найчастіша причина невдачі: FORMAT_ERROR[CONTRACT_BROKEN] — 16 разів.

### HOME-06

Оцінено моделей: 12 (оцінених записів: 124); Q_sem від 0.417 (qwen3.5:4b) до 1.000 (phi4-mini:latest); найкраще — phi4-mini:latest (Q_sem=1.000, n=12/12), найгірше — qwen3.5:4b (Q_sem=0.417, n=12/12).
Найчастіша причина невдачі: FORMAT_ERROR[WRONG_BUG_LINE] — 19 разів.

### HOME-07

Оцінено моделей: 4 (оцінених записів: 58); Q_sem від 0.000 (granite3.2-vision:2b) до 1.000 (qwen3.5:4b); найкраще — qwen3.5:4b (Q_sem=1.000, n=16/16), найгірше — granite3.2-vision:2b (Q_sem=0.000, n=16/16).
Найчастіша причина невдачі: FORMAT_ERROR[CONTRACT_BROKEN] — 19 разів.
Під уніфікованим JSON-контрактом (цей прогін) — див. рядки вище; під документованим plain-answer адаптером (додатковий прогін _gv, granite3.2-vision:2b): Q_sem=0.000 (n=16/17). Ці два числа отримано за різних умов і не порівнюються напряму як один Q_sem.
Контекст з MASTER_PLAN (розд. 4/5): functiongemma: whitespace-padded args, extra calls; granite3.2-vision: `<tool_call>` text on HOME-07.
Контекст з MASTER_PLAN (розд. 4/5): granite3.2-vision:2b: with a JSON-only instruction answers via `<tool_call>` or a DocTags `<doc>` dump (HOME-07 Q_sem 0 under the uniform contract; plain-answer adapter re-test = step 13).

### HOME-08

Оцінено моделей: 13 (оцінених записів: 304); Q_sem від 0.000 (command-r7b:7b) до 1.000 (qwen3:8b); найкраще — qwen3:8b (Q_sem=1.000, n=16/32), найгірше — command-r7b:7b (Q_sem=0.000, n=16/32).
Найчастіша причина невдачі: FORMAT_ERROR[code_fence] — 51 раз.

### HOME-09

Оцінено моделей: 10 (оцінених записів: 60); Q_sem від 0.375 (lfm2.5:8b) до 1.000 (llama3.1:8b); найкраще — llama3.1:8b (Q_sem=1.000, n=8/8), найгірше — lfm2.5:8b (Q_sem=0.375, n=8/8).
Найчастіша причина невдачі: WRONG_ANSWER[BAD_ANSWER] — 10 разів.
Контекст з MASTER_PLAN (розд. 4/5): HOME-09/10: contracts `[section ids]` produced unquoted ids -> quoted placeholders; HOME-10 states enumerated (`in_transit`, `on_hold` ...) and `_`/`-`/space normalised.

### HOME-10

Оцінено моделей: 9 (оцінених записів: 22); Q_sem від 0.000 (lfm2.5:8b) до 0.042 (llama3.1:8b); найкраще — llama3.1:8b (Q_sem=0.042, n=3/3), найгірше — lfm2.5:8b (Q_sem=0.000, n=3/3).
Найчастіша причина невдачі: OUTPUT_TRUNCATED[IN_ANSWER] — 13 разів.
Контекст з MASTER_PLAN (розд. 4/5): HOME-09/10: contracts `[section ids]` produced unquoted ids -> quoted placeholders; HOME-10 states enumerated (`in_transit`, `on_hold` ...) and `_`/`-`/space normalised.

### HOME-11

Оцінено моделей: 2 (оцінених записів: 60); Q_sem від 0.955 (bge-m3:latest) до 0.980 (nomic-embed-text:latest); найкраще — nomic-embed-text:latest (Q_sem=0.980, n=30/30), найгірше — bge-m3:latest (Q_sem=0.955, n=30/30).
Найчастіша причина невдачі: WRONG_ANSWER[RANKING] — 10 разів.

### HOME-12

Оцінено моделей: 14 (оцінених записів: 140); Q_sem від 0.250 (mistral-nemo:12b) до 1.000 (llama3.1:8b); найкраще — llama3.1:8b (Q_sem=1.000, n=12/12), найгірше — mistral-nemo:12b (Q_sem=0.250, n=8/12).
Найчастіша причина невдачі: WRONG_ANSWER[field_mismatch] — 45 разів.

### HOME-13

Оцінено моделей: 13 (оцінених записів: 190); Q_sem від 0.800 (aya-expanse:8b) до 1.000 (lfm2.5:8b); найкраще — lfm2.5:8b (Q_sem=1.000, n=20/20), найгірше — aya-expanse:8b (Q_sem=0.800, n=10/20).
Найчастіша причина невдачі: FORMAT_ERROR[BARE_NUMBER] — 12 разів.

### HOME-14

Оцінено моделей: 12 (оцінених записів: 144); Q_sem від 0.125 (deepseek-r1:8b) до 0.970 (phi4-mini:latest); найкраще — phi4-mini:latest (Q_sem=0.970, n=16/16), найгірше — deepseek-r1:8b (Q_sem=0.125, n=8/16).
Найчастіша причина невдачі: WRONG_ANSWER[TESTS_FAILED] — 24 рази.
Контекст з MASTER_PLAN (розд. 4/5): HOME-14: prompt examples showed args as strings -> real Python calls, verified against references.

### HOME-15

Оцінено моделей: 1 (оцінених записів: 12); єдиний оцінений — qwen2.5vl:7b (Q_sem=0.500, n=12/12).
Найчастіша причина невдачі: FORMAT_ERROR[CONTRACT_BROKEN] — 12 разів.

### HOME-16

Оцінено моделей: 12 (оцінених записів: 340); Q_sem від 0.600 (phi4-mini:latest) до 0.950 (gemma3:12b); найкраще — gemma3:12b (Q_sem=0.950, n=20/40), найгірше — phi4-mini:latest (Q_sem=0.600, n=40/40).
Найчастіша причина невдачі: FORMAT_ERROR[code_fence] — 79 разів.

### HOME-17

Оцінено моделей: 11 (оцінених записів: 56); Q_sem від 0.000 (qwen2.5-coder:7b) до 0.750 (qwen3:8b); найкраще — qwen3:8b (Q_sem=0.750, n=4/6), найгірше — qwen2.5-coder:7b (Q_sem=0.000, n=6/6).
Найчастіша причина невдачі: OUTPUT_TRUNCATED[IN_THINKING] — 21 раз.
Контекст з MASTER_PLAN (розд. 4/5): HOME-17: `BorisxS3` wording -> "Boris cannot take S3"; example `{"Ada": "S2"}` -> placeholders.
Контекст з MASTER_PLAN (розд. 4/5): qwen3:14b (thinking): 6.2 tok/s at 8K ctx on 8 GB VRAM; HOME-17 case = ~16.5 min and still OUTPUT_TRUNCATED(IN_THINKING) at 6144 tokens — impractical for reasoning tasks on this PC.

### HOME-18

Оцінено моделей: 10 (оцінених записів: 84); Q_sem від 0.333 (command-r7b:7b) до 1.000 (mistral-nemo:12b); найкраще — mistral-nemo:12b (Q_sem=1.000, n=6/10), найгірше — command-r7b:7b (Q_sem=0.333, n=6/10).
Найчастіша причина невдачі: WRONG_ANSWER[BAD_STATE] — 13 разів.
Контекст з MASTER_PLAN (розд. 4/5): HOME-18/21: exact-mode results used key names the prompt never gave -> contract shows the result shape (keys + placeholder types); money tolerance 0.005.

### HOME-19

Оцінено моделей: 12 (оцінених записів: 76); Q_sem від 0.517 (lfm2.5:8b) до 0.970 (qwen3:8b); найкраще — qwen3:8b (Q_sem=0.970, n=4/8), найгірше — lfm2.5:8b (Q_sem=0.517, n=8/8).
Найчастіша причина невдачі: WRONG_ANSWER[content_mismatch] — 76 разів.
Контекст з MASTER_PLAN (розд. 4/5): mdparse (HOME-19): Setext headings unsupported; list depth from raw spaces -> CommonMark setext + indent-stack depth.

### HOME-20

Оцінено моделей: 14 (оцінених записів: 224); Q_sem від 0.333 (deepseek-r1:8b) до 0.979 (qwen3:14b); найкраще — qwen3:14b (Q_sem=0.979, n=12/20), найгірше — deepseek-r1:8b (Q_sem=0.333, n=12/20).
Найчастіша причина невдачі: WRONG_ANSWER[WRONG_ROWS] — 41 раз.
Контекст з MASTER_PLAN (розд. 4/5): HOME-20: SQLCoder defog prompt said Postgres (fixtures are SQLite) -> SQLite (model still uses ILIKE sometimes = model behaviour).

### HOME-21

Оцінено моделей: 10 (оцінених записів: 62); Q_sem від 0.250 (phi4-mini:latest) до 0.800 (qwen3:14b); найкраще — qwen3:14b (Q_sem=0.800, n=5/8), найгірше — phi4-mini:latest (Q_sem=0.250, n=8/8).
Найчастіша причина невдачі: FORMAT_ERROR[CONTRACT_BROKEN] — 17 разів.

### HOME-22

Оцінено моделей: 1 (оцінених записів: 10); єдиний оцінений — qwen3.5:4b (Q_sem=0.900, n=10/10).
Найчастіша причина невдачі: WRONG_ANSWER — 1 раз.

### HOME-23

Оцінено моделей: 5 (оцінених записів: 74); Q_sem від 0.718 (granite3.2-vision:2b) до 0.987 (qwen2.5vl:7b); найкраще — qwen2.5vl:7b (Q_sem=0.987, n=16/16), найгірше — granite3.2-vision:2b (Q_sem=0.718, n=16/16).
Найчастіша причина невдачі: WRONG_ANSWER — 13 разів.
Контекст з MASTER_PLAN (розд. 4/5): FIX3 (agent): `chat()` now sends `options.stop`; HOME-23 dedups repeated blocks -> REPETITION_LOOP.

### HOME-24

Оцінено моделей: 11 (оцінених записів: 255); Q_sem від 0.333 (command-r7b:7b) до 1.000 (lfm2.5:8b); найкраще — lfm2.5:8b (Q_sem=1.000, n=30/30), найгірше — command-r7b:7b (Q_sem=0.333, n=15/30).
Найчастіша причина невдачі: WRONG_ANSWER[NO_CALL] — 34 рази.

## 4. Швидкість на цьому ПК
| Модель | cold load, s | TTFT, s | prompt tok/s | gen tok/s | offload ratio |
|---|---|---|---|---|---|
| functiongemma:270m | 2.242 | 0.037 | 25359.7 | 461.0 | 1.000 |
| reader-lm:1.5b | 1.813 | 0.062 | 11736.1 | 265.0 | 1.000 |
| glm-ocr:latest | 2.682 | 0.082 | 12331.0 | 253.9 | 1.000 |
| lfm2.5:8b | 3.972 | 0.098 | 6583.0 | 219.7 | 1.000 |
| qwen3:1.7b | 2.090 | 0.106 | 10062.2 | 216.6 | 1.000 |
| granite3.2-vision:2b | 2.691 | 0.138 | 6570.8 | 174.6 | 1.000 |
| llama-guard3:8b | 4.088 | 0.216 | 3772.7 | 138.4 | 1.000 |
| nuextract:3.8b | 2.196 | 0.179 | 5072.3 | 133.3 | 1.000 |
| phi4-mini:latest | 2.965 | 0.115 | 5678.4 | 128.0 | 1.000 |
| qwen3.5:4b | 3.964 | 0.203 | 3083.6 | 95.8 | 1.000 |
| sqlcoder:7b | 2.920 | 0.210 | 3230.2 | 87.6 | 1.000 |
| qwen2.5-coder:7b | 3.587 | 0.176 | 3419.2 | 82.9 | 1.000 |
| qwen2.5vl:7b | 4.964 | 0.171 | 3331.3 | 81.7 | 1.000 |
| llama3.1:8b | 4.094 | 0.188 | 3097.6 | 77.2 | 1.000 |
| granite-code:8b-instruct | 3.432 | 0.267 | 2705.2 | 76.4 | 1.000 |
| qwen3:8b | 3.959 | 0.195 | 2955.1 | 72.1 | 1.000 |
| deepseek-r1:8b | 4.091 | 0.229 | 2912.4 | 72.1 | 1.000 |
| command-r7b:7b | 4.476 | 0.235 | 2627.9 | 70.7 | 1.000 |
| aya-expanse:8b | 4.341 | 0.190 | 3357.3 | 70.2 | 1.000 |
| mistral-nemo:12b | 6.459 | 0.346 | 1492.2 | 22.9 | 0.798 |
| gemma3:12b | 9.098 | 0.800 | 631.7 | 10.0 | 0.608 |
| qwen3:14b | 7.822 | 0.684 | 725.0 | 8.8 | 0.626 |
| bge-m3:latest | 1.430 | немає даних | немає даних | немає даних | 1.000 |
| nomic-embed-text:latest | 0.592 | немає даних | немає даних | немає даних | 1.000 |
- Частковий CPU offload (offload ratio < 1.0; модель не вмістилась у 8 GB VRAM, тому повільніша за свій розмір): gemma3:12b, mistral-nemo:12b, qwen3:14b.


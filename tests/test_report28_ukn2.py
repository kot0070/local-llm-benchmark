"""W_UKN2 checks: analysis_uk/group_n2.json mirrors analysis_en/group_n2.json.

A1: 4 models, per_test 24/24 each, parallel EN/UK walk with 0 numeric diffs
    (int/float fields AND numbers inside strings), 0 quote diffs, 0 identifier diffs.
A2: outcome vocab only the 5 fixed strings; no untranslated EN prose left;
    canonical-terms grep clean.
A3: numeral-noun agreement correct, incl. every X iz Y genitive construction.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN_PATH = ROOT / "analysis_en" / "group_n2.json"
UK_PATH = ROOT / "analysis_uk" / "group_n2.json"

OUTCOME_MAP = {
    "strong": "сильно",
    "adequate": "задовільно",
    "weak": "слабко",
    "failed": "провал",
    "not attempted": "не виконувався",
}
UK_OUTCOMES = set(OUTCOME_MAP.values())

PROSE_KEYS = {
    "documented", "role_in_run", "rating_basis", "analysis", "title",
    "note", "english_meaning", "what_the_model_did", "why_it_matters",
    "hardware_fit", "bottom_line",
}
PROSE_LIST_KEYS = {"strengths", "weaknesses", "use_when", "avoid_when"}

# numbers incl. comma-grouped thousands (EN "9,000" == UK "9000")
NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _norm_num(tok):
    return tok.replace(",", "")


def _nums(s):
    return [_norm_num(t) for t in NUM_RE.findall(s)]


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def _walk(en, uk, num_diffs, strnum_diffs):
    if isinstance(en, dict):
        assert set(uk.keys()) == set(en.keys()), f"key mismatch {set(en)} vs {set(uk)}"
        for k in en:
            _walk(en[k], uk[k], num_diffs, strnum_diffs)
    elif isinstance(en, list):
        assert len(uk) == len(en), f"list len {len(en)} vs {len(uk)}"
        for a, b in zip(en, uk):
            _walk(a, b, num_diffs, strnum_diffs)
    elif isinstance(en, bool) or en is None:
        assert uk == en, f"scalar {en!r} vs {uk!r}"
    elif isinstance(en, (int, float)):
        assert uk == en, f"numeric {en!r} vs {uk!r}"
        if uk != en:
            num_diffs.append((en, uk))
    elif isinstance(en, str):
        if _nums(en) != _nums(uk):
            strnum_diffs.append((en, uk))


def test_a1_models_and_counts():
    en, uk = _load(EN_PATH), _load(UK_PATH)
    assert [m["model"] for m in uk] == [m["model"] for m in en]
    assert len(uk) == 4
    for m in uk:
        assert len(m["per_test"]) == 24, m["model"]


def test_a1_parallel_walk_no_numeric_diffs():
    en, uk = _load(EN_PATH), _load(UK_PATH)
    num_diffs, strnum_diffs = [], []
    _walk(en, uk, num_diffs, strnum_diffs)
    assert num_diffs == []
    assert strnum_diffs == [], strnum_diffs[:3]


def test_a1_quotes_and_identifiers():
    en, uk = _load(EN_PATH), _load(UK_PATH)
    for em, um in zip(en, uk):
        assert um["model"] == em["model"]
        for ep, up in zip(em["per_test"], um["per_test"]):
            assert up["test_id"] == ep["test_id"]
        for ef, uf in zip(em["failure_analysis"], um["failure_analysis"]):
            assert uf["pattern"] == ef["pattern"]
            assert uf["count"] == ef["count"]
            assert uf["example_case_id"] == ef["example_case_id"]
            assert uf["example_quote"] == ef["example_quote"], uf["example_case_id"]
        assert um["home_test"]["test_id"] == em["home_test"]["test_id"] is None
        assert um["home_test"]["title"] == "немає власного тесту"
        assert um["home_test"]["q_sem"] is None and um["home_test"]["q_strict"] is None
        assert um["home_test"]["n"] == "-"


def test_a1_outcome_mapping():
    en, uk = _load(EN_PATH), _load(UK_PATH)
    for em, um in zip(en, uk):
        for ep, up in zip(em["per_test"], um["per_test"]):
            assert up["outcome"] == OUTCOME_MAP[ep["outcome"]], up["test_id"]


def test_a2_outcome_vocab_only():
    uk = _load(UK_PATH)
    for m in uk:
        for p in m["per_test"]:
            assert p["outcome"] in UK_OUTCOMES, (m["model"], p["test_id"], p["outcome"])


def test_a2_no_untranslated_prose():
    en, uk = _load(EN_PATH), _load(UK_PATH)
    same = []
    no_cyr = []
    for em, um in zip(en, uk):
        pairs = [
            (em["profile"]["documented"], um["profile"]["documented"]),
            (em["profile"]["role_in_run"], um["profile"]["role_in_run"]),
            (em["overall"]["rating_basis"], um["overall"]["rating_basis"]),
            (em["home_test"]["analysis"], um["home_test"]["analysis"]),
            (em["hardware_fit"], um["hardware_fit"]),
            (em["bottom_line"], um["bottom_line"]),
        ]
        for ep, up in zip(em["per_test"], um["per_test"]):
            pairs += [(ep["title"], up["title"]), (ep["note"], up["note"])]
        for ef, uf in zip(em["failure_analysis"], um["failure_analysis"]):
            pairs += [(ef["english_meaning"], uf["english_meaning"]),
                      (ef["what_the_model_did"], uf["what_the_model_did"]),
                      (ef["why_it_matters"], uf["why_it_matters"])]
        for k in PROSE_LIST_KEYS:
            pairs += list(zip(em[k], um[k]))
        for a, b in pairs:
            if a == b:
                same.append((um["model"], a[:60]))
            if b and not re.search(r"[\u0400-\u04FF]", b):
                no_cyr.append((um["model"], b[:60]))
    assert same == [], same[:5]
    assert no_cyr == [], no_cyr[:5]


# Latin tokens allowed inside UA prose: metric/acronym/identifier names only.
LATIN_OK = {
    "RAG", "JSON", "SQL", "SQLite", "HTML", "Markdown", "GGUF", "Ollama",
    "CSV", "TECH", "OCR", "PERF", "HOME", "OK", "HR", "boxed", "GPU",
}
LATIN_RE = re.compile(r"[A-Za-z]{2,}")


def _prose_texts(uk):
    out = []
    for m in uk:
        out += [m["profile"]["documented"], m["profile"]["role_in_run"],
                m["overall"]["rating_basis"], m["home_test"]["analysis"],
                m["hardware_fit"], m["bottom_line"]]
        for p in m["per_test"]:
            out += [p["title"], p["note"]]
        for f in m["failure_analysis"]:
            out += [f["english_meaning"], f["what_the_model_did"], f["why_it_matters"]]
        for k in PROSE_LIST_KEYS:
            out += m[k]
    return out


def test_a2_no_latin_sentences():
    bad = []
    for t in _prose_texts(_load(UK_PATH)):
        for w in LATIN_RE.findall(t):
            if w not in LATIN_OK:
                bad.append((w, t[:80]))
    assert bad == [], bad[:8]


def test_a2_canonical_terms():
    t = "\n".join(_prose_texts(_load(UK_PATH)))
    assert "паркан" not in t
    assert "огорож" not in t
    assert "ембеддинг" not in t
    assert re.search(r"блок", t)
    assert "ембедінг" in t
    assert "Холодне завантаження" in t
    assert "гостьов" in t
    assert "бокс-формат" in t
    assert "обріз" in t


def _expected_uk_form(n):
    if n % 10 == 1 and n % 100 != 11:
        return 0
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return 1
    return 2


def test_a3_numeral_agreement():
    texts = _prose_texts(_load(UK_PATH))
    bad = []
    fams = [
        (["раз", "рази", "разів"], re.compile(r"(\d+)\s+(раз|рази|разів)\b")),
        (["запис", "записи", "записів"], re.compile(r"(\d+)\s+(запис|записи|записів)\b")),
        (["випадок", "випадки", "випадків"],
         re.compile(r"(\d+)\s+(випадок|випадки|випадків)\b")),
    ]
    for t in texts:
        for forms, rx in fams:
            for m in rx.finditer(t):
                n = int(m.group(1))
                if forms[_expected_uk_form(n)] != m.group(2):
                    bad.append(m.group(0))
    assert bad == [], bad[:8]


def test_a3_iz_y_genitive():
    gen_pl = {"випадків", "тестів", "запитів", "звернень", "ранжувань",
              "патчів", "викликів", "генерацій", "разів", "текстів"}
    rx = re.compile(r"із\s+(\d+)\s+([А-Яа-яЇїІіЄєҐґ']+)(?:\s+([А-Яа-яЇїІіЄєҐґ']+))?")
    bad = []
    for t in _prose_texts(_load(UK_PATH)):
        for m in rx.finditer(t):
            if m.group(2) not in gen_pl and (not m.group(3) or m.group(3) not in gen_pl):
                bad.append(m.group(0))
    assert bad == [], bad[:8]

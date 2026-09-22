"""Generator for HOME-14 (codegen with hidden tests). Owner: TASK_B1."""
from __future__ import annotations

import hashlib
import copy
import json
import sys
from pathlib import Path

TEST_ID = "HOME-14"
SEED = 1414
VERSION = "n1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bench.validate import pysandbox  # noqa: E402

CODE_SUFFIX = ("Output exactly one ```python fenced block containing the complete "
               "function, and nothing else.")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_cases_and_manifest(out_dir: Path, cases: list[dict]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    cases_path = out_dir / "cases.jsonl"
    with open(cases_path, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, sort_keys=True, ensure_ascii=False) + "\n")
    files = {"cases.jsonl": sha256_file(cases_path)}
    manifest = {"test_id": TEST_ID, "seed": SEED, "generator": "gen_home_14.py",
                "version": VERSION, "n_cases": len(cases), "files": files}
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def interleave(easy, medium, hard):
    out: list[dict] = []
    lists = [list(easy), list(medium), list(hard)]
    while any(lists):
        for lst in lists:
            if lst:
                out.append(lst.pop(0))
    return out


TASKS: list[dict] = [
    dict(tier="easy", task_id="norm_spaces", func="normalize_spaces", sig="def normalize_spaces(s):",
         title="Collapse whitespace",
         spec=("Return the string with every run of whitespace (spaces, tabs, newlines) "
               "replaced by a single space, and leading/trailing whitespace removed."),
         examples=[("  hello   world ", "hello world"), ("a\t\tb\nc", "a b c")],
         tests=[{"args": ["  hello   world "], "expected": "hello world"},
                {"args": ["a\t\tb\nc"], "expected": "a b c"},
                {"args": [""], "expected": ""},
                {"args": ["   "], "expected": ""},
                {"args": ["nochange"], "expected": "nochange"},
                {"args": [" a  b  c "], "expected": "a b c"},
                {"args": ["\t\n x \r\n y\t"], "expected": "x y"},
                {"args": ["multiple     spaces"], "expected": "multiple spaces"}],
         ref=("def normalize_spaces(s):\n"
              "    return ' '.join(s.split())\n")),
    dict(tier="easy", task_id="count_init", func="count_initial", sig="def count_initial(text, letter):",
         title="Count words by initial letter",
         spec=("Count how many whitespace-separated words in text start with the given "
               "letter, case-insensitively. Empty words are ignored."),
         examples=[("Apple apricot Banana", "a", 2), ("one two three", "z", 0)],
         tests=[{"args": ["Apple apricot Banana", "a"], "expected": 2},
                {"args": ["one two three", "z"], "expected": 0},
                {"args": ["", "a"], "expected": 0},
                {"args": ["aaa AAA aAa", "A"], "expected": 3},
                {"args": ["  spaced   out ", "s"], "expected": 1},
                {"args": ["cat dog cow", "c"], "expected": 2},
                {"args": ["x", "x"], "expected": 1},
                {"args": ["MixED mIx", "m"], "expected": 2}],
         ref=("def count_initial(text, letter):\n"
              "    letter = letter.lower()\n"
              "    return sum(1 for w in text.split() if w and w[0].lower() == letter)\n")),
    dict(tier="easy", task_id="sum_sq_even", func="sum_sq_even", sig="def sum_sq_even(nums):",
         title="Sum of squares of evens",
         spec="Return the sum of squares of the even integers in the list nums.",
         examples=[([1, 2, 3, 4], 20), ([1, 3, 5], 0)],
         tests=[{"args": [[1, 2, 3, 4]], "expected": 20},
                {"args": [[1, 3, 5]], "expected": 0},
                {"args": [[]], "expected": 0},
                {"args": [[0]], "expected": 0},
                {"args": [[-2, -3, 4]], "expected": 20},
                {"args": [[10]], "expected": 100},
                {"args": [[2, 2, 2]], "expected": 12},
                {"args": [[7, 8]], "expected": 64}],
         ref=("def sum_sq_even(nums):\n"
              "    return sum(x * x for x in nums if x % 2 == 0)\n")),
    dict(tier="easy", task_id="acronym", func="acronym", sig="def acronym(phrase):",
         title="Acronym builder",
         spec=("Build the acronym of phrase: the uppercase first letter of every "
               "whitespace-separated word, joined without separators."),
         examples=[("as soon as possible", "ASAP"), ("hello", "H")],
         tests=[{"args": ["as soon as possible"], "expected": "ASAP"},
                {"args": ["hello"], "expected": "H"},
                {"args": [""], "expected": ""},
                {"args": ["  leading space"], "expected": "LS"},
                {"args": ["one-two three"], "expected": "OT"},
                {"args": ["UPPER lower"], "expected": "UL"},
                {"args": ["a b c"], "expected": "ABC"},
                {"args": ["  "], "expected": ""}],
         ref=("def acronym(phrase):\n"
              "    return ''.join(w[0].upper() for w in phrase.split() if w)\n")),
    dict(tier="easy", task_id="anagram", func="is_anagram", sig="def is_anagram(a, b):",
         title="Anagram check",
         spec=("Return True if a and b are anagrams of each other, comparing "
               "case-insensitively and ignoring spaces; otherwise False."),
         examples=[("listen", "silent", True), ("hello", "world", False)],
         tests=[{"args": ["listen", "silent"], "expected": True},
                {"args": ["hello", "world"], "expected": False},
                {"args": ["Dormitory", "dirty room"], "expected": True},
                {"args": ["", ""], "expected": True},
                {"args": ["a", "A"], "expected": True},
                {"args": ["abc", "ab"], "expected": False},
                {"args": ["Eleven plus two", "Twelve plus one"], "expected": True},
                {"args": ["test", "tset "], "expected": True}],
         ref=("def is_anagram(a, b):\n"
              "    na = sorted(a.lower().replace(' ', ''))\n"
              "    nb = sorted(b.lower().replace(' ', ''))\n"
              "    return na == nb\n")),
    dict(tier="medium", task_id="csv_line", func="parse_csv_line", sig="def parse_csv_line(line):",
         title="Minimal CSV line parser",
         spec=("Split one CSV line on commas. Fields may be wrapped in double quotes; "
               "quoted fields may contain commas, and a doubled quote (\"\") inside a "
               "quoted field means a literal quote. Quotes are not part of the result."),
         examples=[('a,b,c', ["a", "b", "c"]), ('"a,b",c', ["a,b", "c"])],
         tests=[{"args": ["a,b,c"], "expected": ["a", "b", "c"]},
                {"args": ['"a,b",c'], "expected": ["a,b", "c"]},
                {"args": [""], "expected": [""]},
                {"args": ['"a""b",c'], "expected": ['a"b', "c"]},
                {"args": ['a,"",c'], "expected": ["a", "", "c"]},
                {"args": ['" spaced "'], "expected": [" spaced "]},
                {"args": ["a,b,"], "expected": ["a", "b", ""]},
                {"args": [",,,"], "expected": ["", "", "", ""]},
                {"args": ['"x","y,z","w"'], "expected": ["x", "y,z", "w"]}],
         ref=("def parse_csv_line(line):\n"
              "    fields = []\n"
              "    cur = []\n"
              "    i = 0\n"
              "    in_q = False\n"
              "    while i < len(line):\n"
              "        ch = line[i]\n"
              "        if in_q:\n"
              "            if ch == '\"':\n"
              "                if i + 1 < len(line) and line[i + 1] == '\"':\n"
              "                    cur.append('\"')\n"
              "                    i += 2\n"
              "                else:\n"
              "                    in_q = False\n"
              "                    i += 1\n"
              "            else:\n"
              "                cur.append(ch)\n"
              "                i += 1\n"
              "        else:\n"
              "            if ch == '\"':\n"
              "                in_q = True\n"
              "                i += 1\n"
              "            elif ch == ',':\n"
              "                fields.append(''.join(cur))\n"
              "                cur = []\n"
              "                i += 1\n"
              "            else:\n"
              "                cur.append(ch)\n"
              "                i += 1\n"
              "    fields.append(''.join(cur))\n"
              "    return fields\n")),
    dict(tier="medium", task_id="rle", func="rle_encode", sig="def rle_encode(s):",
         title="Run-length encoding",
         spec=("Encode s as character-plus-count runs: each maximal run of identical "
               "characters becomes the character followed by the run length "
               '(e.g. "aaabb" -> "a3b2"). Empty string encodes to empty string.'),
         examples=[("aaabb", "a3b2"), ("abc", "a1b1c1")],
         tests=[{"args": ["aaabb"], "expected": "a3b2"},
                {"args": ["abc"], "expected": "a1b1c1"},
                {"args": [""], "expected": ""},
                {"args": ["a"], "expected": "a1"},
                {"args": ["aaaaaaaaaa"], "expected": "a10"},
                {"args": ["aabbaa"], "expected": "a2b2a2"},
                {"args": ["112233"], "expected": "122232"},
                {"args": ["AB B"], "expected": "A1B1 1B1"}],
         ref=("def rle_encode(s):\n"
              "    if not s:\n"
              "        return ''\n"
              "    out = []\n"
              "    cur, n = s[0], 1\n"
              "    for ch in s[1:]:\n"
              "        if ch == cur:\n"
              "            n += 1\n"
              "        else:\n"
              "            out.append(f'{cur}{n}')\n"
              "            cur, n = ch, 1\n"
              "    out.append(f'{cur}{n}')\n"
              "    return ''.join(out)\n")),
    dict(tier="medium", task_id="merge_iv", func="merge_intervals", sig="def merge_intervals(intervals):",
         title="Merge intervals",
         spec=("Merge overlapping [start, end] intervals (inclusive endpoints: touching "
               "intervals such as [1,2] and [2,3] merge). Input and output are lists of "
               "[start, end] pairs; output is sorted by start."),
         examples=[([[1, 3], [2, 6], [8, 10]], [[1, 6], [8, 10]]),
                   ([[1, 2], [3, 4]], [[1, 2], [3, 4]])],
         tests=[{"args": [[[1, 3], [2, 6], [8, 10]]], "expected": [[1, 6], [8, 10]]},
                {"args": [[[1, 2], [3, 4]]], "expected": [[1, 2], [3, 4]]},
                {"args": [[]], "expected": []},
                {"args": [[[5, 5]]], "expected": [[5, 5]]},
                {"args": [[[1, 2], [2, 3]]], "expected": [[1, 3]]},
                {"args": [[[3, 4], [1, 2]]], "expected": [[1, 2], [3, 4]]},
                {"args": [[[1, 10], [2, 3], [4, 5]]], "expected": [[1, 10]]},
                {"args": [[[2, 2], [2, 2]]], "expected": [[2, 2]]}],
         ref=("def merge_intervals(intervals):\n"
              "    if not intervals:\n"
              "        return []\n"
              "    ivs = sorted(intervals)\n"
              "    out = [list(ivs[0])]\n"
              "    for s, e in ivs[1:]:\n"
              "        if s <= out[-1][1]:\n"
              "            out[-1][1] = max(out[-1][1], e)\n"
              "        else:\n"
              "            out.append([s, e])\n"
              "    return out\n")),
    dict(tier="medium", task_id="topk", func="top_k_frequent", sig="def top_k_frequent(words, k):",
         title="Top-k frequent words",
         spec=("Return the k most frequent words, ordered by decreasing frequency; "
               "ties are broken alphabetically ascending. If k exceeds the number of "
               "distinct words, return all of them."),
         examples=[(["b", "a", "b", "c", "a", "b"], 2, ["b", "a"])],
         tests=[{"args": [["b", "a", "b", "c", "a", "b"], 2], "expected": ["b", "a"]},
                {"args": [["x"], 1], "expected": ["x"]},
                {"args": [["b", "a", "c"], 3], "expected": ["a", "b", "c"]},
                {"args": [["b", "a", "c"], 9], "expected": ["a", "b", "c"]},
                {"args": [[], 3], "expected": []},
                {"args": [["aa", "aa", "b", "b", "c"], 2], "expected": ["aa", "b"]},
                {"args": [["z", "y", "x"], 1], "expected": ["x"]},
                {"args": [["m", "n", "m", "n", "o"], 2], "expected": ["m", "n"]}],
         ref=("def top_k_frequent(words, k):\n"
              "    from collections import Counter\n"
              "    c = Counter(words)\n"
              "    ranked = sorted(c, key=lambda w: (-c[w], w))\n"
              "    return ranked[:k]\n")),
    dict(tier="medium", task_id="rpn", func="eval_rpn", sig="def eval_rpn(tokens):",
         title="Evaluate RPN",
         spec=("Evaluate tokens in Reverse Polish Notation. Operators + - * / apply to "
               "integers; division truncates toward zero. Every input is valid RPN "
               "with exactly one final value."),
         examples=[(["2", "1", "+", "3", "*"], 9), (["4", "13", "5", "/", "+"], 6)],
         tests=[{"args": [["2", "1", "+", "3", "*"]], "expected": 9},
                {"args": [["4", "13", "5", "/", "+"]], "expected": 6},
                {"args": [["18"]], "expected": 18},
                {"args": [["3", "-4", "+"]], "expected": -1},
                {"args": [["-7", "3", "/"]], "expected": -2},
                {"args": [["7", "-3", "/"]], "expected": -2},
                {"args": [["2", "3", "-", "4", "*"]], "expected": -4},
                {"args": [["5", "1", "2", "+", "4", "*", "+", "3", "-"]], "expected": 14}],
         ref=("def eval_rpn(tokens):\n"
              "    st = []\n"
              "    for t in tokens:\n"
              "        if t in ('+', '-', '*', '/'):\n"
              "            b, a = st.pop(), st.pop()\n"
              "            if t == '+':\n"
              "                st.append(a + b)\n"
              "            elif t == '-':\n"
              "                st.append(a - b)\n"
              "            elif t == '*':\n"
              "                st.append(a * b)\n"
              "            else:\n"
              "                q = abs(a) // abs(b)\n"
              "                st.append(q if (a >= 0) == (b >= 0) else -q)\n"
              "        else:\n"
              "            st.append(int(t))\n"
              "    return st[0]\n")),
    dict(tier="medium", task_id="swmax", func="sliding_max", sig="def sliding_max(nums, k):",
         title="Sliding window maximum",
         spec=("Return the maximum of every contiguous window of size k in nums. "
               "1 <= k <= len(nums)."),
         examples=[([1, 3, -1, -3, 5, 3, 6, 7], 3, [3, 3, 5, 5, 6, 7])],
         tests=[{"args": [[1, 3, -1, -3, 5, 3, 6, 7], 3], "expected": [3, 3, 5, 5, 6, 7]},
                {"args": [[1], 1], "expected": [1]},
                {"args": [[4, 3, 2, 1], 4], "expected": [4]},
                {"args": [[1, 2, 3, 4], 1], "expected": [1, 2, 3, 4]},
                {"args": [[5, 5, 5], 2], "expected": [5, 5]},
                {"args": [[-1, -2, -3], 2], "expected": [-1, -2]},
                {"args": [[9, 1, 9, 1, 9], 2], "expected": [9, 9, 9, 9]},
                {"args": [[3, 1, 2], 3], "expected": [3]}],
         ref=("def sliding_max(nums, k):\n"
              "    from collections import deque\n"
              "    dq = deque()\n"
              "    out = []\n"
              "    for i, x in enumerate(nums):\n"
              "        while dq and dq[0] <= i - k:\n"
              "            dq.popleft()\n"
              "        while dq and nums[dq[-1]] <= x:\n"
              "            dq.pop()\n"
              "        dq.append(i)\n"
              "        if i >= k - 1:\n"
              "            out.append(nums[dq[0]])\n"
              "    return out\n")),
    dict(tier="hard", task_id="wrap", func="word_wrap", sig="def word_wrap(text, width):",
         title="Greedy word wrap",
         spec=("Wrap text into lines of at most width characters using greedy "
               "word packing: words are whitespace-separated, words on a line are "
               "joined by single spaces, and a word never splits. Every word fits "
               "within width. Return the list of lines."),
         examples=[("the quick brown fox", 10, ["the quick", "brown fox"])],
         tests=[{"args": ["the quick brown fox", 10], "expected": ["the quick", "brown fox"]},
                {"args": ["hello", 10], "expected": ["hello"]},
                {"args": ["a b c", 1], "expected": ["a", "b", "c"]},
                {"args": ["", 5], "expected": []},
                {"args": ["aa bb cc", 5], "expected": ["aa bb", "cc"]},
                {"args": ["aa bb cc", 4], "expected": ["aa", "bb", "cc"]},
                {"args": ["one  two   three", 8], "expected": ["one two", "three"]},
                {"args": ["ab cd ef gh", 5], "expected": ["ab cd", "ef gh"]}],
         ref=("def word_wrap(text, width):\n"
              "    words = text.split()\n"
              "    lines, cur = [], ''\n"
              "    for w in words:\n"
              "        if not cur:\n"
              "            cur = w\n"
              "        elif len(cur) + 1 + len(w) <= width:\n"
              "            cur += ' ' + w\n"
              "        else:\n"
              "            lines.append(cur)\n"
              "            cur = w\n"
              "    if cur:\n"
              "        lines.append(cur)\n"
              "    return lines\n")),
    dict(tier="hard", task_id="jpath", func="json_path_get", sig="def json_path_get(obj, path):",
         title="Dotted JSON path lookup",
         spec=("Look up a dotted path in nested dicts/lists: segments split on '.'; "
               "a segment like key[2] indexes list key at 2; a bare [0] indexes the "
               "current list. Return the value, or None if anything is missing or "
               "an index is out of range."),
         examples=[({"a": {"b": [1, 2]}}, "a.b[1]", 2)],
         tests=[{"args": [{"a": {"b": [1, 2]}}, "a.b[1]"], "expected": 2},
                {"args": [{"a": 1}, "a"], "expected": 1},
                {"args": [{"a": 1}, "b"], "expected": None},
                {"args": [{"a": [1, 2]}, "a[5]"], "expected": None},
                {"args": [{"a": {"b": {"c": 7}}}, "a.b.c"], "expected": 7},
                {"args": [[10, 20], "[0]"], "expected": 10},
                {"args": [{"a": [1, 2]}, "a"], "expected": [1, 2]},
                {"args": [{"a": {"b": 1}}, "a.b.c"], "expected": None},
                {"args": [{"a": None}, "a"], "expected": None}],
         ref=("def json_path_get(obj, path):\n"
              "    import re\n"
              "    cur = obj\n"
              "    for seg in path.split('.'):\n"
              "        m = re.match(r'^([A-Za-z0-9_]*)(\\[\\d+\\])*$', seg)\n"
              "        if not m:\n"
              "            return None\n"
              "        key = seg.split('[')[0]\n"
              "        idxs = re.findall(r'\\[(\\d+)\\]', seg)\n"
              "        if key:\n"
              "            if not isinstance(cur, dict) or key not in cur:\n"
              "                return None\n"
              "            cur = cur[key]\n"
              "        for ix in idxs:\n"
              "            if not isinstance(cur, list):\n"
              "                return None\n"
              "            i = int(ix)\n"
              "            if i >= len(cur):\n"
              "                return None\n"
              "            cur = cur[i]\n"
              "    return cur\n")),
    dict(tier="hard", task_id="uniqsub", func="longest_unique_len", sig="def longest_unique_len(s):",
         title="Longest substring without repeats",
         spec=("Return the length of the longest contiguous substring of s that "
               "contains no repeated character."),
         examples=[("abcabcbb", 3), ("bbbbb", 1)],
         tests=[{"args": ["abcabcbb"], "expected": 3},
                {"args": ["bbbbb"], "expected": 1},
                {"args": [""], "expected": 0},
                {"args": ["abcdef"], "expected": 6},
                {"args": ["pwwkew"], "expected": 3},
                {"args": ["abba"], "expected": 2},
                {"args": ["dvdf"], "expected": 3},
                {"args": ["a"], "expected": 1}],
         ref=("def longest_unique_len(s):\n"
              "    seen = {}\n"
              "    start = best = 0\n"
              "    for i, ch in enumerate(s):\n"
              "        if ch in seen and seen[ch] >= start:\n"
              "            start = seen[ch] + 1\n"
              "        seen[ch] = i\n"
              "        best = max(best, i - start + 1)\n"
              "    return best\n")),
    dict(tier="hard", task_id="turnstile", func="turnstile", sig="def turnstile(events):",
         title="Turnstile state machine",
         spec=("Simulate a turnstile. States: LOCKED, UNLOCKED. Events: 'coin' unlocks "
               "(from LOCKED); 'push' passes through when UNLOCKED and locks it again. "
               "A 'push' while LOCKED is an alarm. Return [final_state, alarms]."),
         examples=[(["coin", "push"], ["LOCKED", 0])],
         tests=[{"args": [["coin", "push"]], "expected": ["LOCKED", 0]},
                {"args": [["push"]], "expected": ["LOCKED", 1]},
                {"args": [[]], "expected": ["LOCKED", 0]},
                {"args": [["coin", "coin", "push"]], "expected": ["LOCKED", 0]},
                {"args": [["push", "push"]], "expected": ["LOCKED", 2]},
                {"args": [["coin", "push", "push", "coin"]], "expected": ["UNLOCKED", 1]},
                {"args": [["coin"]], "expected": ["UNLOCKED", 0]},
                {"args": [["push", "coin", "push"]], "expected": ["LOCKED", 1]}],
         ref=("def turnstile(events):\n"
              "    state = 'LOCKED'\n"
              "    alarms = 0\n"
              "    for e in events:\n"
              "        if e == 'coin':\n"
              "            state = 'UNLOCKED'\n"
              "        elif e == 'push':\n"
              "            if state == 'UNLOCKED':\n"
              "                state = 'LOCKED'\n"
              "            else:\n"
              "                alarms += 1\n"
              "    return [state, alarms]\n")),
    dict(tier="hard", task_id="b36add", func="base36_add", sig="def base36_add(a, b):",
         title="Base-36 addition",
         spec=("Add two non-negative base-36 numbers (digits 0-9a-z, lowercase) given "
               "as strings without leading zeros (except '0' itself). Return the sum "
               "as a base-36 string, same format."),
         examples=[("z", "1", "10"), ("10", "10", "20")],
         tests=[{"args": ["z", "1"], "expected": "10"},
                {"args": ["10", "10"], "expected": "20"},
                {"args": ["0", "0"], "expected": "0"},
                {"args": ["a", "a"], "expected": "k"},
                {"args": ["zz", "1"], "expected": "100"},
                {"args": ["hello", "world"], "expected": None},
                {"args": ["36", "36"], "expected": "6c"},
                {"args": ["abc", "0"], "expected": "abc"}],
         ref=("def base36_add(a, b):\n"
              "    digs = '0123456789abcdefghijklmnopqrstuvwxyz'\n"
              "    val = {c: i for i, c in enumerate(digs)}\n"
              "    i, j, carry, out = len(a) - 1, len(b) - 1, 0, []\n"
              "    while i >= 0 or j >= 0 or carry:\n"
              "        da = val[a[i]] if i >= 0 else 0\n"
              "        db = val[b[j]] if j >= 0 else 0\n"
              "        s = da + db + carry\n"
              "        out.append(digs[s % 36])\n"
              "        carry = s // 36\n"
              "        i -= 1\n"
              "        j -= 1\n"
              "    return ''.join(reversed(out))\n")),
]


def _fix_b36_expected():
    # Fill the hello+world expected sum (computed, not hand-written).
    digs = "0123456789abcdefghijklmnopqrstuvwxyz"

    def from36(s):
        n = 0
        for c in s:
            n = n * 36 + digs.index(c)
        return n

    for t in TASKS:
        if t["task_id"] == "b36add":
            for tc in t["tests"]:
                if tc["expected"] is None:
                    a, b = tc["args"]
                    tc["expected"] = _b36(from36(a) + from36(b))


def _b36(n):
    digs = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = []
    while n:
        out.append(digs[n % 36])
        n //= 36
    return "".join(reversed(out))


def build_cases():
    _fix_b36_expected()
    by_tier: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for i, t in enumerate(TASKS):
        # Ground-truth verification: reference must pass all hidden tests.
        out = pysandbox.run_function_tests(t["ref"], t["func"], t["tests"],
                                           timeout_s=5.0)
        assert out["passed"] == out["total"] == len(t["tests"]), \
            (t["task_id"], out)
        # Signature uses the same meaningful parameter names as the spec;
        # hidden tests stay positional (args lists only).
        assert t["ref"].splitlines()[0].strip() == t["sig"], t["task_id"]
        assert all(set(tc) == {"args", "expected"} for tc in t["tests"]), \
            t["task_id"]
        ex_lines = []
        arity = len(t["tests"][0]["args"])
        ns: dict = {}
        exec(t["ref"], ns)  # trusted reference: examples must be real calls it satisfies
        for ex in t["examples"]:
            assert isinstance(ex, tuple) and len(ex) == arity + 1, (t["task_id"], ex)
            got = ns[t["func"]](*copy.deepcopy(list(ex[:-1])))
            assert json.loads(json.dumps(got)) == json.loads(json.dumps(ex[-1])), (t["task_id"], ex, got)
            ex_lines.append(f"  {t['func']}({', '.join(repr(a) for a in ex[:-1])}) -> {ex[-1]!r}")
        prompt = (f"Task: {t['title']}\n{t['spec']}\nSignature: "
                  f"{t['sig']}\nExamples:\n"
                  + "\n".join(ex_lines) + f"\n{CODE_SUFFIX}")
        by_tier[t["tier"]].append({
            "id": f"tmp-{i}",
            "test_id": TEST_ID,
            "tier": t["tier"],
            "lang": "en",
            "input": {"task_id": t["task_id"], "title": t["title"],
                      "signature": t["sig"],
                      "spec": t["spec"], "examples": t["examples"],
                      "func": t["func"], "prompt": prompt},
            "expected": {"func": t["func"], "tests": t["tests"],
                         "reference": t["ref"]},
            "meta": {},
        })
    cases = interleave(by_tier["easy"], by_tier["medium"], by_tier["hard"])
    for j, c in enumerate(cases):
        c["id"] = f"HOME-14-{j + 1:02d}"
    return cases


def main() -> Path:
    out_dir = Path(__file__).resolve().parents[1] / "fixtures" / TEST_ID
    cases = build_cases()
    assert len(cases) == 16, len(cases)
    for c in cases:
        assert len(c["expected"]["tests"]) >= 8, c["id"]
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for c in cases:
        counts[c["tier"]] += 1
    assert counts == {"easy": 5, "medium": 6, "hard": 5}, counts
    write_cases_and_manifest(out_dir, cases)
    return out_dir


if __name__ == "__main__":
    print(main())

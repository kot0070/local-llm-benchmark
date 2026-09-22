"""Unit tests for bench/validate/mdparse.py (owner: TASK_B2)."""
from bench.validate.mdparse import (block_scores, parse_markdown, text_token_f1,
                                    unwrap_code_fence)

MD = """# Title

Intro paragraph with a [link](https://example.com/x) inside.

## Section A

- item one
- item two
  - nested item

1. first step
2. second step

### Table part

| Flag | Default |
| --- | --- |
| workers | 4 |
| timeout | 30s |

```bash
echo hello
```

![alt diagram](https://cdn.example.com/img.png)
"""


def test_parse_blocks():
    b = parse_markdown(MD)
    assert [h["text"] for h in b["headings"]] == ["Title", "Section A", "Table part"]
    assert [h["level"] for h in b["headings"]] == [1, 2, 3]
    assert len(b["paragraphs"]) >= 1
    assert len(b["list_items"]) == 5
    depths = sorted(i["depth"] for i in b["list_items"])
    assert 0 in depths and 1 in depths
    assert len(b["table_cells"]) == 6  # 2 header + 4 body
    assert b["code_blocks"] == ["echo hello"]
    assert {"href": "https://example.com/x", "text": "link"} in b["links"]
    assert b["images"] == [{"href": "https://cdn.example.com/img.png", "text": "alt diagram"}]


def test_block_scores_identical():
    g = parse_markdown(MD)
    macro, per = block_scores(g, parse_markdown(MD))
    assert macro == 1.0
    assert all(v == 1.0 for v in per.values())
    assert set(per) == {"headings", "list_items", "table_cells", "code_blocks", "links"}


def test_block_scores_partial():
    g = parse_markdown(MD)
    p = parse_markdown("# Title\n\n- item one\n")
    macro, per = block_scores(g, p)
    assert 0.0 < macro < 1.0
    assert per["headings"] < 1.0  # missing two headings


def test_block_scores_empty_pred():
    g = parse_markdown(MD)
    macro, _ = block_scores(g, parse_markdown("nothing here\n"))
    assert macro == 0.0


def test_token_f1():
    assert text_token_f1("hello world", "hello world") == 1.0
    assert text_token_f1("hello world", "goodbye moon") == 0.0
    assert text_token_f1("", "") == 1.0
    f = text_token_f1("the cat sat", "the cat stood")
    assert 0.0 < f < 1.0


def test_unwrap_code_fence():
    inner, wrapped = unwrap_code_fence("```markdown\n# Hi\n```")
    assert wrapped is True
    assert inner == "# Hi"
    same, wrapped2 = unwrap_code_fence("# Hi\n\ntext")
    assert wrapped2 is False
    assert same == "# Hi\n\ntext"

"""Generator for HOME-19 HTML->Markdown (owner: TASK_B2). Seeded, self-verifying."""
from __future__ import annotations

import hashlib
import html as _html
import json
import random
from pathlib import Path

TEST_ID = "HOME-19"
SEED = 191919

BOILERPLATE_HTML = """<nav class="topnav"><a href="/">Home</a> | <a href="/docs">Docs</a> | <a href="/blog">Blog</a></nav>
<header><div class="menu">Products Solutions Pricing Contact Login</div></header>
<div class="cookie-banner">We value your privacy. Accept all cookies? <button>Accept</button></div>
<style>.main{max-width:800px;margin:auto}table{border-collapse:collapse}</style>
<script>window.__analytics={id:"UA-0000"};</script>"""
BOILERPLATE_TEXTS = ["Home", "Docs", "Blog", "Products Solutions Pricing Contact Login",
                     "We value your privacy. Accept all cookies?", "Accept"]

PAGES = [
    {"slug": "atlas-scheduler", "title": "Deploying the Atlas Scheduler",
     "h2": ["Prerequisites", "Configuration"], "h3": "Verifying the rollout",
     "table_head": ["Flag", "Default", "Meaning"], "table_rows": [["workers", "4", "Pool size"], ["timeout", "30s", "Task limit"]],
     "code_lang": "bash", "code": "atlas deploy --workers 4\natlas status --watch",
     "img_alt": "Scheduler overview diagram", "img_src": "https://cdn.example.com/img/atlas.png",
     "link_text": "operations guide", "link_href": "https://docs.example.com/atlas/ops",
     "items": ["Install the agent on each node", "Copy the token from the dashboard", "Start the service and check logs"],
     "code_inline": "atlas.yaml", "bold": "zero-downtime", "italic": "canary phase"},
    {"slug": "helios-api", "title": "Helios API Quickstart",
     "h2": ["Authentication", "First request"], "h3": "Handling errors",
     "table_head": ["Endpoint", "Method", "Purpose"], "table_rows": [["/v1/orders", "GET", "List orders"], ["/v1/refunds", "POST", "Create refund"]],
     "code_lang": "python", "code": "import helios\nclient = helios.Client(token=\"TK-123\")\nprint(client.orders())",
     "img_alt": "API sequence diagram", "img_src": "https://cdn.example.com/img/api.png",
     "link_text": "API reference", "link_href": "https://docs.example.com/helios/api",
     "items": ["Create a token in settings", "Install the SDK with pip", "Run the snippet below"],
     "code_inline": "client.orders()", "bold": "rate limit", "italic": "retry policy"},
    {"slug": "backup-runbook", "title": "Nightly Backup Runbook",
     "h2": ["Schedule", "Restore drill"], "h3": "Retention windows",
     "table_head": ["Tier", "Frequency", "Keep for"], "table_rows": [["Gold", "daily", "30 days"], ["Silver", "weekly", "90 days"]],
     "code_lang": "bash", "code": "backup run --tier gold\nbackup verify --latest",
     "img_alt": "Backup topology", "img_src": "https://cdn.example.com/img/backup.png",
     "link_text": "storage policy", "link_href": "https://docs.example.com/ops/storage",
     "items": ["Confirm disk space before midnight", "Run the job and watch the log", "Verify the checksum file"],
     "code_inline": "backup verify", "bold": "off-site copy", "italic": "quiet hours"},
    {"slug": "onboarding", "title": "New Engineer Onboarding",
     "h2": ["Week one", "First deploy"], "h3": "Buddy checklist",
     "table_head": ["Day", "Task", "Owner"], "table_rows": [["1", "Laptop setup", "IT"], ["3", "Shadow on-call", "Mentor"]],
     "code_lang": "bash", "code": "git clone ssh://repo/main.git\nmake setup",
     "img_alt": "Team map", "img_src": "https://cdn.example.com/img/team.png",
     "link_text": "handbook", "link_href": "https://docs.example.com/hr/handbook",
     "items": ["Meet the buddy and the team", "Read the handbook chapters", "Ship a docs fix"],
     "code_inline": "make setup", "bold": "first Friday demo", "italic": "open questions"},
    {"slug": "cache-tuning", "title": "Cache Tuning Guide",
     "h2": ["Measuring hits", "Eviction rules"], "h3": "Recommended defaults",
     "table_head": ["Key prefix", "TTL", "Notes"], "table_rows": [["sess:", "15m", "Volatile"], ["cfg:", "24h", "Rarely changes"]],
     "code_lang": "yaml", "code": "cache:\n  max_mb: 512\n  policy: lru",
     "img_alt": "Hit-ratio chart", "img_src": "https://cdn.example.com/img/cache.png",
     "link_text": "performance notes", "link_href": "https://docs.example.com/perf/cache",
     "items": ["Record the baseline hit ratio", "Apply one change at a time", "Roll back on regressions"],
     "code_inline": "max_mb", "bold": "thundering herd", "italic": "warm-up pass"},
    {"slug": "incident-review", "title": "Incident Review Template",
     "h2": ["Timeline", "Action items"], "h3": "What went well",
     "table_head": ["Time", "Event", "Owner"], "table_rows": [["09:40", "Alert fired", "Monitor"], ["09:55", "Mitigated", "On-call"]],
     "code_lang": "text", "code": "INC-4401 mitigated 09:55\nfollow-up: runbook update",
     "img_alt": "Timeline graphic", "img_src": "https://cdn.example.com/img/incident.png",
     "link_text": "review process", "link_href": "https://docs.example.com/ops/review",
     "items": ["Freeze the timeline early", "Assign every action an owner", "File the follow-up ticket"],
     "code_inline": "INC-4401", "bold": "blameless", "italic": "lucky break"},
    {"slug": "vpn-setup", "title": "Corporate VPN Setup",
     "h2": ["Enrollment", "Daily use"], "h3": "Troubleshooting",
     "table_head": ["OS", "Client", "Version"], "table_rows": [["Linux", "wg-client", "1.4"], ["Windows", "wg-client", "1.4"]],
     "code_lang": "bash", "code": "wg enroll --user $USER\nwg status",
     "img_alt": "VPN diagram", "img_src": "https://cdn.example.com/img/vpn.png",
     "link_text": "security baseline", "link_href": "https://docs.example.com/sec/baseline",
     "items": ["Enroll the device with IT", "Import the profile file", "Test access to git"],
     "code_inline": "wg status", "bold": "device certificate", "italic": "split tunnel"},
    {"slug": "release-notes", "title": "Release Notes 4.7",
     "h2": ["Highlights", "Fixes"], "h3": "Upgrade steps",
     "table_head": ["Area", "Change", "Issue"], "table_rows": [["Search", "Faster index", "#881"], ["Export", "CSV fix", "#902"]],
     "code_lang": "bash", "code": "app update --to 4.7\napp migrate --check",
     "img_alt": "Release banner", "img_src": "https://cdn.example.com/img/release.png",
     "link_text": "changelog", "link_href": "https://docs.example.com/app/changelog",
     "items": ["Read the highlights below", "Back up before upgrading", "Run the migration check"],
     "code_inline": "app migrate", "bold": "rollback plan", "italic": "maintenance window"},
]


def esc(s: str) -> str:
    return _html.escape(s, quote=True)


def render_html(p: dict) -> str:
    li = "\n".join(f"      <li>{esc(x)}</li>" for x in p["items"])
    rows = "\n".join("      <tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in p["table_rows"])
    head = "".join(f"<th>{esc(c)}</th>" for c in p["table_head"])
    return f"""<!DOCTYPE html>
<html><head><title>{esc(p['title'])}</title></head>
<body>
{BOILERPLATE_HTML}
<main>
<h1>{esc(p['title'])}</h1>
<p>This guide explains <code>{esc(p['code_inline'])}</code> with a <strong>{esc(p['bold'])}</strong> setup and an <em>{esc(p['italic'])}</em>. See the <a href="{esc(p['link_href'])}">{esc(p['link_text'])}</a> for background.</p>
<h2>{esc(p['h2'][0])}</h2>
<ul>
{li}
</ul>
<h2>{esc(p['h2'][1])}</h2>
<ol>
<li>Follow the steps in order
  <ul>
    <li>Nested check for {esc(p['slug'])}</li>
  </ul>
</li>
<li>Confirm with a colleague</li>
</ol>
<h3>{esc(p['h3'])}</h3>
<table>
<thead><tr>{head}</tr></thead>
<tbody>
{rows}
</tbody>
</table>
<pre><code class="language-{p['code_lang']}">{esc(p['code'])}</code></pre>
<img src="{esc(p['img_src'])}" alt="{esc(p['img_alt'])}" />
</main>
<footer>Helios Docs, 2026. All rights reserved.</footer>
</body></html>"""


def render_markdown(p: dict) -> str:
    li = "\n".join(f"- {x}" for x in p["items"])
    head = "| " + " | ".join(p["table_head"]) + " |"
    sep = "| " + " | ".join(["---"] * len(p["table_head"])) + " |"
    rows = "\n".join("| " + " | ".join(r) + " |" for r in p["table_rows"])
    return (f"# {p['title']}\n\n"
            f"This guide explains `{p['code_inline']}` with a **{p['bold']}** setup and an *{p['italic']}*. "
            f"See the [{p['link_text']}]({p['link_href']}) for background.\n\n"
            f"## {p['h2'][0]}\n\n{li}\n\n"
            f"## {p['h2'][1]}\n\n1. Follow the steps in order\n  - Nested check for {p['slug']}\n2. Confirm with a colleague\n\n"
            f"### {p['h3']}\n\n{head}\n{sep}\n{rows}\n\n"
            f"```{p['code_lang']}\n{p['code']}\n```\n\n"
            f"![{p['img_alt']}]({p['img_src']})\n")


def _sha256_file(p) -> str:
    import hashlib as _h
    h = _h.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    from pathlib import Path as _P
    root = _P(__file__).resolve().parents[1]
    dest = root / "fixtures" / TEST_ID
    assets = dest / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    pages = list(PAGES)
    rng.shuffle(pages)
    by_tier = {"easy": [], "medium": [], "hard": []}
    for i, p in enumerate(pages):
        by_tier[["easy", "medium", "hard"][i % 3]].append(p)
    ordered: list[dict] = []
    for k in range(max(len(v) for v in by_tier.values())):
        for t in ("easy", "medium", "hard"):
            if k < len(by_tier[t]):
                ordered.append((t, by_tier[t][k]))
    for n, (tier, p) in enumerate(ordered):
        html = render_html(p)
        md = render_markdown(p)
        # verification: gold contains key elements; boilerplate absent from md, present in html
        assert f"# {p['title']}" in md and p["code"] in md and p["link_href"] in md
        for b in BOILERPLATE_TEXTS:
            assert b not in md, f"boilerplate leak {b}"
        assert "topnav" in html and "cookie-banner" in html
        (assets / f"page-{n+1:02d}.html").write_text(html, encoding="utf-8")
        case = {"id": f"H19-{n+1:03d}", "test_id": TEST_ID, "tier": tier, "lang": "en",
                "input": {"html": html},
                "expected": {"markdown": md},
                "meta": {"slug": p["slug"], "boilerplate": BOILERPLATE_TEXTS, "seed": SEED}}
        ordered[n] = case
    with open(dest / "cases.jsonl", "w", encoding="utf-8") as f:
        for c in ordered:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files = {"cases.jsonl": _sha256_file(dest / "cases.jsonl")}
    for fp in sorted(assets.rglob("*")):
        if fp.is_file():
            files["assets/" + fp.relative_to(assets).as_posix()] = _sha256_file(fp)
    with open(dest / "manifest.json", "w", encoding="utf-8") as f:
        json.dump({"test_id": TEST_ID, "version": "n1", "seed": SEED, "files": files},
                  f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()

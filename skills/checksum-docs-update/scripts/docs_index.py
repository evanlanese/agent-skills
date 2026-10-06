#!/usr/bin/env python3
"""checksum-docs-update — diff the live Checksum docs against a saved index.

The Checksum docs (https://checksum.ai/docs) are a Mintlify site. Mintlify
auto-publishes a machine-readable index at /docs/llms.txt: one line per page
with its title, canonical URL, and frontmatter description. We treat that file
as the source of truth for "the set of topics on the site."

Modes:
  (default)  --check : fetch live index, diff vs saved baseline, print JSON. No write.
  --sync             : same diff, then overwrite the baseline with the live index.
  --init             : create the baseline from the live index (first-time setup). No diff.

The baseline lives in ../reference/docs-index.json (parsed) and ../reference/llms.txt (raw).

Fetching uses curl with a browser User-Agent. The docs site sits behind
Cloudflare; a browser UA returns 200 while some default agents get bounced.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

LLMS_URL = "https://checksum.ai/docs/llms.txt"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

REF = Path(__file__).resolve().parent.parent / "reference"
BASELINE = REF / "docs-index.json"
RAW = REF / "llms.txt"

# - [Title](url): optional description
LINE = re.compile(r"^- \[(.+?)\]\((.+?)\)(?::\s*(.*))?$")


def fetch():
    r = subprocess.run(["curl", "-sSL", "-A", UA, LLMS_URL],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(f"ERROR: failed to fetch {LLMS_URL}\n{r.stderr}")
    return r.stdout


def human_url(md_url):
    """Map a Mintlify .md source URL to the page a human would open."""
    if md_url.endswith("/index.md"):
        return md_url[:-len("/index.md")]
    if md_url.endswith(".md"):
        return md_url[:-len(".md")]
    return md_url


def area_of(md_url):
    """First path segment under /docs/ — the site section a page lives in."""
    m = re.search(r"/docs/([^/]+)/", md_url)
    return m.group(1) if m else "root"


def parse(text):
    """Parse llms.txt into {md_url: {title, url, page_url, area, description}}."""
    pages = {}
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("## "):
            continue
        m = LINE.match(line)
        if not m:
            continue
        title, url, desc = m.group(1), m.group(2), (m.group(3) or "").strip()
        if not url.endswith(".md"):  # skip openapi.json and other non-page specs
            continue
        pages[url] = {
            "title": title,
            "url": url,
            "page_url": human_url(url),
            "area": area_of(url),
            "description": desc,
        }
    return pages


def load_baseline():
    if not BASELINE.exists():
        return None
    return json.loads(BASELINE.read_text())


def diff(old_pages, new_pages):
    old_keys, new_keys = set(old_pages), set(new_pages)
    added = [new_pages[k] for k in sorted(new_keys - old_keys)]
    removed = [old_pages[k] for k in sorted(old_keys - new_keys)]
    changed = []
    for k in sorted(old_keys & new_keys):
        o, n = old_pages[k], new_pages[k]
        deltas = {}
        if o.get("title") != n.get("title"):
            deltas["title"] = {"before": o.get("title"), "after": n.get("title")}
        if o.get("description") != n.get("description"):
            deltas["description"] = {"before": o.get("description"),
                                     "after": n.get("description")}
        if deltas:
            changed.append({
                "title": n["title"],
                "page_url": n["page_url"],
                "area": n["area"],
                "deltas": deltas,
            })
    return added, removed, changed


def write_baseline(new_pages, raw):
    REF.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": LLMS_URL,
        "captured_at": str(date.today()),
        "page_count": len(new_pages),
        "pages": new_pages,
    }
    BASELINE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    RAW.write_text(raw)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--sync", action="store_true",
                   help="diff, then overwrite the baseline with the live index")
    g.add_argument("--init", action="store_true",
                   help="create the baseline from the live index (no diff)")
    args = ap.parse_args()

    raw = fetch()
    new_pages = parse(raw)

    if args.init or not BASELINE.exists():
        write_baseline(new_pages, raw)
        print(json.dumps({"mode": "init", "page_count": len(new_pages),
                          "captured_at": str(date.today())}, indent=2))
        return

    base = load_baseline()
    added, removed, changed = diff(base["pages"], new_pages)
    report = {
        "mode": "sync" if args.sync else "check",
        "source": LLMS_URL,
        "baseline_captured_at": base.get("captured_at"),
        "baseline_page_count": base.get("page_count"),
        "live_page_count": len(new_pages),
        "has_changes": bool(added or removed or changed),
        "added": added,
        "removed": removed,
        "changed": changed,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.sync:
        write_baseline(new_pages, raw)


if __name__ == "__main__":
    # The skill is decommissioned; the code above is kept for reference only.
    sys.exit("DECOMMISSIONED: checksum-docs-update was previously for internal use at Checksum "
             "and is now a non-functional skeleton kept on GitHub for "
             "demonstration purposes only. It no longer runs.")

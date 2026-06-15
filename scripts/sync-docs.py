#!/usr/bin/env python3
"""sync-docs.py — Copy canonical files into docs/ before mkdocs build.

Single source of truth stays in the repo root; docs/ gets build-only copies.
Run this before every `mkdocs build` or `mkdocs serve`.

Handles path rewriting: files in the root use "docs/..." links; when copied
into docs/ those prefixes are stripped so links resolve correctly at build time.
"""
import os
import re
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")


def _rewrite_paths(content: str) -> str:
    """Rewrite old paths in synced files to match the new docs/ structure."""
    # Strip docs/ prefix from links (files at root reference docs/...)
    content = re.sub(r'(\]\()docs/', r'\1', content)

    # Map old filenames to new paths in docs/
    path_map = {
        "OLLAMA_CONNECTION_TROUBLESHOOTING.md": "ops/troubleshooting.md",
        "ARCHITECTURE.md": "architecture/overview.md",
        "API_REFERENCE.md": "developer/api-reference.md",
        "DEVELOPER_GUIDE.md": "developer/getting-started.md",
        "ENVIRONMENT_VARIABLES.md": "ops/env-variables.md",
        "ESCALATION_LADDER.md": "labs/lab-format.md",
        "CHALLENGE_SOLUTIONS.md": "labs/scenario-list.md",
        "workshop-cloud-llm-setup.md": "ops/cloud-setup.md",
    }

    # Rewrite image paths in README: src="application/static/img/... -> src="...
    content = re.sub(r'src="application/static/img/', r'src="', content)

    # Also rewrite .env.example references in docs files
    if content.find("env.example") >= 0:
        content = re.sub(r'(\]\()(\.env\.example)\)', r'\1env.example)', content)

    for old, new in path_map.items():
        content = content.replace(old, new)

    return content


pairs = [
    ("README.md", "README.md"),                           # Landing page
    ("CONTRIBUTING.md", "community/contributing.md"),     # Community
    ("OLLAMA_CONNECTION_TROUBLESHOOTING.md", "ops/troubleshooting.md"),  # Ops
    ("tests/README.md", "quality-assurance/testing-guide.md"),  # QA
    (".env.example", "env.example"),                      # Root of docs
]

for src_rel, dst_name in pairs:
    src = os.path.join(REPO_ROOT, src_rel)
    dst = os.path.join(DOCS_DIR, dst_name)
    if not os.path.exists(src):
        print(f"  WARNING: {src} not found, skipping", file=sys.stderr)
        continue
    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    content = _rewrite_paths(content)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {src_rel} -> docs/{dst_name}")

print("Done. Run 'mkdocs build' or 'mkdocs serve' next.")

# Also copy images referenced by synced files
_IMG_DIR = os.path.join(REPO_ROOT, "application", "static", "img")
_SYNCED_IMGS = ["index.png"]

for img in _SYNCED_IMGS:
    src = os.path.join(_IMG_DIR, img)
    dst = os.path.join(DOCS_DIR, img)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  application/static/img/{img} -> docs/{img}")
    else:
        print(f"  WARNING: {src} not found, skipping", file=sys.stderr)

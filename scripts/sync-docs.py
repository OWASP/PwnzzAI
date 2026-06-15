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


def _rewrite_paths(content: str, dst_depth: int = 0) -> str:
    """Rewrite old paths in synced files to match the new docs/ structure.

    dst_depth: how many directories deep the destination is from docs/
               (0 = docs/README.md, 1 = docs/community/contributing.md, etc.)
    """
    prefix = "../" * dst_depth

    # Strip docs/ prefix from links (files at root reference docs/...)
    # and replace with the correct relative prefix for the destination depth
    content = re.sub(r'(\]\()docs/', lambda m: m.group(1) + prefix, content)

    # Map old filenames to new paths in docs/
    path_map = {
        "OLLAMA_CONNECTION_TROUBLESHOOTING.md": f"{prefix}ops/troubleshooting.md",
        "ARCHITECTURE.md": f"{prefix}architecture/overview.md",
        "API_REFERENCE.md": f"{prefix}developer/api-reference.md",
        "DEVELOPER_GUIDE.md": f"{prefix}developer/getting-started.md",
        "ENVIRONMENT_VARIABLES.md": f"{prefix}ops/env-variables.md",
        "ESCALATION_LADDER.md": f"{prefix}labs/lab-format.md",
        "CHALLENGE_SOLUTIONS.md": f"{prefix}labs/scenario-list.md",
        "workshop-cloud-llm-setup.md": f"{prefix}ops/cloud-setup.md",
    }

    # Rewrite image paths in README: src="application/static/img/... -> src="...
    content = re.sub(r'src="application/static/img/', r'src="', content)

    # Also rewrite .env.example references in docs files
    if content.find("env.example") >= 0:
        content = re.sub(r'(\]\()(\.env\.example)\)', rf'\1{prefix}env.example)', content)

    for old, new in path_map.items():
        content = content.replace(old, new)

    return content


pairs = [
    ("CONTRIBUTING.md", "community/contributing.md", 1),                 # Community
    ("OLLAMA_CONNECTION_TROUBLESHOOTING.md", "ops/troubleshooting.md", 1),  # Ops
    ("tests/README.md", "quality-assurance/testing-guide.md", 1),        # QA
    (".env.example", "env.example", 0),                                  # Root of docs
]

for src_rel, dst_name, depth in pairs:
    src = os.path.join(REPO_ROOT, src_rel)
    dst = os.path.join(DOCS_DIR, dst_name)
    if not os.path.exists(src):
        print(f"  WARNING: {src} not found, skipping", file=sys.stderr)
        continue
    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    content = _rewrite_paths(content, dst_depth=depth)
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

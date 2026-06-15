#!/usr/bin/env python3
"""check-doc-coverage.py — Ensure code changes have corresponding doc updates.

Compares routes and vulnerability modules against the API reference and
codebase map docs. Fails CI if anything is undocumented.

Zero dependencies — uses only Python stdlib (ast, os, glob, re, sys).
"""
import ast
import glob
import os
import re
import sys


DOCS_API_REF = "docs/developer/api-reference.md"
DOCS_CODEBASE = "docs/developer/codebase-map.md"
ROUTES_FILE = "application/route.py"
VULN_DIR = "application/vulnerabilities"

ALLOWED_UNDOCUMENTED_ROUTES = {
    "OPTIONS /",
    "OPTIONS /<var>",
    "GET /promotion-photo-claim",  # redirect → /promotion-photo
}


def extract_routes_from_ast(filepath: str) -> list[tuple[int, str, str, str]]:
    """Parse route.py AST and return [(lineno, method, path, function_name)]."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=filepath)

    routes = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            if not isinstance(dec.func, ast.Attribute):
                continue
            if dec.func.attr != "route":
                continue

            path = ""
            if dec.args:
                first = dec.args[0]
                if isinstance(first, ast.Constant):
                    path = first.value
                elif isinstance(first, ast.JoinedStr):
                    path = "".join(
                        p.value if isinstance(p, ast.Constant) else "<var>"
                        for p in first.values
                    )

            methods = ["GET"]
            for kw in dec.keywords:
                if kw.arg == "methods":
                    if isinstance(kw.value, ast.List):
                        methods = [
                            e.value
                            for e in kw.value.elts
                            if isinstance(e, ast.Constant)
                        ]

            for method in methods:
                routes.append((node.lineno, method, path, node.name))

    return routes


def extract_documented_endpoints(filepath: str) -> set[str]:
    """Parse api-reference.md for documented endpoints.

    Handles three formats:
    1. Heading: `METHOD /path`
    2. Table with method: `| METHOD /path | ...`
    3. Table implicit GET: `| /path | ...`
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    documented = set()

    # Pattern 1: `#### \`METHOD /path\``  (API route headings)
    heading_pattern = re.compile(r"^####\s+`(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s`]+)`")

    # Pattern 2: Table rows with method prefix: `| \`METHOD /path\` | ...`
    table_with_method = re.compile(r"^\|\s+`(GET|POST|PUT|DELETE|PATCH)\s+(/[^`\s]+)`")

    # Pattern 3: Table rows without method prefix: `| \`/path\` | ...`
    # These imply GET (used in Page Routes and Vulnerability Demo sections)
    table_implicit_get = re.compile(r"^\|\s+`(/[^`\s]*)`\s*\|")

    for line in lines:
        m = heading_pattern.match(line)
        if m:
            documented.add(f"{m.group(1)} {m.group(2)}")
            continue

        m = table_with_method.match(line)
        if m:
            documented.add(f"{m.group(1)} {m.group(2)}")
            continue

        m = table_implicit_get.match(line)
        if m:
            documented.add(f"GET {m.group(1)}")
            continue

    return documented


def extract_documented_modules(filepath: str) -> set[str]:
    """Parse codebase-map.md for vulnerability module filenames."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    found = set()
    pattern = re.compile(r"`([\w_]+\.py)`")
    for m in pattern.finditer(text):
        name = m.group(1)
        if name.endswith(".py") and name != "__init__.py":
            found.add(name[:-3])
    return found


def get_vulnerability_modules(directory: str) -> set[str]:
    """List all .py files in directory, excluding __init__."""
    modules = set()
    for fpath in glob.glob(os.path.join(directory, "*.py")):
        name = os.path.splitext(os.path.basename(fpath))[0]
        if name != "__init__":
            modules.add(name)
    return modules


def normalize_path(path: str) -> str:
    """Replace Flask variable segments with <var> for comparison."""
    return re.sub(r"<[^>]+>", "<var>", path)


def main():
    errors = 0

    routes = extract_routes_from_ast(ROUTES_FILE)
    documented = extract_documented_endpoints(DOCS_API_REF)

    undocumented = []
    for _, method, path, func in routes:
        key = f"{method} {path}"
        key_norm = f"{method} {normalize_path(path)}"
        key_norm_all = normalize_path(key)

        if key in documented or key_norm in documented or key_norm_all in documented:
            continue
        if key in ALLOWED_UNDOCUMENTED_ROUTES or key_norm in ALLOWED_UNDOCUMENTED_ROUTES:
            continue
        undocumented.append(key)

    if undocumented:
        print(f"\nMissing from {DOCS_API_REF}:")
        for ep in sorted(set(undocumented)):
            print(f"  {ep}")
        errors += 1
    else:
        print(f"All {len(routes)} routes documented in {DOCS_API_REF}.")

    vuln_modules = get_vulnerability_modules(VULN_DIR)
    doc_modules = extract_documented_modules(DOCS_CODEBASE)

    missing_modules = vuln_modules - doc_modules
    if missing_modules:
        print(f"\nMissing from {DOCS_CODEBASE}:")
        for m in sorted(missing_modules):
            print(f"  {m}")
        errors += 1
    else:
        print(f"All {len(vuln_modules)} vulnerability modules documented in {DOCS_CODEBASE}.")

    if errors:
        print("\nRun `make docs` and update the relevant documentation files.")
        sys.exit(1)

    print("\nDocumentation coverage OK.")
    sys.exit(0)


if __name__ == "__main__":
    main()

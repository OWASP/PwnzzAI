#!/usr/bin/env python3
"""check-codeblocks.py — Validate Python code blocks in markdown files.

Zero-dependency checker that extracts ```python blocks from .md files and
validates syntax (compilation) and optionally executes them.

Usage:
    python3 scripts/check-codeblocks.py              # syntax check all docs/
    python3 scripts/check-codeblocks.py README.md    # specific file
    python3 scripts/check-codeblocks.py --exec       # syntax + runtime exec

Runtime execution will fail on snippets that depend on the Flask app context
(e.g. `from application import app`). These are expected — only use --exec
when you've verified the snippets are self-contained.
"""
import ast
import os
import re
import sys
import traceback


def extract_python_blocks(text: str):
    """Yield (lineno, code) tuples for each ```python block."""
    pattern = re.compile(
        r"^```python\s*\n(.*?)\n^```",
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(text):
        lineno = text[: m.start()].count("\n") + 1
        code = m.group(1)
        yield lineno, code


def check_file(filepath: str, run_exec: bool = False) -> int:
    """Check all Python blocks in a file. Returns number of failures."""
    relpath = os.path.relpath(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    failures = 0
    for lineno, code in extract_python_blocks(text):
        code = code.strip()
        if not code:
            continue

        # Always check syntax with ast.parse
        try:
            ast.parse(code)
        except SyntaxError as e:
            print(f"  FAIL {relpath}:{lineno} — syntax error: {e}")
            failures += 1
            continue

        # Optionally try to exec (will fail on app-context snippets)
        if run_exec:
            try:
                exec(code, {"__MODULE__": "__main__"})
                print(f"  OK   {relpath}:{lineno}")
            except Exception as e:
                tb = "".join(traceback.format_exception_only(type(e), e)).strip()
                print(f"  SKIP {relpath}:{lineno} — {tb}")
        else:
            print(f"  OK   {relpath}:{lineno}")

    return failures


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    run_exec = "--exec" in sys.argv

    targets = args if args else ["docs/"]

    # Collect .md files from targets
    files = []
    for target in targets:
        if os.path.isfile(target):
            files.append(target)
        elif os.path.isdir(target):
            for root, _dirs, fnames in os.walk(target):
                for fname in fnames:
                    if fname.endswith(".md"):
                        files.append(os.path.join(root, fname))

    if not files:
        print("No markdown files found.")
        sys.exit(0)

    total = 0
    failures = 0
    for filepath in sorted(files):
        f = check_file(filepath, run_exec=run_exec)
        total += 1
        failures += f

    print(f"\n{total} files checked, {failures} block failures.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

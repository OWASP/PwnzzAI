# Documentation Guide

How to add and edit pages on the PwnzzAI documentation site.

The site is built with [MkDocs](https://www.mkdocs.org/) using the
[Material](https://squidfunk.github.io/mkdocs-material/) theme, and published to
GitHub Pages at [https://owasp.org/PwnzzAI/](https://owasp.org/PwnzzAI/). Everything
it serves comes from the `docs/` directory plus the `mkdocs.yml` config at the repo
root.

## Table of Contents

- [Quick version](#quick-version)
- [Layout](#layout)
- [Step 1 — Create the page](#step-1--create-the-page)
- [Step 2 — Add it to the navigation](#step-2--add-it-to-the-navigation)
- [Navigation hierarchy](#navigation-hierarchy)
  - [How each level renders in this theme](#how-each-level-renders-in-this-theme)
  - [Choosing where a page goes](#choosing-where-a-page-goes)
  - [Ordering](#ordering)
  - [Section headers aren't clickable](#section-headers-arent-clickable)
  - [Directory structure vs. nav structure](#directory-structure-vs-nav-structure)
- [Step 3 — Preview locally](#step-3--preview-locally)
- [Step 4 — Commit and deploy](#step-4--commit-and-deploy)
- [Writing pages](#writing-pages)
  - [Images](#images)
  - [Internal links and anchors](#internal-links-and-anchors)
  - [Available markdown features](#available-markdown-features)
- [Lab page template](#lab-page-template)
- [Conventions](#conventions)
- [Pre-submit checklist](#pre-submit-checklist)
- [Troubleshooting](#troubleshooting)

## Quick version

```bash
# 1. write the page
$EDITOR docs/my-new-page.md

# 2. add it to nav: in mkdocs.yml
#      - My New Page: my-new-page.md

# 3. preview
pip install mkdocs mkdocs-material
mkdocs serve                      # http://127.0.0.1:8000

# 4. ship
git add docs/my-new-page.md mkdocs.yml
git commit -m "docs: add my new page"
git push
```

Pushing to `main` triggers the GitHub Pages deploy automatically. No manual build
step, and no committing the `site/` directory.

## Layout

```
mkdocs.yml                    # site config + navigation tree
docs/
├── index.md                  # site home page
├── installation.md
├── dev-guide.md
├── labs.md                   # the lab manual
├── misinformation.md         # per-lab deep dive
├── workshop-cloud-llm-setup.md
├── CHALLENGE_SOLUTIONS.md    # answer key (intentionally not in nav)
├── rfc-ex-b-direct-prompt-injection.md
└── assets/
    └── images/
        ├── logo.png
        ├── favicon.png
        └── labs/             # lab screenshots (image1.png … image18.png)
```

Two rules follow from this:

- **Only files under `docs/` are published.** A markdown file elsewhere in the repo (like this one) is not part of the site.
- **Paths in `mkdocs.yml` are relative to `docs/`**, not to the repo root. It's `labs.md`, never `docs/labs.md`.

## Step 1 — Create the page

Add a `.md` file under `docs/`. Filename becomes the URL, so use lowercase
kebab-case:

| File | URL |
| :---- | :---- |
| `docs/troubleshooting.md` | `/troubleshooting/` |
| `docs/labs/sql-injection.md` | `/labs/sql-injection/` |
| `docs/My Page.md` | avoid — spaces and capitals make ugly, fragile URLs |

Start the file with a single `#` H1 — that becomes the page title in the browser tab
and the top of the sidebar's table of contents. Use `##` for sections below it; don't
use a second `#`.

```markdown
# Page Title

Intro paragraph.

## First Section
```

Subdirectories are fine and are the right call once a topic has several pages — they
group the URLs as well as the files.

## Step 2 — Add it to the navigation

Edit the `nav:` block at the bottom of `mkdocs.yml`. Left of the colon is the label
shown in the UI; right of it is the path relative to `docs/`:

```yaml
nav:
  - Home: index.md
  - Installation: installation.md
  - Dev Guide: dev-guide.md
  - Labs:
      - Lab Manual: labs.md
      - Misinformation: misinformation.md
  - Troubleshooting: troubleshooting.md
```

!!! note "Files not listed in nav still get published"
    MkDocs builds every `.md` file under `docs/` whether or not it appears in `nav:`.
    An omitted page has no sidebar entry but is still reachable by URL and still
    turns up in site search. That's deliberate for `CHALLENGE_SOLUTIONS.md` — it's
    the answer key, kept out of the menu. If you're adding a page you want people to
    find, it must be in `nav:`.

## Navigation hierarchy

Indentation in `nav:` is the whole hierarchy — there is no other mechanism. A `key:
value` pair is a **page**; a key whose value is a *list* is a **section**:

```yaml
nav:
  - Installation: installation.md      # page
  - Labs:                              # section (value is a list)
      - Lab Manual: labs.md
      - Misinformation: misinformation.md
```

### How each level renders in this theme

The rendering depends on which Material features are switched on, and this site
enables `navigation.tabs`, `navigation.sections`, and `navigation.expand`
(`mkdocs.yml:23-25`). With that combination:

| Nesting level | Renders as |
| :---- | :---- |
| Level 1 (top-level) | A **tab** in the header bar — whether it's a page or a section |
| Level 2 | A **section group** in the left sidebar: a bold, non-clickable header with its pages beneath |
| Level 3+ | Pages / nested groups inside that group, expanded by default rather than collapsed |

So the current config produces four tabs — Home, Installation, Dev Guide, Labs — and
clicking **Labs** shows a sidebar containing Lab Manual and Misinformation.

```
Header tabs:   Home   Installation   Dev Guide   [Labs]
                                                   │
Sidebar (Labs tab):                                ▼
                                            Lab Manual
                                            Misinformation
```

Because `navigation.expand` is on, sub-sections don't collapse — everything in the
active tab is visible at once. That's fine at the current size, but it means a deep
tree produces a very long sidebar; keep it in mind before nesting four levels of labs.

### Choosing where a page goes

- **New top-level tab** — only for a genuinely new top-level topic. Tabs are horizontal and finite; past six or seven they wrap and stop being scannable.
- **Nested under an existing section** — the default choice. A new per-lab deep dive goes under `Labs`, not next to it:

```yaml
  - Labs:
      - Lab Manual: labs.md
      - Misinformation: misinformation.md
      - Excessive Agency: excessive-agency.md      # new
```

- **A section inside a section** — reach for this when one grouping genuinely has sub-groupings:

```yaml
  - Labs:
      - Lab Manual: labs.md
      - Prompt Injection:
          - Direct: labs/direct-prompt-injection.md
          - Indirect: labs/indirect-prompt-injection.md
          - Guardrail Ladder: labs/guardrail-ladder.md
      - Data Attacks:
          - Data Poisoning: labs/data-poisoning.md
          - RAG Poisoning: labs/rag-poisoning.md
      - Misinformation: misinformation.md
```

That's three levels, which is about the practical ceiling here — deeper works in
MkDocs but reads badly under `navigation.expand`.

### Ordering

`nav:` order is literal and manual — top to bottom, exactly as written. MkDocs never
sorts alphabetically or by date, and filenames have no influence. Order pages the way
a reader progresses: install → concepts → labs → reference.

Omitting `nav:` entirely would make MkDocs auto-build the tree alphabetically from
the filesystem, which is why this repo declares it explicitly.

### Section headers aren't clickable

A section is a label, not a destination. `Labs:` has no page of its own, which is why
`labs.md` sits *inside* the section as "Lab Manual" rather than being the section
itself. Clicking the section header in the sidebar does nothing.

Making a section's landing page clickable requires the `navigation.indexes` feature,
which this site does **not** currently enable:

```yaml
# mkdocs.yml — would need this under theme.features
  - navigation.indexes
```

```yaml
# then the first child becomes the section's own page
  - Labs:
      - labs.md                        # ← no label: this IS the Labs page
      - Misinformation: misinformation.md
```

Enabling it is a site-wide change affecting every section, so raise it in a PR of its
own rather than as a side effect of adding a page.

### Directory structure vs. nav structure

These are **independent**. A file can live at `docs/misinformation.md` and appear
nested under `Labs` in the menu; nothing forces the two to agree.

But nav nesting doesn't change URLs — only directories do. `docs/misinformation.md`
stays at `/misinformation/` no matter how deeply you nest its menu entry. So once a
section has more than two or three pages, move the files into a matching
subdirectory:

```
docs/labs/direct-prompt-injection.md   →  /labs/direct-prompt-injection/
```

The URL then reflects the hierarchy the reader sees, and related files sit together.
Remember to update the `nav:` paths and any inbound links when you move a file.

## Step 3 — Preview locally

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Then open <http://127.0.0.1:8000>. The dev server live-reloads on save, so keep it
running while you write.

Note that `mkdocs` is **not** in `requirements.txt` — it isn't needed to run the app,
so install it separately (a virtualenv or `pipx` is fine). CI installs it the same
way.

Two commands worth knowing:

```bash
mkdocs build            # render to ./site/ — same as CI does
mkdocs build --strict   # turn warnings (broken links, orphan pages) into errors
```

Run `--strict` before opening a PR — it's the fastest way to catch a typo'd internal
link. Separately, watch the build log for the `INFO` line listing pages that exist
but aren't in `nav:`; that one is informational and `--strict` won't fail on it.

## Step 4 — Commit and deploy

`.github/workflows/docs.yml` handles publishing:

| Event | What happens |
| :---- | :---- |
| PR touching `docs/**` or `mkdocs.yml` | Builds the site — a build failure fails the check |
| Push to `main` | Builds **and** deploys to GitHub Pages |
| Push to `feature/**` | Builds only; no deploy |

The workflow only fires on changes to `docs/**`, `mkdocs.yml`, or the workflow file
itself. A docs change outside those paths won't trigger a rebuild.

Do not commit the `site/` directory — it's generated output, built fresh by CI on
every deploy.

## Writing pages

### Images

Put images under `docs/assets/images/`, using the `labs/` subfolder for lab
screenshots. Reference them with a path relative to `docs/`:

```markdown
![Misinformation lab](assets/images/labs/image15.png)

*Figure 1 — description of what the screenshot shows*
```

The italic caption line under the image is the existing convention in `labs.md`;
follow it so figures read consistently. Prefer PNG for screenshots, and crop to the
relevant part of the UI rather than pasting a full desktop.

### Internal links and anchors

Link to other pages by their **`.md` filename**, not their URL. MkDocs rewrites the
extension at build time and — importantly — warns you if the target doesn't exist:

```markdown
[Installation guide](installation.md)              ← correct
[Installation guide](/installation/)               ← works, but silently breaks on rename
```

Section anchors are auto-generated from headings (lowercased, spaces to hyphens):

```markdown
See [RAG Poisoning](labs.md#rag-poisoning) for the setup.
```

Because `attr_list` is enabled, you can also pin a stable anchor to a heading so it
survives the heading text being reworded — `labs.md` uses this:

```markdown
## Model Theft Attack {#model-theft-attack}
```

### Available markdown features

These extensions are configured in `mkdocs.yml`, so you can use them without any
further setup:

**Admonitions** (`admonition`, `pymdownx.details`) — call-out boxes. Types include
`note`, `tip`, `warning`, `danger`, `info`, `example`:

```markdown
!!! warning "Run this in an isolated environment"
    PwnzzAI is intentionally vulnerable.

??? note "Collapsed by default"
    Use `???` instead of `!!!` for a collapsible block.
```

**Code blocks** with copy buttons and line numbers (`pymdownx.highlight`,
`content.code.copy`):

````markdown
```python title="application/route.py" hl_lines="2"
def misinformation():
    return render_template('misinformation.html')
```
````

**Tabbed content** (`pymdownx.tabbed`) — good for local-vs-cloud or
Docker-vs-manual instructions:

```markdown
=== "Ollama (local)"
    Run `make dev`.

=== "Cloud model"
    Save an API key first.
```

**Tables** (`tables`) — standard GitHub-flavoured pipe tables.

**Anchor permalinks** (`toc` with `permalink: true`) — every heading gets a `¶`
link, so readers can deep-link a section.

Also available: `pymdownx.superfences` (nested/complex fences), `pymdownx.inlinehilite`
(`` `#!python code` ``), `pymdownx.snippets` (include external files), and
`md_in_html` (markdown inside HTML blocks).

## Lab page template

`docs/misinformation.md` is the reference for a per-lab deep dive. The structure that
page follows, and that new lab pages should reuse:

```markdown
# Lab Name

**Lab N** — [LLMxx:2025 Category](https://genai.owasp.org/llmrisk/...)

[http://localhost:8080/route](http://localhost:8080/route)

| | |
| :---- | :---- |
| **Objective** | What the attacker is trying to achieve |
| **Threat Model** | STRIDE-style framing |
| **Difficulty Rating** | Beginner / Intermediate / Advanced |
| **OWASP Category** | LLMxx:2025 ... |
| **Backends** | Local (Ollama) and/or cloud |

![Screenshot](assets/images/labs/imageN.png)

## What the vulnerability is      ← concept, provider-neutral
## How this lab is built          ← pipeline + the specific design flaws, with file:line refs
## Walkthrough                    ← numbered, reproducible steps
## Detection                      ← signals you could assert on in a test
## Mitigations                    ← ordered by impact
## API reference                  ← routes, request/response shapes, status codes
## Source map                     ← file → role table
## Related labs                   ← cross-links
```

For a short entry that only needs the summary block, add it to `docs/labs.md`
instead of creating a new file — the lab manual is the index, and per-page deep dives
are for labs that need the extra depth.

## Conventions

- **Filenames**: lowercase kebab-case (`workshop-cloud-llm-setup.md`). The uppercase exceptions in `docs/` (`CHALLENGE_SOLUTIONS.md`) are legacy; don't add new ones.
- **One H1 per page**, at the top.
- **Code references** use `file.py:line` (`application/route.py:1253`) so they're greppable and clickable in editors.
- **Ports and URLs**: the app runs on `localhost:8080` throughout the docs — keep it consistent.
- **OWASP links** point at the 2025 Top 10 for LLM Applications entries; match the format used in `labs.md`.
- **Don't publish the answer key.** New solution content belongs in `docs/CHALLENGE_SOLUTIONS.md`, which stays out of `nav:`.
- **Security framing**: PwnzzAI is deliberately vulnerable. Pages describing an exploit should also cover the mitigation — that pairing is the teaching point.

## Pre-submit checklist

- [ ] File is under `docs/` with a lowercase kebab-case name
- [ ] Single `#` H1 at the top
- [ ] Added to `nav:` in `mkdocs.yml` (or deliberately omitted, and you know why)
- [ ] `mkdocs build --strict` passes with no warnings
- [ ] Internal links use `.md` filenames and resolve
- [ ] Images render, live under `docs/assets/images/`, and have captions
- [ ] Checked in both light and dark mode (the theme has a toggle)
- [ ] `site/` is not staged

## Troubleshooting

**Page doesn't appear in the menu** — it's missing from `nav:`, or the path is wrong.
Paths are relative to `docs/`: `my-page.md`, not `docs/my-page.md`.

**`INFO - The following pages exist in the docs directory, but are not included in the "nav" configuration`**
— exactly the above. It's informational rather than an error, and `--strict` won't
fail the build over it, so read the log rather than relying on the exit code.

**Broken image** — check the path is relative to `docs/` and the case matches. Linux
CI is case-sensitive even when macOS and Windows let it slide locally, so
`Image15.PNG` will build fine on your machine and 404 in production.

**Link works locally, 404s on the deployed site** — you used an absolute path like
`/installation/`. The site is served from a subpath (`/PwnzzAI/`), so absolute paths
break. Use relative `.md` links.

**Anchor link doesn't jump** — anchors are derived from heading text; if the heading
changed, the anchor did too. Pin it with `{#stable-anchor}`.

**Changes not live after pushing** — confirm the push landed on `main` (deploy is
gated on it) and that the change touched `docs/**` or `mkdocs.yml`. Check the
**Deploy MkDocs to GitHub Pages** run in the Actions tab.

**`mkdocs: command not found`** — `pip install mkdocs mkdocs-material`. It's not in
`requirements.txt` by design.

**Admonition renders as plain text** — the content must be indented four spaces
under the `!!!` line, and there must be a blank line after it.

---

Related: [CONTRIBUTING.md](CONTRIBUTING.md) for the general contribution workflow,
and [docs/dev-guide.md](docs/dev-guide.md) for working on the application itself.

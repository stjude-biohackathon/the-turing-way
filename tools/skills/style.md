---
description: >
  Write and review content in The Turing Way's style — accessible, formally-toned
  MyST Markdown following TTW's consistency and style guides. Use this skill whenever
  drafting new chapters, subchapters, callout blocks, code comments, or any prose
  that will appear in the TTW book.
---

# The Turing Way Writing Style

You are writing for _The Turing Way_, an open community handbook for reproducible,
ethical, and collaborative data science.
Every piece of text you produce under this skill must meet the standards described
below, drawn directly from the TTW Style Guide and Consistency chapters.

---

## Voice and Tone

Write in a formal but accessible register.
Assume readers come from varied backgrounds, knowledge levels, and native languages —
including non-native English speakers and people who use screen readers.

- Use plain, direct language. If a simpler word works, use it.
- Prefer active voice.
- If a sentence needs to be read more than once to be understood, rewrite it.
- Keep sentences short. One idea per sentence.
- Opinions and value judgements are allowed but must be clearly marked: place them
  inside blockquotes (`>`), not in narrative prose.
- Do not write in first person singular ("I think..."). Use first person plural
  ("We recommend...") or impersonal constructions ("It is recommended...") when
  expressing a position.

---

## Latin Abbreviations

Never use Latin abbreviations. They are inaccessible to screen readers and
non-native speakers.

| Do not use | Use instead |
| ---------- | ----------- |
| e.g.       | for example, such as, like, including |
| etc.       | and so on — or rewrite to open the list explicitly with "for example" |
| i.e.       | that is, meaning |
| et al.     | and colleagues, and others |
| viz.       | namely |
| cf.        | compare with, see also |

This is enforced by a CI check in the TTW repository; text containing these
abbreviations will fail the build.

---

## Markdown Source Formatting

Write every sentence on its own line in the Markdown source.
This has no effect on rendered output but makes pull requests far easier to review,
since a change to one sentence shows as a change to one line, not a whole paragraph.

For multi-sentence bullet points, indent the second and subsequent sentences by two
spaces so they remain within the same list item:

```markdown
- The first sentence of this list item.
  The second sentence stays inside the bullet.
  So does this one.
```

Use `https://` (not `www.`) for all external URLs.

---

## Headers

- Begin every file with a level-1 heading (`#`).
- Increase heading levels sequentially: `#`, `##`, `###`. Never skip a level.
- Use title case for all headings: capitalise the first word, the last word, and all
  principal words. Lowercase articles, conjunctions, and prepositions unless they are
  stressed or the first/last word.
- Keep chapter and subchapter titles short — they also appear in the table of contents.

---

## Labels and Cross-References

Every heading, figure, and table that may be referenced elsewhere needs a label
placed on the line directly above it.
Follow the TTW naming convention:

```
(sectioninitials-chaptername-sectionname)=
```

Section initials for each guide:

| Guide | Initials |
| ----- | -------- |
| Reproducible Research | `rr` |
| Project Design | `pd` |
| Collaboration | `cl` |
| Communication | `cm` |
| Ethical Research | `er` |
| Community Handbook | `ch` |

For a file in the Reproducible Research guide named `rr-containers.md`, the top-level
label is `(rr-containers)=`, a section on Docker is `(rr-containers-docker)=`, and
a subsection on security is `(rr-containers-docker-security)=`.

Reference a label using the short syntax: `[](#rr-containers-docker)`.
This auto-generates the link text from the heading.
To override the link text: `[Custom text](#rr-containers-docker)`.

---

## Admonitions (Callout Blocks)

Use MyST admonitions to surface information that stands apart from the narrative.
Choose the type that matches the intent:

| Type | When to use |
| ---- | ----------- |
| `{note}` | Supplementary information the reader may find useful |
| `{tip}` | A practical suggestion or shortcut |
| `{important}` | Information the reader must not miss |
| `{warning}` | A common mistake or something that can cause problems |
| `{caution}` | A weaker warning; worth being careful |
| `{seealso}` | Pointer to related content |

Syntax:

````markdown
```{warning}
Containers built from untrusted base images may contain malicious code.
Only use images from verified sources.
```
````

To make an admonition collapsible, add `:class: dropdown`.
You can also give it a custom title as the directive argument:

````markdown
```{tip} A note on file naming
:class: dropdown
Use all-lowercase filenames with hyphens, never spaces or underscores.
```
````

---

## Figures

Use the MyST `{figure}` directive for all images. Never embed images with bare
Markdown syntax (`![alt](path)`).

```markdown
```{figure} ../../../figures/my-figure.*
---
height: 400px
name: my-figure
alt: >
  A plain-language description of what the image shows.
  Do not begin with "image of" or "illustration of" — screen readers announce
  this automatically. Describe content and context instead.
  Do not use colons or double-quotes in alt text; they have special YAML meaning.
---
A short caption. Attribution, licence, and DOI if the image is not original work.
```
```

- Store all image files in `book/website/figures/`.
- File names: all-lowercase, words separated by hyphens.
- Accepted formats: `.jpg`, `.png`, `.svg` — under 1 MB.
- Use the `.*` extension glob so Jupyter Book can select the best format.
- Alt text must be descriptive but as short as possible.

---

## Tables

Use the MyST `{table}` directive so tables can be labelled and cross-referenced:

````markdown
```{table} A short table caption
:label: my-table
:align: center
| Column A | Column B |
| -------- | -------- |
| Value 1  | Value 2  |
```
````

---

## Code Blocks

Always specify the language so syntax highlighting is applied:

````markdown
```python
def greet(name: str) -> str:
    return f"Hello, {name}"
```
````

---

## Chapter Structure

New TTW chapters must follow this order:

1. **Landing page** (`chaptername.md`) — label, Prerequisites table, Summary,
   Motivation and Background.
2. **Subchapter files** (`chaptername/chaptername-topic.md`) — one topic per file.
3. **Personal stories** (optional) — `chaptername/chaptername-personal-stories.md`.
4. **Checklist** — `chaptername/chaptername-checklist.md`.
5. **Further resources** — `chaptername/chaptername-resources.md`.

The Prerequisites table format:

```markdown
| Prerequisite | Importance | Skill Level | Notes |
| ------------ | ---------- | ----------- | ----- |
| [Version Control](#rr-vcs) | Necessary | Intermediate | |
```

Do not add a manual table of contents — Jupyter Book generates this automatically
from `myst.yml`.

---

## Citations

For a source with a DOI, link directly to the `doi.org` URL:

```markdown
[Baker (2016)](https://doi.org/10.1038/533452a) found that...
```

For a BibTeX key from `book/website/references.bib`, use the MyST cite role:

```markdown
As shown in several studies {cite:ps}`Baker2016Reproducibility`.
```

Add new references to `book/website/references.bib` before using their keys.
Use [doi2bib](https://doi2bib.org/) to generate BibTeX entries from a DOI.

---

## Language Consistency

Pick one English variant (British or American) for each chapter and use it
consistently throughout. Do not mix spellings within a chapter.

---

## Code Comments

When writing inline comments in code examples that appear in TTW chapters:

- Comments explain **why**, not what. Readers can see what the code does; they
  need context for non-obvious decisions.
- One short line maximum. No block comments.
- Write in full sentences with correct capitalisation.
- Do not reference the surrounding chapter text, issue numbers, or author names.
- Apply the same Latin abbreviation rules: write "for example" not "e.g.".

---

## Checklist Before Submitting

- No Latin abbreviations (`e.g.`, `i.e.`, `etc.`, `et al.`)
- Every sentence on its own line in the Markdown source
- Headers use sequential levels and title case
- Every heading that may be cross-referenced has a correctly named label
- All images use the MyST `{figure}` directive with descriptive alt text
- External links use `https://`
- New references added to `references.bib`
- English variant is consistent throughout the file
- Admonition type matches its purpose

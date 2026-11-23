---
name: validate
description: Validate QuickView code and documentation — lint/format (ruff, prettier), spelling (codespell), version consistency, conventional commits, app smoke test, VitePress docs build, and doc↔code drift (shortcuts, CLI flags, UI labels, dev docs). Use before committing or opening a PR, or when the user asks to check, validate, or verify changes or docs. Accepts an optional scope argument (`all`, `docs`, `code`, or a git ref).
---

# Validate QuickView code and docs

Two phases. Phase 1 is mechanical and scripted, and Phase 2 needs judgment.
Report both in a single summary at the end.

## Scope

Parse the argument the user passed:

| Argument            | Meaning                                                                       |
| ------------------- | ----------------------------------------------------------------------------- |
| _(none)_            | Changes vs `origin/master` merge-base, plus uncommitted and untracked files   |
| `all`               | Whole repository (`--all`)                                                    |
| `docs` / `code`     | Default scope, but only run the doc-related or code-related checks in Phase 2 |
| a git ref (`HEAD~3`) | Changes since that ref (`--base <ref>`)                                      |

## Phase 1: deterministic checks

Run from the repo root:

```bash
python3 .claude/skills/validate/scripts/check.py [--all | --base <ref>]
```

**Before you run it**: pre-commit has no dry-run mode, so hooks always write
their fixes. If the working tree has uncommitted changes, tell the user that
formatter fixes will be mixed into their changes. With `all`, the repo isn't
pre-commit-clean today (a full run touches about 65 files: prettier on JSON,
JS, and CSS, plus whitespace fixes in the docs). So **ask before using `--all`**,
and suggest doing that cleanup as its own `style:` commit.

The script runs pre-commit with **auto-fix enabled for every hook except
codespell** (ruff, ruff-format, prettier, trailing-whitespace,
end-of-file-fixer). It also checks the version in the 4 semantic-release files,
JSON validity, conventional commit subjects, `python -m e3sm_quickview.app
--help`, and `npm run build` for the docs. The build runs whenever `docs/` changed (or
with `all`), and the script runs `npm ci` first if `node_modules` is missing.
A failure here usually means a dead internal link or a broken Vue/Markdown
page: report the file and the link.

After it runs:

- **FIXED**: list the files that were auto-fixed. Don't revert them.
- **FAIL in pre-commit after the fixes**: these are issues ruff can't fix, such
  as unused variables or bare excepts. Fix them by hand when the fix is obvious
  and keeps the behavior the same. Otherwise report them.
- **SKIPPED**: say why, and tell the user how to enable the check (for
  example, `npm ci`).

### codespell: never fix blindly

The script reports codespell hits **without fixing them**. Each hit is tagged
`[binary]`, `[generated/vendored]`, or `[source]`. Group the hits by file and
decide what to do for each group:

1. **`[binary]` or `[generated/vendored]` file**: the file most likely
   shouldn't be spell-checked. Recommend adding it to `skip =` in
   `.codespellrc`.
2. **`[source]` file, where the word is a real typo** in prose, comments,
   strings, or identifiers that aren't part of a public API: recommend
   fixing the spelling.
3. **`[source]` file, where the word is intentional**: domain terms such as
   `SCRIP`/`hist`, variable names that come from data files, quoted external
   text, or identifiers that external code depends on (state JSON keys, CLI
   flags, public API names). Recommend adding the word to `ignore-words-list`
   in `.codespellrc`, or an `ignore-regex` for a narrow pattern.

**Always ask the user before applying any codespell resolution.** Use
`AskUserQuestion` with one question per file (up to 4 per call, batching the
rest). In each question, show the line(s) and the suggested replacement. The
options are:

- "Fix spelling" (put `(Recommended)` on whichever option you recommend)
- "Skip this file in .codespellrc"
- "Ignore this word in .codespellrc"

Apply the chosen resolution, then rerun only the codespell check:

```bash
python3 .claude/skills/validate/scripts/check.py --skip precommit,versions,json,commits,smoke,docs [scope flags]
```

Note: `.codespellrc` is the only codespell config that's read. Words that are
only listed in `.codespell-ignore` are **not** ignored. If you add an ignored
word, put it in `.codespellrc`, and point out the mismatch if
`.codespell-ignore` still exists.

## Phase 2: judgment checks

**Out of scope:** `docs/guides/quickcompare/**`, `docs/guides/siteview/**`,
and the sibling repositories. Their own validation skill handles them. See the
"Out of scope" section of the map for details.

Read `references/doc-code-map.md`. For each changed file (or every row, with
`all`), open the code and its mapped docs, then compare them using the "What
to compare" column. Concretely:

- **Shortcuts**: extract every `mt.bind(...)` in `app.py`. Diff that list
  against `shortcuts.md`, the `keys=` hints in `components/doc.py`, and the
  `keybinding=` hints in `components/tools.py`.
- **CLI**: compare the argparse options against the flags used in the docs
  and the launcher scripts.
- **New user-visible features** (`feat:` commits, new UI controls or options):
  check that a guide mentions them. If none does, propose where the
  documentation should go (which page and which section). Don't write long
  prose without asking.
- **Dev docs**: `docs/guides/dev/ci.md` should match `.github/workflows/`, and
  `what_is_where.md` should match the actual paths and symbols.
- **Config drift**: paths in `.pre-commit-config.yaml` `exclude`,
  `[tool.hatch.build] include`, `.gitattributes`, and `.codespellrc` should
  point to files that exist (the repo moved to a `src/` layout).
- **Docs quality** (for changed `.md` files): headings and links make sense,
  relative links resolve, images or state JSON files referenced from the page
  exist, and the terminology stays consistent with the UI labels.

For Phase 2 findings, **report them and propose a fix, but don't edit until
the user agrees**. The one exception is an unambiguous factual correction,
such as a wrong key letter or a wrong file path. You can fix those directly
and list them as fixed.

## Report format

End with:

```
## Validation report: <scope>

Auto-fixed: <files, or "none">
Blocking:   <file:line: problem>   (fails CI or pre-commit, broken docs build, wrong docs)
Should fix: <file:line: problem>   (doc drift, missing docs for a feature, config drift)
Nits:       <file:line: problem>
Skipped:    <check: reason>
```

If the map in `references/doc-code-map.md` was missing a relationship you
had to discover, suggest adding it.

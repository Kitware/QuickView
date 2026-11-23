#!/usr/bin/env python3
"""Deterministic validation checks for QuickView.

Usage: python3 check.py [--all | --base <ref>] [--skip <name>,...]

- Auto-fixing pre-commit hooks (ruff, ruff-format, prettier, whitespace/EOF)
  always write their fixes (pre-commit has no dry-run mode).
- codespell is run REPORT-ONLY: every hit is listed with a file classification
  so the caller (Claude) can ask the user whether to fix the word or ignore the file.
- Each section prints a header "## <name>: PASS|FAIL|FIXED|SKIPPED".
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    ).stdout.strip()
)
os.chdir(ROOT)

CODESPELL_VERSION = "2.3.0"  # keep in sync with .pre-commit-config.yaml
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns", ".mp4", ".nc", ".vtk",
    ".vtp", ".pdf", ".zip", ".gz", ".exe",
}  # fmt: skip
GENERATED_HINTS = (
    "package-lock.json", "CHANGELOG.md", "/presets/", "/sidecar/",
    "node_modules/", "/dist/", "/.vitepress/cache/", "/serve/html2canvas.js",
)  # fmt: skip
VERSION_FILES = {
    "pyproject.toml": r'^version\s*=\s*"([^"]+)"',
    "src-tauri/Cargo.toml": r'^version\s*=\s*"([^"]+)"',
    "src/e3sm_quickview/__init__.py": r'^__version__\s*=\s*"([^"]+)"',
    "src-tauri/tauri.conf.json": r'"version"\s*:\s*"([^"]+)"',
}
CC_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([\w\-./ ]+\))?!?: \S"
)
RELEASE_RE = re.compile(r"^\d+\.\d+\.\d+")  # semantic-release version commits

results = []


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def section(name, status, body=""):
    results.append((name, status))
    print(f"\n## {name}: {status}")
    if body.strip():
        print(body.rstrip())


def tool(name, version=None):
    if shutil.which(name):
        return [name]
    if shutil.which("uvx"):
        return ["uvx", f"{name}=={version}" if version else name]
    return None


def changed_files(args):
    if args.all:
        return None, "all tracked files"
    base = args.base
    if not base:
        mb = run(["git", "merge-base", "HEAD", "origin/master"]).stdout.strip()
        head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
        base = mb if mb and mb != head else "HEAD"
    files = set(run(["git", "diff", "--name-only", base]).stdout.split())
    files |= set(
        run(["git", "ls-files", "--others", "--exclude-standard"]).stdout.split()
    )
    files = sorted(f for f in files if Path(f).is_file())
    return files, f"changes since {base}"


def commit_range(args):
    if args.all:
        return None
    if args.base:
        return f"{args.base}..HEAD"
    mb = run(["git", "merge-base", "HEAD", "origin/master"]).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    return f"{mb}..HEAD" if mb and mb != head else None


def classify(path):
    p = "/" + path
    if Path(path).suffix.lower() in BINARY_EXT:
        return "binary"
    attr = run(["git", "check-attr", "filter", "binary", "--", path]).stdout
    if "lfs" in attr or "binary: set" in attr:
        return "binary"
    if any(h in p for h in GENERATED_HINTS):
        return "generated/vendored"
    try:
        Path(path).read_bytes()[:4096].decode("utf-8")
    except UnicodeDecodeError:
        return "binary"
    return "source"


# ---------------------------------------------------------------------------


def snapshot(paths):
    """Content hash per file, so fixes to already-modified files are detected."""
    out = {}
    for f in paths:
        try:
            out[f] = hashlib.sha1(Path(f).read_bytes()).hexdigest()
        except OSError:
            out[f] = None
    return out


def check_precommit(files):
    """Run all pre-commit hooks except codespell. Hooks write fixes in place."""
    pc = tool("pre-commit")
    if not pc:
        return section("pre-commit", "SKIPPED", "pre-commit / uvx not available")
    if files == []:
        return section("pre-commit", "PASS", "no changed files")
    name = "pre-commit (codespell excluded)"
    env = dict(os.environ, SKIP="codespell")
    cmd = pc + ["run"] + (["--all-files"] if files is None else ["--files", *files])
    candidates = files if files is not None else run(["git", "ls-files"]).stdout.split()
    before = snapshot(candidates)
    r = run(cmd, env=env)
    if r.returncode == 0:
        return section(name, "PASS")
    after = snapshot(candidates)
    touched = sorted(f for f in candidates if before.get(f) != after.get(f))
    r2 = run(cmd, env=env)  # second pass: anything left is not auto-fixable
    body = ""
    if touched:
        body = "Files auto-fixed:\n" + "\n".join(f"  {t}" for t in touched)
    if r2.returncode == 0:
        return section(name, "FIXED", body)
    remaining = [
        ln for ln in (r2.stdout + r2.stderr).splitlines()
        if ln.strip() and not ln.endswith("Passed") and "Skipped" not in ln
    ]  # fmt: skip
    body += "\nRemaining issues (not auto-fixable):\n" + "\n".join(remaining[-80:])
    section(name, "FAIL", body)


def check_codespell(files):
    cs = tool("codespell", CODESPELL_VERSION)
    if not cs:
        return section("codespell", "SKIPPED", "codespell / uvx not available")
    if files == []:
        return section("codespell", "PASS", "no changed files")
    if files is None:
        # Only git-tracked files, like pre-commit; never walk node_modules/,
        # docs/.vitepress/dist/ or other untracked build output.
        files = run(["git", "ls-files"]).stdout.split()
    r = run(cs + files)
    hits = [ln for ln in r.stdout.splitlines() if "==>" in ln]
    if not hits:
        return section("codespell", "PASS")
    rows = []
    for h in hits:
        path = h.split(":", 1)[0].removeprefix("./")
        rows.append(f"  [{classify(path)}] {h.removeprefix('./')}")
    section(
        "codespell",
        "FAIL",
        "Report-only (NOT auto-fixed). Format: [file-class] file:line: typo ==> fix\n"
        + "\n".join(rows),
    )


def check_versions():
    found = {}
    for f, pat in VERSION_FILES.items():
        m = re.search(pat, Path(f).read_text(), re.M) if Path(f).exists() else None
        found[f] = m.group(1) if m else "<not found>"
    body = "\n".join(f"  {v:12} {f}" for f, v in found.items())
    section(
        "version consistency", "PASS" if len(set(found.values())) == 1 else "FAIL", body
    )


def check_json(files):
    targets = [
        f
        for f in (
            files if files is not None else run(["git", "ls-files"]).stdout.split()
        )
        if f.endswith(".json") and Path(f).is_file()
    ]
    bad = []
    for f in targets:
        try:
            json.loads(Path(f).read_text())
        except Exception as e:  # noqa: BLE001
            bad.append(f"  {f}: {e}")
    section("JSON files parse", "FAIL" if bad else "PASS", "\n".join(bad))


def check_commits(args):
    rng = commit_range(args)
    if not rng:
        return section("conventional commits", "SKIPPED", "no commits ahead of master")
    subjects = run(["git", "log", "--format=%h %s", rng]).stdout.splitlines()
    bad = [
        s for s in subjects
        if not CC_RE.match(s.split(" ", 1)[1]) and not RELEASE_RE.match(s.split(" ", 1)[1])
    ]  # fmt: skip
    section(
        "conventional commits",
        "FAIL" if bad else "PASS",
        "\n".join(f"  {b}" for b in bad),
    )


def check_smoke():
    py = None
    if run([sys.executable, "-c", "import e3sm_quickview"]).returncode == 0:
        py = [sys.executable]
    elif shutil.which("conda") and "quickview" in run(["conda", "env", "list"]).stdout:
        py = ["conda", "run", "-n", "quickview", "python"]
    if not py:
        return section("app --help smoke test", "SKIPPED", "no env with e3sm_quickview")
    r = run(py + ["-m", "e3sm_quickview.app", "--help"])
    section(
        "app --help smoke test",
        "PASS" if r.returncode == 0 else "FAIL",
        "" if r.returncode == 0 else (r.stdout + r.stderr)[-3000:],
    )


def check_docs_build(files):
    if files is not None and not any(f.startswith("docs/") for f in files):
        return section("docs build", "SKIPPED", "no docs/ changes")
    if not Path("node_modules/.bin/vitepress").exists():
        if not shutil.which("npm"):
            return section("docs build", "SKIPPED", "npm not available")
        print("\n# installing docs dependencies (npm ci)...", flush=True)
        r = run(["npm", "ci", "--no-audit", "--no-fund"])
        if r.returncode != 0:
            return section(
                "docs build", "FAIL", "npm ci failed:\n" + (r.stdout + r.stderr)[-3000:]
            )
    r = run(["npm", "run", "build"])
    out = r.stdout + r.stderr
    dead = [
        ln
        for ln in out.splitlines()
        if "dead link" in ln.lower() or "error" in ln.lower()
    ]
    section(
        "docs build (vitepress, dead links)",
        "PASS" if r.returncode == 0 else "FAIL",
        "" if r.returncode == 0 else "\n".join(dead[-60:]) or out[-3000:],
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="check the whole repo")
    ap.add_argument("--base", help="git ref to diff against")
    ap.add_argument("--skip", default="", help="comma list: precommit,codespell,"
                    "versions,json,commits,smoke,docs")  # fmt: skip
    args = ap.parse_args()
    skip = set(filter(None, args.skip.split(",")))

    files, scope = changed_files(args)
    print(f"# QuickView validation — scope: {scope}")
    if files is not None:
        print(f"# {len(files)} file(s):")
        for f in files:
            print(f"#   {f}")

    if "precommit" not in skip:
        check_precommit(files)
    if "codespell" not in skip:
        check_codespell(files)
    if "versions" not in skip:
        check_versions()
    if "json" not in skip:
        check_json(files)
    if "commits" not in skip:
        check_commits(args)
    if "smoke" not in skip:
        check_smoke()
    if "docs" not in skip:
        check_docs_build(files)

    print("\n# Summary")
    for name, status in results:
        print(f"  {status:8} {name}")
    sys.exit(1 if any(s == "FAIL" for _, s in results) else 0)


if __name__ == "__main__":
    main()

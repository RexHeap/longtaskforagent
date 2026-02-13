#!/usr/bin/env python3
"""
Initialize a long-task-agent project structure.

Creates the persistent artifacts needed for multi-session agent work:
- long-task-guide.md (worker session guide with TDD workflow, auto-referenced from CLAUDE.md)
- feature-list.json (empty template)
- task-progress.md (empty progress log)
- RELEASE_NOTES.md (living release notes, updated after every git commit)
- init.sh / init.ps1 (environment bootstrap stubs)
- Appends a reference line to CLAUDE.md (creates if not exists, never overwrites)

Usage:
    python init_project.py <project-name> [--path <output-dir>]
"""

import argparse
import json
import os
import sys
from datetime import datetime


CLAUDE_MD_REFERENCE = (
    "\n\n<!-- long-task-agent -->\n"
    "## Long-Task Agent\n"
    "This project uses a multi-session agent workflow. "
    "Read `long-task-guide.md` at the start of EVERY session (including after /clear) "
    "and follow its instructions to pick up the next task.\n"
    "<!-- /long-task-agent -->\n"
)

MARKER = "<!-- long-task-agent -->"


def create_feature_list(project_name: str) -> dict:
    return {
        "project": project_name,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "features": []
    }


def create_progress_log(project_name: str) -> str:
    return f"""# Task Progress Log

## Project: {project_name}
Created: {datetime.now().strftime("%Y-%m-%d")}
Requirement Doc: [TODO: path to requirement doc]
Design Doc: [TODO: path to design doc]

---

"""


def create_long_task_guide(project_name: str) -> str:
    return f"""# {project_name} — Long-Task Worker Guide

This file guides the agent through each work session. Follow these steps on EVERY session start (including after /clear).

## Session Workflow

### Step 1: Orient — understand current state
1. Run `pwd` to confirm working directory
2. Read `task-progress.md` to see what prior sessions accomplished
3. Read `feature-list.json` to identify passing/failing features
4. Run `git log --oneline -20` to review recent commits
5. Identify the next target: highest-priority `"failing"` feature whose dependencies are all `"passing"`

### Step 2: Bootstrap — restore environment
1. Run the init script:
   - Windows: `powershell -File init.ps1`
   - Linux/Mac: `bash init.sh`
2. Quick smoke test: verify previously-passing features still work
3. If any feature regressed, fix it FIRST before starting new work

### Step 3: TDD Red — write failing tests FIRST
1. Pick the highest-priority failing feature from Step 1
2. Write **unit tests** that cover the feature's `verification_steps` — run tests, they MUST fail (no implementation yet)
3. If the feature has a UI component: write **Chrome DevTools MCP functional tests**:
   - Use `navigate_page` to load the relevant page
   - Use `take_snapshot` to capture accessibility tree
   - Use `click`, `fill` to simulate user interactions
   - Use `wait_for`, `take_screenshot` to verify expected outcomes
   - Use `list_console_messages(types=["error"])` to check for runtime errors
   - These tests MUST also fail initially

### Step 4: TDD Green — implement to pass tests
1. Write **minimal code** to make ALL tests pass (unit tests + functional tests)
2. Run full test suite — confirm all new tests green, no regressions on existing features

### Step 5: TDD Refactor — clean up
1. Refactor code while keeping all tests green
2. Run full verification again
3. Mark `status` as `"passing"` in `feature-list.json` ONLY after ALL tests (UT + functional) pass
4. If context budget remains, pick the next failing feature and repeat from Step 3

### Step 6: Persist — save state for next session
1. `git add` relevant files + `git commit` with descriptive message
2. **Update `RELEASE_NOTES.md`**: add entry under `[Unreleased]` with the feature title, ID, and change type (Added/Changed/Fixed)
3. Append a session entry to `task-progress.md`:
   ```
   ### Session N — [date]
   **Focus**: [feature title(s)]
   **Completed**: [what was done]
   **Tests**: [UT count passing, functional tests passing (if UI)]
   **Issues**: [any problems encountered]
   **Next Priority**: [next failing feature title and id]
   **Git Commits**: [commit hashes]
   ```
4. Validate: `python scripts/validate_features.py feature-list.json`
5. Commit the updated `task-progress.md`, `feature-list.json`, and `RELEASE_NOTES.md`
6. Check `feature-list.json`: if ALL features are `"passing"`, announce **project completion** and stop

### Step 7: Clear context and continue
If there are still failing features:
1. Tell the user: "Feature [X] done. Clearing context to continue with feature [Y]."
2. Execute `/clear`
3. After context is cleared, send: **"Continue working on this project. Read long-task-guide.md for instructions."**

This triggers the next session cycle starting from Step 1.

## Critical Rules
- **Strict TDD**: NEVER write implementation before tests — always Red→Green→Refactor
- **UI features require Chrome DevTools MCP testing**: use `take_snapshot`, `click`, `fill`, `take_screenshot` etc.
- **Update `RELEASE_NOTES.md` after every git commit** — keep it in sync with actual changes
- NEVER remove or edit `verification_steps` in feature-list.json
- NEVER mark a feature `"passing"` without ALL tests (UT + functional) actually passing
- NEVER leave code in a broken state — revert if a feature is incomplete
- ONE feature per context cycle (clear context after each)
- ALWAYS update task-progress.md + RELEASE_NOTES.md before clearing context
- ALWAYS commit working code before clearing context

## Project Files
| File | Purpose |
|------|---------|
| `feature-list.json` | Structured task inventory (JSON format, never convert to other formats) |
| `task-progress.md` | Session-by-session progress log |
| `RELEASE_NOTES.md` | Living release notes, updated after every git commit |
| `init.sh` / `init.ps1` | Environment bootstrap script |
| `scripts/validate_features.py` | Validates feature-list.json structure |
"""


def create_release_notes(project_name: str) -> str:
    return f"""# Release Notes — {project_name}

## [Unreleased]

### Added
- Initial project scaffold

### Changed
- (none yet)

### Fixed
- (none yet)

---

_Format: [Keep a Changelog](https://keepachangelog.com/) — Updated after every git commit._
"""


def create_init_script_sh() -> str:
    return """#!/bin/bash
# init.sh — project environment bootstrap
# Customize this script for your project's setup needs.
cd "$(dirname "$0")"

echo "=== Environment Bootstrap ==="

# Install dependencies (uncomment as needed)
# npm install
# pip install -r requirements.txt
# pip install -e .

# Start services (uncomment as needed)
# docker-compose up -d

# Start dev server (uncomment as needed)
# npm run dev &
# python manage.py runserver &

echo "=== Environment ready ==="
"""


def create_init_script_ps1() -> str:
    return """# init.ps1 — project environment bootstrap (Windows PowerShell)
# Customize this script for your project's setup needs.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== Environment Bootstrap ==="

# Install dependencies (uncomment as needed)
# npm install
# pip install -r requirements.txt
# pip install -e .

# Start services (uncomment as needed)
# docker-compose up -d

# Start dev server (uncomment as needed)
# Start-Process -NoNewWindow npm -ArgumentList "run","dev"
# Start-Process -NoNewWindow python -ArgumentList "manage.py","runserver"

Write-Host "=== Environment ready ==="
"""


def append_claude_md_reference(out_dir: str):
    """Append long-task-agent reference to CLAUDE.md (idempotent)."""
    cm_path = os.path.join(out_dir, "CLAUDE.md")

    # Check if reference already exists
    if os.path.exists(cm_path):
        with open(cm_path, "r", encoding="utf-8") as f:
            content = f.read()
        if MARKER in content:
            print(f"Skipped: {cm_path} (reference already exists)")
            return
        # Append reference
        with open(cm_path, "a", encoding="utf-8") as f:
            f.write(CLAUDE_MD_REFERENCE)
        print(f"Updated: {cm_path} (appended long-task-agent reference)")
    else:
        # Create new CLAUDE.md with just the reference
        with open(cm_path, "w", encoding="utf-8") as f:
            f.write(f"# {os.path.basename(out_dir)}\n")
            f.write(CLAUDE_MD_REFERENCE)
        print(f"Created: {cm_path}")


def main():
    parser = argparse.ArgumentParser(description="Initialize a long-task-agent project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--path", default=".", help="Output directory (default: current dir)")
    args = parser.parse_args()

    out_dir = os.path.abspath(args.path)
    os.makedirs(out_dir, exist_ok=True)

    # long-task-guide.md (worker session guide)
    guide_path = os.path.join(out_dir, "long-task-guide.md")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(create_long_task_guide(args.project_name))
    print(f"Created: {guide_path}")

    # CLAUDE.md (append reference, never overwrite)
    append_claude_md_reference(out_dir)

    # feature-list.json
    fl_path = os.path.join(out_dir, "feature-list.json")
    with open(fl_path, "w", encoding="utf-8") as f:
        json.dump(create_feature_list(args.project_name), f, indent=2, ensure_ascii=False)
    print(f"Created: {fl_path}")

    # task-progress.md
    tp_path = os.path.join(out_dir, "task-progress.md")
    with open(tp_path, "w", encoding="utf-8") as f:
        f.write(create_progress_log(args.project_name))
    print(f"Created: {tp_path}")

    # RELEASE_NOTES.md
    rn_path = os.path.join(out_dir, "RELEASE_NOTES.md")
    with open(rn_path, "w", encoding="utf-8") as f:
        f.write(create_release_notes(args.project_name))
    print(f"Created: {rn_path}")

    # init.sh
    sh_path = os.path.join(out_dir, "init.sh")
    with open(sh_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(create_init_script_sh())
    print(f"Created: {sh_path}")

    # init.ps1
    ps1_path = os.path.join(out_dir, "init.ps1")
    with open(ps1_path, "w", encoding="utf-8") as f:
        f.write(create_init_script_ps1())
    print(f"Created: {ps1_path}")

    # scripts dir
    scripts_dir = os.path.join(out_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    print(f"\nProject '{args.project_name}' initialized at {out_dir}")
    print("Files: long-task-guide.md, CLAUDE.md, feature-list.json, task-progress.md, RELEASE_NOTES.md, init.sh, init.ps1")
    print("Next: Read requirement/design docs and populate feature-list.json")


if __name__ == "__main__":
    main()

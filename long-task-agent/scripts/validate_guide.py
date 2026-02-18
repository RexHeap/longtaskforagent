#!/usr/bin/env python3
"""
Validate LLM-generated long-task-guide.md for structural completeness.

Checks that the guide contains all required workflow sections and critical
rule keywords. This prevents the LLM from accidentally omitting essential
workflow steps when generating a project-tailored guide.

Does NOT check exact content — only that required concepts are present.

Usage:
    python validate_guide.py <path/to/long-task-guide.md>

Exit codes:
    0 — all required sections present
    1 — one or more required sections missing
"""

import re
import sys


# Required section concepts — each is (label, list of alternative patterns).
# The guide passes if at least ONE pattern from each group is found (case-insensitive).
REQUIRED_SECTIONS = [
    ("Orient / current state",
     [r"orient", r"current state", r"understand.*state"]),
    ("Bootstrap / restore environment",
     [r"bootstrap", r"restore.*environment", r"init\s*script", r"init\.sh"]),
    ("Config Gate / required configurations",
     [r"config\s*gate", r"required.config", r"check_configs"]),
    ("TDD Red / failing tests first",
     [r"tdd\s*red", r"failing\s*tests?\s*first", r"write.*failing.*test"]),
    ("TDD Green / implement to pass",
     [r"tdd\s*green", r"implement.*pass", r"minimal.*code.*pass"]),
    ("Coverage Gate",
     [r"coverage\s*gate", r"coverage.*threshold", r"line.*coverage.*branch.*coverage"]),
    ("TDD Refactor",
     [r"tdd\s*refactor", r"refactor.*keeping.*test", r"clean\s*up"]),
    ("Mutation Gate / mutation testing",
     [r"mutation\s*gate", r"mutation.*test", r"mutation.*score"]),
    ("Verification enforcement",
     [r"verification.*enforce", r"fresh.*evidence", r"never.*mark.*passing.*without"]),
    ("Code Review",
     [r"code\s*review", r"spec.*compliance.*code.*quality", r"two.stage.*review"]),
    ("Examples",
     [r"example", r"examples/"]),
    ("Persist / save state / commit",
     [r"persist", r"save.*state", r"git.*commit", r"task-progress"]),
    ("Critical Rules",
     [r"critical\s*rule", r"iron\s*rule", r"must\s*never"]),
]


def validate_guide(path: str) -> list[str]:
    """
    Validate that a long-task-guide.md contains all required sections.

    Args:
        path: Path to the guide markdown file

    Returns:
        List of error strings (empty = valid)
    """
    errors = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"File not found: {path}"]
    except Exception as e:
        return [f"Cannot read file: {e}"]

    if not content.strip():
        return ["Guide file is empty"]

    content_lower = content.lower()

    for label, patterns in REQUIRED_SECTIONS:
        found = False
        for pattern in patterns:
            if re.search(pattern, content_lower):
                found = True
                break
        if not found:
            errors.append(f"Missing required section: {label}")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_guide.py <path/to/long-task-guide.md>")
        sys.exit(1)

    errors = validate_guide(sys.argv[1])

    if errors:
        print(f"GUIDE VALIDATION FAILED — {len(errors)} issue(s):\n")
        for e in errors:
            print(f"  - {e}")
        print(f"\nTotal required sections: {len(REQUIRED_SECTIONS)}")
        print(f"Missing: {len(errors)}, Present: {len(REQUIRED_SECTIONS) - len(errors)}")
        sys.exit(1)
    else:
        print(f"VALID — all {len(REQUIRED_SECTIONS)} required sections present")
        sys.exit(0)


if __name__ == "__main__":
    main()

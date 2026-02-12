#!/usr/bin/env python3
"""
Validate feature-list.json structure and integrity.

Checks:
- Valid JSON structure
- Required fields present on each feature
- No duplicate IDs
- Status values are valid
- Dependencies reference existing feature IDs
- Verification steps are non-empty

Usage:
    python validate_features.py <path/to/feature-list.json>
"""

import json
import sys


REQUIRED_FIELDS = {"id", "category", "title", "description", "priority", "status", "verification_steps"}
VALID_STATUSES = {"failing", "passing"}
VALID_PRIORITIES = {"high", "medium", "low"}


def validate(path: str) -> list[str]:
    errors = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return [f"Cannot read feature-list.json: {e}"]

    if "features" not in data:
        return ['"features" key missing from root object']

    features = data["features"]
    if not isinstance(features, list):
        return ['"features" must be an array']

    ids_seen = set()

    for i, feat in enumerate(features):
        prefix = f"Feature [{i}]"

        if not isinstance(feat, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        # Check required fields
        missing = REQUIRED_FIELDS - set(feat.keys())
        if missing:
            errors.append(f"{prefix}: missing fields: {missing}")

        # Check ID uniqueness
        fid = feat.get("id")
        if fid is not None:
            if fid in ids_seen:
                errors.append(f"{prefix}: duplicate id={fid}")
            ids_seen.add(fid)

        # Check status
        status = feat.get("status")
        if status and status not in VALID_STATUSES:
            errors.append(f"{prefix} (id={fid}): invalid status '{status}', must be one of {VALID_STATUSES}")

        # Check priority
        priority = feat.get("priority")
        if priority and priority not in VALID_PRIORITIES:
            errors.append(f"{prefix} (id={fid}): invalid priority '{priority}', must be one of {VALID_PRIORITIES}")

        # Check verification_steps
        steps = feat.get("verification_steps")
        if steps is not None:
            if not isinstance(steps, list) or len(steps) == 0:
                errors.append(f"{prefix} (id={fid}): verification_steps must be a non-empty array")

        # Check dependencies
        deps = feat.get("dependencies", [])
        if isinstance(deps, list):
            for dep in deps:
                if dep not in ids_seen and dep != fid:
                    # Defer check — dependency may appear later
                    pass

    # Second pass: validate all dependencies reference existing IDs
    all_ids = {f.get("id") for f in features if isinstance(f, dict)}
    for feat in features:
        if not isinstance(feat, dict):
            continue
        fid = feat.get("id")
        for dep in feat.get("dependencies", []):
            if dep not in all_ids:
                errors.append(f"Feature id={fid}: dependency id={dep} does not exist")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_features.py <path/to/feature-list.json>")
        sys.exit(1)

    errors = validate(sys.argv[1])

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        # Print summary
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data["features"]
        passing = sum(1 for f in features if f.get("status") == "passing")
        failing = sum(1 for f in features if f.get("status") == "failing")
        print(f"VALID — {len(features)} features ({passing} passing, {failing} failing)")
        sys.exit(0)


if __name__ == "__main__":
    main()

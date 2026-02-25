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
- tech_stack.language is a supported value (if present)
- quality_gates values are numbers between 0 and 100 (if present)
- ui field is boolean (if present)
- ui_entry field is string (if present)
- UI features (ui=true) have at least one [devtools]-prefixed verification step

Usage:
    python validate_features.py <path/to/feature-list.json>
"""

import json
import sys


REQUIRED_FIELDS = {"id", "category", "title", "description", "priority", "status", "verification_steps"}
VALID_STATUSES = {"failing", "passing"}
VALID_PRIORITIES = {"high", "medium", "low"}
VALID_LANGUAGES = {"python", "java", "javascript", "typescript", "c", "cpp", "c++"}
QUALITY_GATE_KEYS = {"line_coverage_min", "branch_coverage_min", "mutation_score_min"}
VALID_CONFIG_TYPES = {"env", "file"}
DEVTOOLS_STEP_PREFIX = "[devtools]"
REQUIRED_CONFIG_FIELDS = {"name", "type", "description", "required_by"}


def validate(path: str) -> tuple[list[str], list[str]]:
    """Validate feature-list.json. Returns (errors, warnings)."""
    errors = []
    warnings = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return [f"Cannot read feature-list.json: {e}"], []

    if "features" not in data:
        return ['"features" key missing from root object'], []

    # Validate tech_stack if present
    tech_stack = data.get("tech_stack")
    if tech_stack:
        if not isinstance(tech_stack, dict):
            errors.append("tech_stack must be an object")
        else:
            lang = tech_stack.get("language", "").lower()
            if lang and lang != "todo" and lang not in VALID_LANGUAGES:
                errors.append(
                    f"tech_stack.language '{lang}' not in supported: {sorted(VALID_LANGUAGES)}"
                )

    # Validate quality_gates if present
    quality_gates = data.get("quality_gates")
    if quality_gates:
        if not isinstance(quality_gates, dict):
            errors.append("quality_gates must be an object")
        else:
            for key in QUALITY_GATE_KEYS:
                val = quality_gates.get(key)
                if val is not None:
                    if not isinstance(val, (int, float)) or val < 0 or val > 100:
                        errors.append(
                            f"quality_gates.{key} must be a number between 0 and 100, got {val!r}"
                        )

    # Validate constraints if present
    constraints = data.get("constraints")
    if constraints is not None:
        if not isinstance(constraints, list):
            errors.append('"constraints" must be an array')
        else:
            for ci, item in enumerate(constraints):
                if not isinstance(item, str):
                    errors.append(f"constraints[{ci}]: must be a string, got {type(item).__name__}")

    # Validate assumptions if present
    assumptions = data.get("assumptions")
    if assumptions is not None:
        if not isinstance(assumptions, list):
            errors.append('"assumptions" must be an array')
        else:
            for ai, item in enumerate(assumptions):
                if not isinstance(item, str):
                    errors.append(f"assumptions[{ai}]: must be a string, got {type(item).__name__}")

    # Validate required_configs if present
    required_configs = data.get("required_configs")
    if required_configs is not None:
        if not isinstance(required_configs, list):
            errors.append("required_configs must be an array")
        else:
            config_names_seen = set()
            for ci, config in enumerate(required_configs):
                cprefix = f"required_configs[{ci}]"

                if not isinstance(config, dict):
                    errors.append(f"{cprefix}: must be an object")
                    continue

                # Check common required fields
                cmissing = REQUIRED_CONFIG_FIELDS - set(config.keys())
                if cmissing:
                    errors.append(f"{cprefix}: missing fields: {cmissing}")

                # Check name uniqueness
                cname = config.get("name")
                if cname:
                    if cname in config_names_seen:
                        errors.append(f"{cprefix}: duplicate config name '{cname}'")
                    config_names_seen.add(cname)

                # Check type is valid
                ctype = config.get("type")
                if ctype and ctype not in VALID_CONFIG_TYPES:
                    errors.append(
                        f"{cprefix}: invalid type '{ctype}', must be one of {VALID_CONFIG_TYPES}"
                    )

                # Check type-specific required fields
                if ctype == "env":
                    if "key" not in config:
                        errors.append(f"{cprefix}: env type requires 'key' field")
                elif ctype == "file":
                    if "path" not in config:
                        errors.append(f"{cprefix}: file type requires 'path' field")

                # Check required_by is a list of integers
                req_by = config.get("required_by")
                if req_by is not None:
                    if not isinstance(req_by, list):
                        errors.append(f"{cprefix}: required_by must be an array")
                    elif not all(isinstance(x, int) for x in req_by):
                        errors.append(f"{cprefix}: required_by must contain only integer feature IDs")

    features = data["features"]
    if not isinstance(features, list):
        return ['"features" must be an array'], []

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

        # Check ui field type
        ui = feat.get("ui")
        if ui is not None and not isinstance(ui, bool):
            errors.append(f"{prefix} (id={fid}): 'ui' must be a boolean, got {type(ui).__name__}")

        # Check ui_entry field type
        ui_entry = feat.get("ui_entry")
        if ui_entry is not None and not isinstance(ui_entry, str):
            errors.append(f"{prefix} (id={fid}): 'ui_entry' must be a string, got {type(ui_entry).__name__}")

        # Check ui features have at least one [devtools] verification step
        if ui is True:
            steps = feat.get("verification_steps")
            if isinstance(steps, list) and len(steps) > 0:
                devtools_steps = [
                    s for s in steps
                    if isinstance(s, str) and s.strip().lower().startswith(DEVTOOLS_STEP_PREFIX)
                ]
                if not devtools_steps:
                    errors.append(
                        f"{prefix} (id={fid}): UI feature (ui=true) must have at least one "
                        f"verification_step starting with '{DEVTOOLS_STEP_PREFIX}'"
                    )
                else:
                    # Check EXPECT/REJECT format in [devtools] steps (warnings, not errors)
                    for step in devtools_steps:
                        if "EXPECT:" not in step:
                            warnings.append(
                                f"{prefix} (id={fid}): [devtools] step missing EXPECT clause: "
                                f"'{step[:60]}...'" if len(step) > 60 else
                                f"{prefix} (id={fid}): [devtools] step missing EXPECT clause: '{step}'"
                            )
                        if "REJECT:" not in step:
                            warnings.append(
                                f"{prefix} (id={fid}): [devtools] step missing REJECT clause: "
                                f"'{step[:60]}...'" if len(step) > 60 else
                                f"{prefix} (id={fid}): [devtools] step missing REJECT clause: '{step}'"
                            )

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

    # Validate required_configs.required_by references existing feature IDs
    if required_configs and isinstance(required_configs, list):
        for ci, config in enumerate(required_configs):
            if not isinstance(config, dict):
                continue
            for ref_id in config.get("required_by", []):
                if isinstance(ref_id, int) and ref_id not in all_ids:
                    errors.append(
                        f"required_configs[{ci}] ('{config.get('name', '?')}'): "
                        f"required_by references feature id={ref_id} which does not exist"
                    )

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_features.py <path/to/feature-list.json>")
        sys.exit(1)

    result = validate(sys.argv[1])
    # Support both old (list) and new (tuple) return formats
    if isinstance(result, tuple):
        errors, warnings = result
    else:
        errors, warnings = result, []

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
        summary = f"VALID — {len(features)} features ({passing} passing, {failing} failing)"

        # Show quality gates if configured
        qg = data.get("quality_gates")
        if qg:
            line_min = qg.get("line_coverage_min", "N/A")
            branch_min = qg.get("branch_coverage_min", "N/A")
            mutation_min = qg.get("mutation_score_min", "N/A")
            summary += f" | Quality gates: line>={line_min}%, branch>={branch_min}%, mutation>={mutation_min}%"

        # Show constraints/assumptions counts
        ct = data.get("constraints", [])
        if ct:
            summary += f" | Constraints: {len(ct)}"
        at = data.get("assumptions", [])
        if at:
            summary += f" | Assumptions: {len(at)}"

        # Show required configs count
        rc = data.get("required_configs", [])
        if rc:
            summary += f" | Required configs: {len(rc)}"

        # Show tech stack if configured
        ts = data.get("tech_stack")
        if ts:
            lang = ts.get("language", "N/A")
            if lang != "TODO":
                summary += f" | Language: {lang}"

        if warnings:
            summary += f" | {len(warnings)} warning(s)"

        print(summary)

        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  - {w}")

        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Validate ST test case document structure and completeness.

Checks:
- Valid markdown structure with required sections
- Each test case has all required fields (Case ID, Related Requirement, etc.)
- Case IDs are unique and follow the ST-{CAT}-{FID}-{SEQ} format
- When --feature-list and --feature are given:
  - Every verification_step has at least one corresponding test case
  - Feature ID in case IDs matches the specified feature

Usage:
    python validate_st_cases.py <path/to/test-case-doc.md>
    python validate_st_cases.py <path/to/test-case-doc.md> --feature-list feature-list.json --feature 1
"""

import json
import re
import sys


# Case ID pattern: ST-{CATEGORY}-{FEATURE_ID}-{SEQ}
# FEATURE_ID is zero-padded 3 digits, SEQ is zero-padded 3 digits
CASE_ID_PATTERN = re.compile(
    r"^ST-(FUNC|BNDRY|UI|SEC|A11Y|PERF)-(\d{3})-(\d{3})$"
)

VALID_CATEGORIES = {"FUNC", "BNDRY", "UI", "SEC", "A11Y", "PERF"}

# Required sections within each test case block
REQUIRED_CASE_SECTIONS = [
    "用例编号",
    "关联需求",
    "测试目标",
    "前置条件",
    "测试步骤",
    "验证点",
    "后置检查",
    "元数据",
]

# Also accept English equivalents
REQUIRED_CASE_SECTIONS_EN = [
    "Case ID",
    "Related Requirement",
    "Test Objective",
    "Preconditions",
    "Test Steps",
    "Verification Points",
    "Post-Conditions",
    "Metadata",
]


def _normalize_heading(text: str) -> str:
    """Strip markdown heading markers and whitespace."""
    return text.lstrip("#").strip()


def _parse_case_blocks(content: str) -> list[dict]:
    """Parse the markdown content into test case blocks.

    Returns a list of dicts, each with:
        - 'raw': the full text of the case block
        - 'sections': dict mapping section name -> section content
        - 'case_id': extracted case ID string (or None)
        - 'line': approximate line number of the case start
    """
    lines = content.split("\n")
    cases = []
    current_case_lines = []
    current_case_start = 0
    in_case = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        heading = _normalize_heading(stripped) if stripped.startswith("#") else None

        # Detect start of a case block by "用例编号" or "Case ID" heading
        if heading and (heading == "用例编号" or heading == "Case ID"):
            # Save previous case if any
            if in_case and current_case_lines:
                cases.append({
                    "raw": "\n".join(current_case_lines),
                    "line": current_case_start + 1,
                })
            current_case_lines = [line]
            current_case_start = i
            in_case = True
        elif in_case:
            current_case_lines.append(line)

    # Save last case
    if in_case and current_case_lines:
        cases.append({
            "raw": "\n".join(current_case_lines),
            "line": current_case_start + 1,
        })

    # Parse sections within each case
    for case in cases:
        case["sections"] = {}
        case["case_id"] = None
        current_section = None
        section_lines = []

        for cline in case["raw"].split("\n"):
            cstripped = cline.strip()
            cheading = _normalize_heading(cstripped) if cstripped.startswith("#") else None

            if cheading:
                # Save previous section
                if current_section is not None:
                    case["sections"][current_section] = "\n".join(section_lines).strip()
                current_section = cheading
                section_lines = []
            else:
                section_lines.append(cline)

        # Save last section
        if current_section is not None:
            case["sections"][current_section] = "\n".join(section_lines).strip()

        # Extract case ID
        case_id_content = case["sections"].get("用例编号") or case["sections"].get("Case ID")
        if case_id_content:
            case["case_id"] = case_id_content.strip()

    return cases


def validate(path: str, feature_list_path: str = None, feature_id: int = None) -> tuple[list[str], list[str]]:
    """Validate an ST test case document. Returns (errors, warnings)."""
    errors = []
    warnings = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"File not found: {path}"], []
    except Exception as e:
        return [f"Cannot read file: {e}"], []

    if not content.strip():
        return ["File is empty"], []

    # Parse test case blocks
    cases = _parse_case_blocks(content)

    if not cases:
        errors.append("No test case blocks found (expected '### 用例编号' or '### Case ID' headings)")
        return errors, warnings

    # Check for summary section
    has_summary = ("摘要" in content or "Summary" in content)
    if not has_summary:
        warnings.append("Missing summary table section ('摘要' or 'Summary')")

    # Check for traceability matrix
    has_matrix = ("可追溯矩阵" in content or "Traceability Matrix" in content)
    if not has_matrix:
        warnings.append("Missing traceability matrix section ('可追溯矩阵' or 'Traceability Matrix')")

    # Validate each test case
    case_ids_seen = set()

    for case in cases:
        case_label = f"Case at line {case['line']}"
        cid = case["case_id"]

        # Check case ID presence
        if not cid:
            errors.append(f"{case_label}: missing case ID content")
            continue

        case_label = f"Case {cid}"

        # Check case ID format
        match = CASE_ID_PATTERN.match(cid)
        if not match:
            errors.append(
                f"{case_label}: case ID '{cid}' does not match pattern "
                f"ST-{{CATEGORY}}-{{FEATURE_ID(3 digits)}}-{{SEQ(3 digits)}}"
            )
        else:
            cat = match.group(1)
            fid_str = match.group(2)

            # Validate category
            if cat not in VALID_CATEGORIES:
                errors.append(f"{case_label}: invalid category '{cat}'")

            # Validate feature ID match if --feature specified
            if feature_id is not None:
                expected_fid = f"{feature_id:03d}"
                if fid_str != expected_fid:
                    errors.append(
                        f"{case_label}: feature ID in case ID ({fid_str}) does not match "
                        f"--feature {feature_id} (expected {expected_fid})"
                    )

        # Check uniqueness
        if cid in case_ids_seen:
            errors.append(f"{case_label}: duplicate case ID")
        case_ids_seen.add(cid)

        # Check required sections
        sections = case["sections"]
        section_names = set(sections.keys())

        for req_cn, req_en in zip(REQUIRED_CASE_SECTIONS, REQUIRED_CASE_SECTIONS_EN):
            if req_cn not in section_names and req_en not in section_names:
                errors.append(f"{case_label}: missing required section '{req_cn}' (or '{req_en}')")

        # Check test steps table exists (look for pipe-separated table)
        steps_content = sections.get("测试步骤") or sections.get("Test Steps") or ""
        if steps_content and "|" not in steps_content:
            warnings.append(f"{case_label}: test steps section does not contain a table (expected '|' delimited rows)")

        # Check verification points are non-empty
        vp_content = sections.get("验证点") or sections.get("Verification Points") or ""
        if not vp_content.strip():
            errors.append(f"{case_label}: verification points section is empty")

    # If --feature-list and --feature provided, check verification_step coverage
    if feature_list_path and feature_id is not None:
        try:
            with open(feature_list_path, "r", encoding="utf-8") as f:
                fl_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            errors.append(f"Cannot read feature-list.json: {e}")
            return errors, warnings

        features = fl_data.get("features", [])
        target_feature = None
        for feat in features:
            if isinstance(feat, dict) and feat.get("id") == feature_id:
                target_feature = feat
                break

        if not target_feature:
            errors.append(f"Feature id={feature_id} not found in {feature_list_path}")
        else:
            v_steps = target_feature.get("verification_steps", [])
            if v_steps and len(cases) == 0:
                errors.append(
                    f"Feature id={feature_id} has {len(v_steps)} verification_steps "
                    f"but no test cases found"
                )
            elif v_steps:
                # Check that every verification step is mentioned somewhere
                # in the traceability matrix or case content
                for vi, vstep in enumerate(v_steps):
                    if not isinstance(vstep, str):
                        continue
                    # Look for the step text (or index reference) in the document
                    step_ref = f"verification_step[{vi}]"
                    vstep_short = vstep[:40]
                    found = (
                        step_ref in content
                        or vstep_short in content
                        or vstep in content
                    )
                    if not found:
                        warnings.append(
                            f"verification_step[{vi}] may not be covered: "
                            f"'{vstep_short}{'...' if len(vstep) > 40 else ''}'"
                        )

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_st_cases.py <path/to/test-case-doc.md> [--feature-list path] [--feature id]")
        sys.exit(1)

    path = sys.argv[1]
    feature_list_path = None
    feature_id = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--feature-list" and i + 1 < len(sys.argv):
            feature_list_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--feature" and i + 1 < len(sys.argv):
            try:
                feature_id = int(sys.argv[i + 1])
            except ValueError:
                print(f"Error: --feature value must be an integer, got '{sys.argv[i + 1]}'")
                sys.exit(1)
            i += 2
        else:
            print(f"Unknown argument: {sys.argv[i]}")
            sys.exit(1)

    errors, warnings = validate(path, feature_list_path, feature_id)

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        if warnings:
            print(f"\n{len(warnings)} warning(s):")
            for w in warnings:
                print(f"  - {w}")
        sys.exit(1)
    else:
        summary = f"VALID — {len(_parse_case_blocks(open(path, 'r', encoding='utf-8').read()))} test case(s)"
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

# ST Test Case Template — ISO/IEC/IEEE 29119-3

> This template defines the structure for per-feature system test case documents.
> The LLM generates test case content following this structure.
> Users may override this template via `st_case_template_path` in `feature-list.json`.
> Users may also provide a style/language example via `st_case_example_path`.

---

## Document Header

```markdown
# 测试用例集: {feature_title}

**Feature ID**: {feature_id}
**关联需求**: {requirement_ids}  (e.g., FR-001, FR-002, NFR-003)
**日期**: {YYYY-MM-DD}
**测试标准**: ISO/IEC/IEEE 29119-3
**模板版本**: 1.0
```

## Summary Table

```markdown
## 摘要

| 类别 | 用例数 |
|------|--------|
| functional | N |
| boundary | N |
| ui | N |
| security | N |
| accessibility | N |
| performance | N |
| **合计** | **N** |
```

## Test Case Block (repeat per case)

Each test case MUST include ALL of the following sections. No section may be omitted.

```markdown
---

### 用例编号

ST-{CATEGORY}-{FEATURE_ID}-{SEQ}

### 关联需求

{FR-xxx / NFR-xxx}（{需求标题}）

### 测试目标

{本用例验证的具体内容，一句话描述}

### 前置条件

- {前置条件 1}
- {前置条件 2}
- ...

### 测试步骤

| Step | 操作           | 预期结果         |
| ---- | -------------- | ---------------- |
| 1    | {具体操作}     | {明确的预期结果} |
| 2    | {具体操作}     | {明确的预期结果} |
| ...  | ...            | ...              |

### 验证点

- {验证点 1 — 可观测、可断言的检查项}
- {验证点 2}
- ...

### 后置检查

- {后置检查或清理动作}
- ...

### 元数据

- **优先级**: High / Medium / Low
- **类别**: functional / boundary / ui / security / accessibility / performance
- **已自动化**: Yes / No
- **测试引用**: {test_file::test_name 或 N/A}
```

## Traceability Matrix

```markdown
## 可追溯矩阵

| 用例 ID | 关联需求 | verification_step | 自动化测试 | 结果 |
|---------|----------|-------------------|-----------|------|
| ST-FUNC-{id}-001 | FR-xxx | verification_step[0] | test_xxx | PENDING |
| ST-FUNC-{id}-002 | FR-xxx | verification_step[1] | test_xxx | PENDING |
| ... | ... | ... | ... | ... |
```

---

## Category Definitions

| Category | Abbrev | Description | When to use |
|----------|--------|-------------|-------------|
| `functional` | FUNC | Happy-path and error-path verification | Always — every feature needs functional tests |
| `boundary` | BNDRY | Edge cases, limits, empty/max/zero values | Always — test boundaries of inputs and states |
| `ui` | UI | Chrome DevTools interaction + visual verification | Only when feature has `"ui": true` |
| `security` | SEC | Injection, authorization, data validation | When feature handles user input, auth, or external data |
| `accessibility` | A11Y | WCAG 2.1 AA checks (keyboard nav, contrast, ARIA) | Only when feature has `"ui": true` |
| `performance` | PERF | Response time, throughput, resource usage | Only when traceable to NFR-xxx performance requirements |

## Case ID Format

```
ST-{CATEGORY}-{FEATURE_ID}-{SEQ}
```

- `{CATEGORY}`: One of FUNC, BNDRY, UI, SEC, A11Y, PERF
- `{FEATURE_ID}`: Feature ID from feature-list.json (zero-padded to 3 digits: 001, 002, ...)
- `{SEQ}`: Sequential number within category for this feature (001, 002, ...)

Examples:
- `ST-FUNC-005-001` — First functional test case for feature #5
- `ST-UI-005-002` — Second UI test case for feature #5
- `ST-SEC-012-001` — First security test case for feature #12

## UI Test Case Requirements

For `"ui": true` features, UI category test cases MUST include:

1. **Navigation path**: The URL or route to navigate to (from `ui_entry` or specific route)
2. **EXPECT clause**: Elements, text, or states that MUST be present after each step
3. **REJECT clause**: Conditions that MUST NOT be present (forces error-seeking)
4. **Console error gate**: Post-step check — `list_console_messages(types=["error"])` must return 0
5. **Accessibility checkpoint**: At least one WCAG check per UI test case (keyboard, contrast, ARIA)
6. **UCD token reference**: Which style tokens (colors, typography, spacing) apply to verified elements

Example UI test step:

```markdown
| Step | 操作 | 预期结果 |
| ---- | ---- | -------- |
| 1 | 导航至 /login | EXPECT: 显示邮箱输入框(type=email)、密码输入框(type=password)、登录按钮 |
| 2 | — | REJECT: 任何无 label 的输入框、禁用的提交按钮（无校验消息时）、'TODO' 占位文字 |
| 3 | 输入有效邮箱和密码 | EXPECT: 输入框显示输入内容，登录按钮保持可用 |
| 4 | 点击登录按钮 | EXPECT: 跳转至 /dashboard，控制台无 error |
```

## Execution Rules

1. **Environment prerequisite**: `start.sh` / `start.ps1` must have succeeded (Worker Step 2 Bootstrap). If services are not running, runtime test steps are BLOCKED.
2. **Failure is a Hard Gate**: Any test case failure (step result mismatch, verification point unmet, post-check failure) blocks the feature from being marked `"passing"`. Report to user via `AskUserQuestion`.
3. **No bypass allowed**: Cannot skip ST execution for any reason ("simple feature", "env temporarily unavailable", "case might be wrong"). All failures must be recorded in `task-progress.md`.
4. **Environment cleanup**: `cleanup.sh` / `cleanup.ps1` runs at Worker session end (Step 14 Continue).

## Derivation Rules

When generating test cases from a feature's `verification_steps`:

1. Each `verification_step` must produce **at least one** test case
2. Steps prefixed with `[devtools]` produce `ui` category test cases
3. Every feature gets at least one `functional` and one `boundary` test case
4. If the feature handles user input → add `security` test cases
5. If the feature has `"ui": true` → add `accessibility` test cases
6. If the feature traces to an NFR-xxx with performance metrics → add `performance` test cases
7. Test case steps must be concrete and executable (no vague "verify it works")
8. Expected results must be specific and assertable (no "should look correct")

# Test Scenario Rules

## Purpose

Rules that guide the LLM when generating test scenarios during TDD Red. These rules are **enforced by the Test Plan Review** subagent — the reviewer checks every test suite against these rules before allowing implementation to proceed.

## Rule 1: Scenario Category Coverage

Every test suite must include tests from **all applicable categories**:

| Category | What to test | Example scenarios |
|----------|-------------|-------------------|
| **Happy path** | Normal operation with valid inputs | Valid login returns token; creating user with valid data succeeds |
| **Error handling** | Known failure modes, invalid inputs, error responses | Invalid password returns 401; duplicate email returns 409; missing field returns 422 |
| **Boundary / edge cases** | Limits, empty inputs, max values, type boundaries | Empty string input; max-length password; zero-item list; single-character name |
| **Security** | Input validation, injection, authorization | SQL injection in username; XSS in display name; accessing resource without auth |

**When a category does not apply**, state it explicitly in a test file comment:

```python
# Security: N/A — this is an internal utility with no user-facing input
```

## Rule 2: Negative Test Ratio

**At least 40%** of test functions must test non-happy-path scenarios (error handling + boundary + security):

```
negative_test_count / total_test_count >= 0.40
```

**Why 40%**: Happy paths are typically fewer but more obvious. Bugs cluster at boundaries and error paths. A ratio below 40% indicates the test suite is optimistically biased.

**How to count**: Each `def test_...` function is one unit. A test is "negative" if it:
- Expects an exception, error response, or failure state
- Uses boundary/extreme input values
- Tests unauthorized access, invalid formats, or malformed data
- Tests empty, null, or missing input handling

**Example**:
```python
# 10 test functions total
# 4 happy path tests → 40%
# 3 error handling tests → 30%  ┐
# 2 boundary tests → 20%        ├─ negative = 60% ✓ (>= 40%)
# 1 security test → 10%        ┘
```

## Rule 3: Assertion Quality

**Low-value assertions must not exceed 20%** of total assertions:

```
low_value_count / total_assertion_count <= 0.20
```

Low-value assertion patterns:
- `assert x is not None` / `assert x is None` (when testing defaults)
- `assert isinstance(x, SomeType)`
- `assert len(x) > 0` (without checking contents)
- `assert "key" in dict` (without checking value)
- `assert bool(x)` / `assert x` (truthiness only)
- Import-only tests (`from module import X; assert X is not None`)

See [testing-anti-patterns.md — Anti-Pattern #14](testing-anti-patterns.md) for detailed examples and fixes.

## Rule 4: The "Wrong Implementation" Challenge

For each test function, the test author must be able to answer: **"What wrong implementation would this test catch?"**

If the answer is "almost any wrong implementation would still pass" → the test is low-value and must be rewritten.

**Concrete process** (applied during Test Plan Review):

1. For each test, imagine **2-3 plausible wrong implementations**:
   - Returns a hardcoded value instead of computing
   - Swaps two fields (e.g., returns `email` where `name` was expected)
   - Off-by-one error (e.g., `>=` instead of `>`)
   - Missing a step (e.g., doesn't hash the password)
   - Returns stale/cached data instead of fresh query

2. Check: would the test **fail** for each wrong implementation?
   - If YES for most → good test
   - If NO for most → rewrite with more specific assertions

**Example**:
```python
# BAD: Would pass for ANY wrong implementation that returns a non-None User object
def test_get_user():
    result = get_user(1)
    assert result is not None  # Passes for User(name="WRONG", email="WRONG")

# GOOD: Would fail if name or email is wrong
def test_get_user():
    result = get_user(1)
    assert result.name == "Alice"
    assert result.email == "alice@example.com"
```

## Rule 5: UI-Specific Test Rules

For features with `"ui": true` in `feature-list.json`:

### 5a. EXPECT/REJECT Format

Every `[devtools]` verification step must use the structured format:

```
[devtools] <page-path> | EXPECT: <positive criteria> | REJECT: <negative criteria>
```

- **EXPECT**: Elements, text, or states that MUST be present
- **REJECT**: Conditions that MUST NOT be present (forces error-seeking behavior)

Both clauses are required. See [ui-error-detection.md](ui-error-detection.md) for details.

### 5b. Automated Error Detection

Every UI test must execute the automated error detection script via `evaluate_script()`. Detected errors > 0 is an automatic FAIL. See [ui-error-detection.md](ui-error-detection.md) for the script.

### 5c. Console Error Gate

`list_console_messages(types=["error"])` must return 0 errors, unless the verification step explicitly expects errors via `[expect-console-error: <pattern>]`.

## Quick Reference Checklist (for Test Authors)

Before submitting tests for Test Plan Review:

- [ ] Tests cover all applicable scenario categories (happy path, error, boundary, security)
- [ ] Negative test ratio >= 40%
- [ ] Low-value assertion ratio <= 20%
- [ ] Each test would fail for at least 2 plausible wrong implementations
- [ ] No test recalculates the expected value using the same algorithm as the implementation
- [ ] Tests assert behavior (outputs/state changes), not implementation details (method calls)
- [ ] Each test is independent (no shared mutable state, no execution order dependency)
- [ ] For UI features: EXPECT/REJECT format used, automated detection included, console errors checked

## Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| [testing-anti-patterns.md](testing-anti-patterns.md) | Anti-pattern #14 defines low-value assertions in detail |
| [test-plan-review.md](test-plan-review.md) | The Test Plan Review enforces these rules via structured scoring rubric |
| [ui-error-detection.md](ui-error-detection.md) | Rules 5a-5c reference the UI error detection specification |
| [plan-writing.md](plan-writing.md) | Plan Task 1 (write tests) must follow these rules |

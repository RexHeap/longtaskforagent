# Testing Anti-Patterns

## Purpose

Catalog of common testing mistakes that produce false confidence. Reference this when writing tests or reviewing test quality.

## Anti-Pattern Catalog

### 1. Testing Mock Behavior Instead of Real Behavior

**Symptom**: Tests pass but the feature doesn't actually work.

**Example (BAD)**:
```python
def test_user_login(mock_db):
    mock_db.get_user.return_value = User(id=1, name="test")
    result = login("test", "password")
    mock_db.get_user.assert_called_once_with("test")  # Testing the mock!
```

**Why it fails**: You're testing that your code calls the mock correctly, not that the login actually works.

**Fix**: Test with real dependencies when possible (test database, in-memory store). Mock only external services you can't control.

### 2. Adding Test-Only Methods to Production Code

**Symptom**: Production code has `_test_helper()`, `get_for_testing()`, or similar methods.

**Why it fails**: Production code should not know about tests. Test-only methods can be called in production, creating maintenance burden and potential bugs.

**Fix**: Test through public interfaces. If you can't test something without a backdoor, the design needs refactoring.

### 3. Mocking Without Understanding Dependencies

**Symptom**: Every test mocks everything, and you're not sure what each mock represents.

**Why it fails**: Over-mocking makes tests brittle (break when implementation changes) and meaningless (test mock wiring, not behavior).

**Fix**:
- Understand the dependency before mocking it
- Mock at the boundary (HTTP calls, file system, time) not at internal layers
- Prefer fakes (in-memory implementations) over mocks for complex dependencies

### 4. Testing Implementation Details

**Symptom**: Tests break when you refactor without changing behavior.

**Example (BAD)**:
```python
def test_sort():
    result = sort_list([3, 1, 2])
    # Testing that quicksort was used (implementation detail)
    assert mock_quicksort.called
```

**Fix**: Test the output, not how it was computed:
```python
def test_sort():
    result = sort_list([3, 1, 2])
    assert result == [1, 2, 3]
```

### 5. Non-Deterministic Tests

**Symptom**: Tests pass sometimes and fail sometimes.

**Common causes**:
- Depending on current time/date
- Random values without seeds
- Race conditions in async code
- Shared state between tests
- Network calls to external services

**Fix**: Control all sources of non-determinism. Use fixed timestamps, seeded random, proper async handling, test isolation, and mocked network.

### 6. Tests That Can't Fail

**Symptom**: Test always passes regardless of implementation.

**Example (BAD)**:
```python
def test_something():
    try:
        result = do_thing()
        assert result is not None
    except:
        pass  # Swallowing the failure!
```

**Fix**: Always run TDD Red first — if the test passes before implementation, the test is wrong.

### 7. Testing Too Much in One Test

**Symptom**: One test has 20+ assertions covering multiple behaviors.

**Why it fails**: When it fails, you don't know which behavior broke. Makes debugging harder.

**Fix**: One behavior per test. Use descriptive test names that describe the single behavior being tested.

### 8. Shared Mutable State Between Tests

**Symptom**: Tests pass in isolation but fail when run together.

**Why it fails**: One test modifies shared state that another test depends on.

**Fix**: Each test sets up and tears down its own state. Use fresh fixtures, database transactions, or isolated test containers.

### 9. Assertion-Free Tests

**Symptom**: Test runs code but doesn't assert anything meaningful.

**Example (BAD)**:
```python
def test_create_user():
    create_user("test", "test@email.com")
    # No assertion! Just checking it doesn't throw.
```

**Fix**: Assert the observable outcome:
```python
def test_create_user():
    user = create_user("test", "test@email.com")
    assert user.name == "test"
    assert user.email == "test@email.com"
```

### 10. Copy-Paste Test Suites

**Symptom**: Tests are duplicated with minor variations, making the suite hard to maintain.

**Fix**: Use parameterized tests for variations. Extract shared setup into fixtures. But avoid over-abstracting — tests should be readable without jumping through hoops.

### 11. Gaming Coverage with Assert-Free Tests

**Symptom**: High coverage numbers but tests have weak or no assertions.

**Example (BAD)**:
```python
def test_process_data():
    process_data(sample_input)  # 100% line coverage, 0% verification
```

**Why it fails**: Exercising code paths without verifying correctness gives false confidence. Tests will never fail even if the function returns garbage.

**Fix**: Every test must assert observable outcomes. Mutation testing exposes this — if a mutant survives, the test isn't actually checking the result.

```python
def test_process_data():
    result = process_data(sample_input)
    assert result.status == "success"
    assert result.count == 42
```

### 12. Ignoring Surviving Mutants

**Symptom**: Mutation score below threshold but feature is marked as "passing" anyway.

**Why it fails**: Surviving mutants are bugs your tests can't catch. If you change `>` to `>=` and no test fails, your boundary logic is untested.

**Fix**: For each surviving mutant:
- **Real gap**: add a test that kills it
- **Equivalent mutant**: document why the change produces identical behavior (e.g., `# equivalent mutant: condition is always true due to precondition on line X`)
- **Never ignore**: every survivor must be addressed (fixed or documented)

### 13. Running Mutation Tests on Untested Code

**Symptom**: Running mutation tests before achieving coverage threshold. Many mutants show "no coverage".

**Why it fails**: Mutation testing on uncovered code produces many false survivors and wastes time — there's no test to kill the mutant in the first place.

**Fix**: Always pass the coverage gate before running mutation tests. Coverage first, mutation second.

## Quick Reference: Test Writing Checklist

Before marking a test as complete:

- [ ] Test fails without the implementation (TDD Red verified)
- [ ] Test name describes the behavior being tested
- [ ] Test has meaningful assertions (not just "no error")
- [ ] Test is deterministic (passes/fails consistently)
- [ ] Test is independent (doesn't depend on other tests' state)
- [ ] Test tests behavior, not implementation details
- [ ] No test-only methods added to production code
- [ ] Mocks are at boundaries, not internal layers
- [ ] Coverage meets project thresholds (line >= 90%, branch >= 80%)
- [ ] Mutation score meets threshold (>= 80%) for changed files
- [ ] No surviving mutants without justification

# System Testing Recipes

Per-language/framework recipes for each ST test category. Select recipes based on `tech_stack` in `feature-list.json`.

## 1. Integration Test Patterns

### Python
```bash
# Directory structure
tests/integration/
  test_feature_a_b_integration.py
  conftest.py  # shared fixtures

# Run with pytest
pytest tests/integration/ -v --tb=short

# With coverage
pytest tests/integration/ --cov=src --cov-report=term-missing
```

**Patterns:**
- Use `pytest` fixtures for shared state setup/teardown
- Use `unittest.mock.patch` for external service boundaries
- Use `sqlite:///:memory:` or `testcontainers` for database integration
- Use `httpx` or `requests-mock` for HTTP API contract tests

### JavaScript / TypeScript
```bash
# Directory structure
tests/integration/
  featureA-featureB.test.ts
  setup.ts  # shared setup

# Run with vitest
npx vitest run tests/integration/ --reporter=verbose

# Run with jest
npx jest tests/integration/ --verbose
```

**Patterns:**
- Use `beforeAll`/`afterAll` for shared state
- Use `msw` (Mock Service Worker) for HTTP contract tests
- Use `testcontainers` for database integration
- Use `supertest` for Express/Fastify API integration

### Java
```bash
# Directory structure
src/test/java/integration/
  FeatureABIntegrationTest.java

# Run with Maven
mvn test -Dtest="integration.*" -pl module-name

# Run with Gradle
./gradlew test --tests "integration.*"
```

**Patterns:**
- Use `@SpringBootTest` for Spring integration
- Use `Testcontainers` for database/service integration
- Use `RestAssured` for API contract tests
- Use `@DirtiesContext` for state isolation between tests

### C / C++
```bash
# Integration tests in separate directory
tests/integration/
  test_module_integration.cpp

# Build and run with CMake + CTest
cmake --build build --target integration_tests
ctest --test-dir build -R integration -V
```

**Patterns:**
- Use `gtest` fixtures for shared state
- Use mock libraries (`gmock`, `fff`) for external boundaries
- Test IPC, shared memory, file I/O between modules

---

## 2. E2E Test Tools

### API-Based E2E

| Language | Tool | Install |
|----------|------|---------|
| Python | `httpx` + `pytest` | `pip install httpx` |
| Python | `requests` + `pytest` | `pip install requests` |
| JS/TS | `supertest` | `npm install supertest` |
| JS/TS | `axios` + `vitest` | `npm install axios` |
| Java | `RestAssured` | Maven: `io.rest-assured:rest-assured` |

### UI E2E (Chrome DevTools MCP)

For projects with `"ui": true` features, use Chrome DevTools MCP tools directly:

```
1. navigate_page → url: <ui_entry from feature>
2. take_snapshot → capture initial state
3. click/fill/press_key → simulate user interaction
4. take_snapshot → verify state change
5. list_console_messages → check for errors
6. list_network_requests → verify API calls
7. take_screenshot → visual evidence
```

**Multi-step workflow pattern:**
```
Scenario: User completes checkout flow
  navigate_page → /products
  click → "Add to Cart" button
  navigate_page → /cart
  take_snapshot → verify cart has item
  click → "Checkout" button
  fill_form → payment details
  click → "Pay" button
  wait_for → "Order confirmed"
  take_snapshot → verify confirmation page
  list_console_messages → zero errors
```

### CLI E2E

| Language | Approach |
|----------|----------|
| Python | `subprocess.run()` in pytest |
| Node.js | `execa` or `child_process` in vitest |
| Java | `ProcessBuilder` in JUnit |
| C/C++ | `system()` or `popen()` in gtest |

---

## 3. Performance Benchmarking

### Python
```bash
# pytest-benchmark (micro-benchmarks)
pip install pytest-benchmark
pytest tests/perf/ --benchmark-only --benchmark-json=benchmark.json

# locust (load testing)
pip install locust
locust -f tests/perf/locustfile.py --headless -u 100 -r 10 --run-time 60s --csv=perf_results

# time module (simple timing)
import time
start = time.perf_counter()
# ... operation ...
elapsed = time.perf_counter() - start
assert elapsed < 0.2, f"Response time {elapsed:.3f}s exceeds 200ms threshold"
```

### JavaScript / TypeScript
```bash
# Vitest bench
npx vitest bench

# k6 (load testing)
k6 run tests/perf/load-test.js --out csv=perf_results.csv

# autocannon (HTTP benchmarking)
npx autocannon -c 100 -d 30 http://localhost:3000/api/endpoint
```

### Java
```bash
# JMH (micro-benchmarks)
mvn exec:exec -Pbenchmark

# Gatling (load testing)
mvn gatling:test
```

### C / C++
```bash
# Google Benchmark
cmake --build build --target benchmarks
./build/benchmarks --benchmark_format=json --benchmark_out=benchmark.json

# Custom timing
#include <chrono>
auto start = std::chrono::high_resolution_clock::now();
// ... operation ...
auto elapsed = std::chrono::duration<double>(std::chrono::high_resolution_clock::now() - start).count();
```

---

## 4. Security Scanning

### Dependency Vulnerability Scanners

| Language | Tool | Command |
|----------|------|---------|
| Python | `pip-audit` | `pip-audit --strict` |
| Python | `safety` | `safety check` |
| JS/TS | `npm audit` | `npm audit --audit-level=high` |
| JS/TS | `snyk` | `npx snyk test` |
| Java | `OWASP Dependency-Check` | `mvn org.owasp:dependency-check-maven:check` |
| C/C++ | `cve-bin-tool` | `cve-bin-tool ./build/` |
| General | `trivy` | `trivy fs --severity HIGH,CRITICAL .` |

### Static Analysis (Security-Focused)

| Language | Tool | Command |
|----------|------|---------|
| Python | `bandit` | `bandit -r src/ -f json -o bandit-report.json` |
| JS/TS | `eslint-plugin-security` | `npx eslint --rule 'security/*' src/` |
| Java | `SpotBugs + FindSecBugs` | `mvn spotbugs:check` |
| C/C++ | `cppcheck` | `cppcheck --enable=all --force src/` |

### OWASP Top 10 Checklist (Manual Review)

| # | Category | What to Check |
|---|----------|---------------|
| A01 | Broken Access Control | Auth bypass, privilege escalation, IDOR |
| A02 | Cryptographic Failures | Hardcoded secrets, weak algorithms, plaintext sensitive data |
| A03 | Injection | SQL, XSS, command, LDAP, template injection |
| A04 | Insecure Design | Missing rate limiting, missing input validation |
| A05 | Security Misconfiguration | Debug mode, default credentials, verbose errors |
| A06 | Vulnerable Components | Outdated dependencies (run scanner above) |
| A07 | Authentication Failures | Weak passwords, missing MFA, session fixation |
| A08 | Data Integrity Failures | Unsigned updates, untrusted deserialization |
| A09 | Logging Failures | Missing audit logs, sensitive data in logs |
| A10 | SSRF | Unvalidated URLs, internal network access |

---

## 5. Accessibility Testing

### Automated Tools

| Tool | Language | Command |
|------|----------|---------|
| axe-core | JS/TS | `npx @axe-core/cli http://localhost:3000 --tags wcag2aa` |
| pa11y | JS/TS | `npx pa11y http://localhost:3000 --standard WCAG2AA --reporter json` |
| Lighthouse | General | `npx lighthouse http://localhost:3000 --only-categories=accessibility --output=json` |

### Manual Checks (WCAG 2.1 AA)

| Criterion | Check |
|-----------|-------|
| 1.1.1 Non-text Content | All images have alt text |
| 1.3.1 Info and Relationships | Semantic HTML (headings, lists, tables) |
| 1.4.3 Contrast | 4.5:1 for normal text, 3:1 for large text |
| 2.1.1 Keyboard | All interactive elements reachable via Tab/Enter/Space |
| 2.4.1 Skip Navigation | Skip-to-content link exists |
| 4.1.2 Name, Role, Value | ARIA labels on custom components |

### Chrome DevTools MCP Accessibility Check
```
1. navigate_page → target URL
2. take_snapshot verbose:true → inspect a11y tree
3. Verify: all interactive elements have accessible names
4. Verify: heading hierarchy is logical (h1 → h2 → h3)
5. Verify: form inputs have associated labels
```

---

## 6. Compatibility Testing

### Cross-Browser (UI Projects)

Use Chrome DevTools MCP with different user agents:

```
# Emulate different browsers
emulate → userAgent: "Mozilla/5.0 ... Firefox/120.0"
emulate → viewport: { width: 1920, height: 1080 }
navigate_page → target URL
take_screenshot → evidence

# Mobile emulation
emulate → viewport: { width: 375, height: 812, isMobile: true, hasTouch: true }
```

### Cross-Platform (CLI/Library)

Verify on target platforms using available environment:
```bash
# Check platform-specific behavior
python -c "import platform; print(platform.system())"

# Verify file path handling
# Verify line ending handling
# Verify permission handling
```

---

## 7. Test Report Metrics Collection

### Collecting Coverage Metrics

| Language | Command to Get Summary |
|----------|----------------------|
| Python | `pytest --cov=src --cov-report=term-missing` |
| JS/TS | `npx vitest run --coverage` |
| Java | `mvn jacoco:report` (then read `target/site/jacoco/index.html`) |
| C/C++ | `gcovr --print-summary` |

### Collecting Test Counts

| Language | Command |
|----------|---------|
| Python | `pytest --tb=no -q` (last line shows counts) |
| JS/TS | `npx vitest run --reporter=verbose` |
| Java | `mvn test` (Surefire report) |
| C/C++ | `ctest --test-dir build -V` |

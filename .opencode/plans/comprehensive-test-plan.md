# Comprehensive Test Plan for Peppy

## Overview
This document outlines a comprehensive test suite for Peppy codebase indexing plugin, focusing on:
- Correct file selection and search accuracy
- Context token optimization (savings)
- Multi-language parsing
- Property-based testing with Hypothesis
- Performance benchmarks run on CI

## Test Suite Structure

```
tests/
├── fixtures/
│   └── sample_codebase/          # Multi-language test fixtures
│       ├── python/
│       │   ├── basic.py          # Simple functions, classes, variables
│       │   ├── advanced.py       # Nested classes, decorators, async
│       │   └── errors.py         # Syntax errors (for error handling)
│       ├── javascript/
│       │   └── sample.js         # ES6+ features
│       ├── typescript/
│       │   └── sample.ts         # Interfaces, types, generics
│       ├── go/
│       │   └── sample.go         # Structs, methods, interfaces
│       └── rust/
│           └── sample.rs         # Structs, impls, enums
├── unit/
│   ├── test_cache.py             # Cache CRUD, corruption, expiration
│   ├── test_parsers.py           # All 6 languages, fallback mode
│   ├── test_indexer.py           # File collection, gitignore, parallel
│   └── test_searcher.py          # Search filters, edge cases, context
├── property/
│   ├── test_cache_consistency.py # Property-based cache validation
│   ├── test_search_properties.py # Search result properties
│   └── test_parser_properties.py # Symbol extraction properties
├── integration/
│   ├── test_mcp_tools.py         # All 6 MCP tools end-to-end
│   └── test_workflows.py         # Real-world usage scenarios
├── performance/
│   └── test_scalability.py       # Small/medium/large benchmarks
└── token_efficiency/
    └── test_token_optimization.py # Token savings verification
```

---

## 1. Fixtures - Multi-Language Sample Codebase

### File: `tests/fixtures/sample_codebase/python/basic.py`
```python
"""Basic Python code for testing symbol extraction."""

def hello_world():
    """Simple greeting function."""
    return "Hello, World!"

def calculate_sum(a, b):
    """Add two numbers."""
    return a + b

class Calculator:
    """Calculator class for basic operations."""

    def add(self, x, y):
        """Add method."""
        return x + y

    def subtract(self, x, y):
        """Subtract method."""
        return x - y

PI = 3.14159
```

### File: `tests/fixtures/sample_codebase/python/advanced.py`
```python
"""Advanced Python features for testing."""

from typing import Optional, List
from functools import wraps

API_VERSION = "1.0.0"

async def fetch_data(url: str) -> dict:
    """Async function for network operations."""
    await None
    return {"data": "value"}

class Outer:
    """Outer class with inner class."""

    @staticmethod
    def static_method():
        """Static method."""
        pass

    @classmethod
    def class_method(cls):
        """Class method."""
        pass

    class Inner:
        """Inner class definition."""

        def method(self):
            """Instance method."""
            pass

def decorator(func):
    """Simple decorator."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

### File: `tests/fixtures/sample_codebase/python/errors.py`
```python
"""File with syntax errors for error handling tests."""

def incomplete_function(
    """Missing closing parenthesis."""
    pass

class IncompleteClass:
    """Incomplete class definition."""

def
    """No function name."""
```

### File: `tests/fixtures/sample_codebase/javascript/sample.js`
```javascript
// JavaScript ES6+ features

const API_VERSION = "1.0.0";

function calculateSum(a, b) {
    return a + b;
}

class Calculator {
    add(x, y) {
        return x + y;
    }

    static create() {
        return new Calculator();
    }
}

const arrowFunction = (a, b) => a + b;

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}
```

### File: `tests/fixtures/sample_codebase/typescript/sample.ts`
```typescript
// TypeScript with interfaces and generics

interface IUser {
    id: number;
    name: string;
}

type Result<T> = Success<T> | Error;

interface Success<T> {
    status: 'success';
    data: T;
}

interface Error {
    status: 'error';
    message: string;
}

class ApiClient<T> {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    async get(url: string): Promise<Result<T>> {
        return { status: 'success', data: {} as T };
    }
}

function processData<T>(data: T): T {
    return data;
}
```

### File: `tests/fixtures/sample_codebase/go/sample.go`
```go
// Go sample code

package main

type User struct {
    Name string
    ID   int
}

type Service interface {
    GetUser(id int) (*User, error)
}

type UserService struct{}

func (s *UserService) GetUser(id int) (*User, error) {
    return &User{Name: "test", ID: id}, nil
}

func CalculateSum(a, b int) int {
    return a + b
}
```

### File: `tests/fixtures/sample_codebase/rust/sample.rs`
```rust
// Rust sample code

struct User {
    name: String,
    id: u32,
}

impl User {
    fn new(name: String, id: u32) -> Self {
        User { name, id }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

enum Status {
    Active,
    Inactive,
}

fn calculate_sum(a: i32, b: i32) -> i32 {
    a + b
}
```

---

## 2. Unit Tests - `unit/test_cache.py` (18 tests)

### Test Categories:

#### Cache Lifecycle (4 tests)
- `test_cache_directory_creation` - Cache dir created on init
- `test_cache_set_and_get` - Basic set/get operations
- `test_cache_set_overwrite` - Overwrite existing cache
- `test_cache_clear_specific_path` - Clear single path cache

#### Cache Validation (6 tests)
- `test_cache_timestamp_validation` - Fresh cache accepted
- `test_cache_path_validation` - Deleted paths invalidate cache
- `test_cache_invalid_json_handling` - Corrupted JSON handled gracefully
- `test_cache_missing_timestamp` - Cache without timestamp rejected
- `test_cache_key_consistency` - Same path produces same key
- `test_cache_key_collision_different_paths` - Different paths produce different keys

#### Cache Edge Cases (4 tests)
- `test_cache_nonexistent_path` - Get returns None for missing
- `test_cache_empty_index` - Storing/empty index data
- `test_cache_large_data` - Large index handling
- `test_cache_concurrent_access` - Thread-safe operations

#### Cache Errors (4 tests)
- `test_cache_write_permission_error` - Handle write failures gracefully
- `test_cache_read_permission_error` - Handle read failures gracefully
- `test_cache_cleanup_on_errors` - Partial cache doesn't break system
- `test_cache_directory_creation_failure` - Handle missing cache dir

---

## 3. Unit Tests - `unit/test_parsers.py` (22 tests)

### Test Categories:

#### Language Detection (4 tests)
- `test_python_extension_detection` - .py maps to python
- `test_javascript_extensions` - .js and .jsx map to javascript
- `test_typescript_extensions` - .ts and .tsx map to typescript
- `test_unknown_extension_returns_none` - Unknown extensions handled

#### Python Parsing (4 tests)
- `test_python_functions_detected` - find functions and their locations
- `test_python_classes_detected` - find classes and their locations
- `test_python_nested_classes` - deeply nested class structures
- `test_python_decorators_and_async` - decorated and async functions

#### JavaScript Parsing (3 tests)
- `test_javascript_functions` - function declarations and expressions
- `test_javascript_classes` - class definitions
- `test_javascript_arrow_functions` - arrow function syntax

#### TypeScript Parsing (3 tests)
- `test_typescript_interfaces` - interface declarations
- `test_typescript_types` - type aliases
- `test_typescript_generics` - generic type handling

#### Go Parsing (2 tests)
- `test_go_functions` - function declarations
- `test_go_structs_and_methods` - struct definitions and methods

#### Rust Parsing (2 tests)
- `test_rust_functions` - function definitions
- `test_rust_structs_and_impls` - struct and impl blocks

#### Fallback Parser (2 tests)
- `test_fallback_python_parsing` - Regex-based Python parsing
- `test_fallback_handles_syntax_errors` - Invalid syntax doesn't crash

#### Edge Cases (2 tests)
- `test_parser_empty_file` - Empty files return empty symbols
- `test_parser_unicode_handling` - Unicode in symbol names

---

## 4. Unit Tests - `unit/test_indexer.py` (14 tests)

### Test Categories:

#### File Collection (4 tests)
- `test_collect_files_by_extension` - Only supported extensions
- `test_collect_ignored_directories` - ignores node_modules, .git, etc.
- `test_gitignore_respected` - custom .gitignore patterns
- `test_collect_empty_directory` - empty directory returns empty

#### File Indexing (3 tests)
- `test_index_single_file` - parses symbols correctly
- `test_index_multiple_files` - batch indexing
- `test_index_error_handling` - file errors don't stop indexing

#### Cache Integration (2 tests)
- `test_index_uses_cache_when_available` - honors existing cache
- `test_index_force_reindex` - ignores cache when forced

#### Parallel Processing (2 tests)
- `test_parallel_indexing` - efficient with multiple files
- `test_parallel_indexing_errors` - one error doesn't stop others

#### Edge Cases (3 tests)
- `test_nonexistent_path` - graceful handling
- `test_symlink_handling` - symbolic link resolution
- `test_large_files` - memory usage bounded

---

## 5. Unit Tests - `unit/test_searcher.py` (20 tests)

### Focus: **Context Token Savings**

#### Symbol Search (6 tests)
- `test_symbol_search_basic` - exact match query
- `test_symbol_search_regex` - regex pattern matching
- `test_symbol_search_empty_results` - no matches returns empty
- `test_symbol_search_type_filter` - filter by function/class/method
- `test_symbol_search_file_pattern_filter` - filter by *.py, *.js
- `test_symbol_search_limit` - respects limit parameter

#### Grep Search (6 tests with focus on token savings)
- `test_grep_basic_pattern` - simple pattern matching
- `test_grep_with_context_lines` - context returned correctly
- `test_grep_no_context_minimizes_tokens` - zero context saves tokens
- `test_grep_max_results_limited` - respects max_results parameter
- `test_grep_file_pattern_filter` - reduces search space (token savings)
- `test_grep_regex_handling` - invalid regex falls back gracefully

#### File Operations (3 tests)
- `test_get_file_symbols` - returns all symbols in file
- `test_get_file_symbols_empty` - empty file returns empty list
- `test_nonexistent_file` - returns empty gracefully

#### Statistics (2 tests)
- `test_statistics_correct_counts` - file and symbol counts accurate
- `test_statistics_correct_types` - symbol types and extensions correct

#### Edge Cases (3 tests)
- `test_search_not_indexed` - returns empty for unindexed codebase
- `test_search_regex_error_handling` - invalid regex handled
- `test_search_large_result_set` - handles thousands of results

---

## 6. Property Tests - `property/test_cache_consistency.py` (8 tests)

### Using Hypothesis

#### Cache Key Properties (2 tests)
```python
@given(st.text())
def test_cache_key_deterministic(path):
    """Same input always produces same key."""
    key1 = cache._get_cache_key(Path(path))
    key2 = cache._get_cache_key(Path(path))
    assert key1 == key2
```

```python
@given(st.text(), st.text())
def test_cache_key_never_collides_different_paths(path1, path2):
    """Different paths should have different keys."""
    assume(path1 != path2)
    key1 = cache._get_cache_key(Path(path1))
    key2 = cache._get_cache_key(Path(path2))
    assume(key1 != key2)
```

#### Cache Roundtrip Property (2 tests)
```python
@given(st.dictionaries(st.text(), st.one_of(st.text(), st.integers(), st.booleans())))
def test_cache_roundtrip_preserves_data(data):
    """Data should be unchanged after set/get."""
    cache.set(Path("/test"), data)
    retrieved = cache.get(Path("/test"))
    assert retrieved["index"] == data
```

#### Search Result Properties (2 tests)
```python
@given(st.lists(st.text(), min_size=0))
def test_search_results_within_limit(symbols):
    """Results never exceed limit."""
    results = searcher.search_symbols(path, "*", limit=10)
    assert len(results) <= 10
```

#### Symbol Location Properties (2 tests)
```python
@given(st.sampled_from(fixtures))
def test_symbol_positions_within_file_bounds(file_path):
    """Line/column positions should be within file."""
    symbols = parser.parse_file(file_path)
    for symbol in symbols:
        with open(file_path) as f:
            lines = f.readlines()
        assert 0 < symbol.line <= len(lines)
        assert symbol.column >= 0
```

---

## 7. Property Tests - `property/test_search_properties.py` (6 tests)

#### Filter Combinations Property
```python
@given(st.lists(st.text()), st.sampled_from(["function", "class", "method"]))
def test_filters_always_reduce_results(all_symbols, symbol_type):
    """Applying a filter should not increase results."""
    unfiltered = searcher.search_symbols(path, "*")
    filtered = searcher.search_symbols(path, "*", symbol_type=symbol_type)
    assert len(filtered) <= len(unfiltered)
```

#### Search Result Consistency
```python
@given(st.text(), st.integers(min_value=0, max_value=100))
def test_search_results_include_query(query, limit):
    """All results should contain or match the query."""
    results = searcher.search_symbols(path, query, limit=limit)
    for result in results:
        assert re.search(query, result.name, re.IGNORECASE)
```

---

## 8. Property Tests - `property/test_parser_properties.py` (5 tests)

#### Symbol Count Non-Negative
```python
@given(st.sampled_from(fixtures))
def test_symbol_count_non_negative(file_path):
    """Parsing should never return negative counts."""
    symbols = parser.parse_file(file_path)
    assert len(symbols) >= 0
```

#### Symbol Names Non-Empty
```python
@given(st.sampled_from(fixtures))
def test_symbol_names_non_empty(file_path):
    """All symbols should have non-empty names."""
    symbols = parser.parse_file(file_path)
    for symbol in symbols:
        assert symbol.name and len(symbol.name) > 0
```

#### No Duplicate Locations
```python
@given(st.sampled_from(fixtures))
def test_no_duplicate_locations(file_path):
    """Symbols should not have duplicate exact locations."""
    symbols = parser.parse_file(file_path)
    locations = {(s.file_path, s.line, s.column) for s in symbols}
    assert len(locations) == len(symbols)
```

---

## 9. Integration Tests - `integration/test_mcp_tools.py` (18 tests)

### Test Categories:

#### `index_codebase` Tool (3 tests)
- `test_mcp_index_codebase_valid_path` - indexes successfully
- `test_mcp_index_codebase_invalid_path` - returns error for non-existent
- `test_mcp_index_codebase_force_reindex` - ignores cache when forced

#### `search_symbols` Tool (3 tests)
- `test_mcp_search_symbols_basic` - finds symbols correctly
- `test_mcp_search_symbols_missing_index` - returns error for unindexed
- `test_mcp_search_symbols_with_filters` - respects type and file filters

#### `grep_code` Tool (3 tests)
- `test_mcp_grep_code_basic` - finds patterns correctly
- `test_mcp_grep_code_with_context` - includes context lines properly
- `test_mcp_grep_code_max_results` - respects result limit

#### `get_file_symbols` Tool (3 tests)
- `test_mcp_get_file_symbols_valid` - returns file symbols
- `test_mcp_get_file_symbols_invalid` - returns empty for non-existent
- `test_mcp_get_file_symbols_not_indexed` - returns error for unindexed codebase

#### `get_statistics` Tool (3 tests)
- `test_mcp_get_statistics_valid` - returns correct statistics
- `test_mcp_get_statistics_not_indexed` - returns error message
- `test_mcp_get_statistics_correct_counts` - validates file/symbol counts

#### `clear_cache` Tool (3 tests)
- `test_mcp_clear_cache_all` - clears all caches
- `test_mcp_clear_cache_specific` - clears one codebase cache
- `test_mcp_clear_cache_no_path` - clears all with no argument

---

## 10. Integration Tests - `integration/test_workflows.py` (12 tests)

### Focus: **Token-Saving Workflows**

#### Exploration Workflow (2 tests)
- `test_exploration_workflow_start_to_finish` - index → stats → symbol search
- `test_exploration_workflow_token_efficient` - minimal context, focused queries

#### Debugging Workflow (2 tests)
- `test_debugging_workflow_find_errors` - grep errors → find definitions
- `test_debugging_workflow_with_context` - minimal context for location

#### Refactoring Workflow (2 tests)
- `test_refactoring_workflow_find_function` - locate definition + usages
- `test_refactoring_workflow_verify_changes` - check after modifications

#### Multi-Language Search (2 tests)
- `test_cross_language_search` - symbols across different files
- `test_language_specific_search` - filter by file extension

#### Cache Persistence (2 tests)
- `test_cache_persists_across_sessions` - index survives restart
- `test_cache_invalidation_on_changes` - cache fresh after code changes

#### Siggy Integration (2 tests)
- `test_siggy_planning_workflow` - prompt helpers work correctly
- `test_siggy_execution_workflow` - targeted location finding

---

## 11. Performance Tests - `performance/test_scalability.py` (9 tests)
**All tests run on CI with standard timeout guards**

### Test Categories:

#### Small Codebase (2 tests)
- `test_small_codebase_10_files` - baseline performance (~100ms)
- `test_small_codebase_search_speed` - query performance (~50ms)

#### Medium Codebase (2 tests)
- `test_medium_codebase_100_files` - scaling performance (~1s)
- `test_medium_codebase_search_speed` - query performance (~200ms)

#### Large Codebase (2 tests)
- `test_large_codebase_1000_files` - stress test performance (~30s)
- `test_large_codebase_search_speed` - query performance (~1s)

#### Memory Usage (2 tests)
- `test_indexing_memory_usage` - bounded memory during indexing
- `test_search_memory_usage` - bounded memory during search

#### Cache Performance (1 test)
- `test_cache_load_save_speed` - cache persistence speed (~100ms)

### Performance Assertions
```python
@pytest.mark.timeout(60)  # CI timeout guard
def test_large_codebase_1000_files():
    import time
    start = time.time()
    stats = interface.index(large_fixture)
    duration = time.time() - start
    assert duration < 60  # Complete within 60 seconds
    # Memory check would be implemented separately
```

---

## 12. Token Efficiency Tests - `token_efficiency/test_token_optimization.py` (10 tests)

### Focus: **Verifying Context Token Savings Claims**

#### Result Limiting (3 tests)
- `test_search_respects_limit_param` - never returns more than limit
- `test_grep_respects_max_results` - grep result count bounded
- `test_default_limits_prevent_overflow` - default limits are reasonable

#### Context Optimization (3 tests)
- `test_zero_context_minimizes_tokens` - no context lines returned
- `test_context_lines_honored` - exact number of lines returned
- `test_context_only_when_needed` - location-only queries have no context

#### File Pattern Filtering (2 tests)
- `test_file_pattern_reduces_search_space` - filtered searches are faster
- `test_file_pattern_correctness` - only matching files searched

#### Token Savings Verification (2 tests)
- `test_index_once_search_many_pattern` - reuse index across searches
- `test_cache_avoids_reindexing_cost` - cached searches are instant

---

## Test Execution Strategy

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run only property tests
pytest tests/property/ -v

# Run specific test suite
pytest tests/unit/test_searcher.py -v -k grep

# Run with coverage
pytest --cov=peppy tests/ --cov-report=html
```

### CI Configuration
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e .[dev]
          pip install pytest-timeout pytest-mock

      - name: Run tests
        run: pytest tests/ -v --timeout=300 --cov=peppy --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Dependencies to Add
Update `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-timeout>=2.1.0",
    "pytest-mock>=3.11.0",
    "hypothesis>=6.80.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

---

## Estimated Test Metrics

| Category | Test Count | Lines of Code | Focus Areas |
|----------|-----------|---------------|-------------|
| Unit | 74 tests | ~1,800 LOC | Core functionality correctness |
| Property | 19 tests | ~600 LOC | Hypothesis-based invariants |
| Integration | 30 tests | ~1,200 LOC | MCP tools, workflows |
| Performance | 9 tests | ~400 LOC | Scalability benchmarks |
| Token Efficiency | 10 tests | ~500 LOC | Savings verification |
| **Total** | **142 tests** | **~4,500 LOC** | **Comprehensive coverage** |

---

## Key Testing Priorities

### 1. Correct File Selection (Priority: Critical)
- Search results only contain symbols from files matching queries
- File pattern filters work correctly
- No files are missed during collection
- Ignored directories are properly excluded

### 2. Context Token Savings (Priority: Critical)
- Result limits are strictly enforced
- Context lines are only returned when requested
- File pattern filtering reduces search space
- Caching eliminates redundant indexing

### 3. Multi-Language Accuracy (Priority: High)
- All 6 languages parse correctly
- Fallback parser works when tree-sitter unavailable
- Symbols extracted with correct line/column positions
- Nested structures handled properly

### 4. Robustness (Priority: High)
- Invalid inputs handled gracefully
- Network errors (cache) don't crash
- Syntax errors in source code handled
- Concurrent access thread-safe

### 5. Performance (Priority: Medium)
- Small codebase: < 500ms
- Medium codebase: < 2s
- Large codebase: < 60s
- Search latency: < 2s

---

## Success Criteria

✅ All 142 tests pass on CI (Ubuntu + macOS, Python 3.10-3.12)
✅ Test coverage >= 80% across all modules
✅ Performance tests complete within timeout limits
✅ Property tests run 200+ examples each
✅ Token savings claims verified (70-85% reduction demonstrated)
✅ Zero flaky tests (all deterministic)

---

## Implementation Order

1. Create fixtures directory structure with sample code files
2. Implement unit tests (cache, parsers, indexer, searcher)
3. Add Hypothesis property tests for invariants
4. Implement integration tests for MCP tools + workflows
5. Create performance benchmarks with timeout guards
6. Add token efficiency tests to verify savings claims
7. Configure CI pipeline with multi-OS multi-Python matrix
8. Document test execution in CONTRIBUTING.md
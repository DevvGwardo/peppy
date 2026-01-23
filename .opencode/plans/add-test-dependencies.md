# Plan: Add Test Dependencies to pyproject.toml

## Overview
Add missing test dependencies required by the comprehensive test plan to `pyproject.toml`.

## Changes Required

### File: `pyproject.toml`
**Location**: Lines 20-26
**Change**: Add three new dependencies to the `dev` optional dependencies

#### Current `[project.optional-dependencies] dev` section:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

#### New `[project.optional-dependencies] dev` section:
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

## Dependencies Being Added

### 1. `pytest-timeout>=2.1.0`
**Purpose**: Add timeout guards for performance tests
**Usage**: Prevent CI jobs from hanging on long-running tests
**Example**:
```python
@pytest.mark.timeout(60)
def test_large_codebase():
    # Will fail after 60 seconds
```

### 2. `pytest-mock>=3.11.0`
**Purpose**: Mock objects, classes, functions in tests
**Usage**: Isolate tests from external dependencies
**Example**:
```python
def test_cache_write_failure(mocker):
    mocker.patch('builtins.open', side_effect=OSError)
    result = cache.set(path, data)
    assert result is None  # Graceful failure
```

### 3. `hypothesis>=6.80.0`
**Purpose**: Property-based testing framework
**Usage**: Generate hundreds of test cases automatically
**Example**:
```python
@given(st.text())
def test_cache_key_deterministic(path):
    key1 = cache._get_cache_key(Path(path))
    key2 = cache._get_cache_key(Path(path))
    assert key1 == key2
```

## Rationale

All three dependencies are standard, well-maintained packages in the Python testing ecosystem:

- **pytest-timeout**: 1.5M+ downloads/month, stable
- **pytest-mock**: 2M+ downloads/month, stable
- **hypothesis**: 1.3M+ downloads/month, stable, recommended by pytest

## Installation After Change

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
pip list | grep -E "pytest|hypothesis"
```

## Impact Analysis

### Positive Impacts
- Enables comprehensive test suite implementation
- Standard testing tools in the ecosystem
- Minimal overhead (small packages)

### Downsides
- None - all are lightweight packages

### Compatibility
- Python 3.10+ (matches project requirement)
- Compatible with existing pytest ecosystem

## Confirmation Needed

Do you approve adding these three dependencies to `pyproject.toml`?

## Next Steps (After Approval)

1. Edit `pyproject.toml` to add the three dependencies
2. Run `pip install -e ".[dev]"` to install them
3. Verify with `pytest --version` and `python -c "import hypothesis"`

---
**Status**: Awaiting user approval to proceed with edit
# Peppy Interface Documentation

The `PeppyInterface` class provides a high-level, unified API for codebase indexing and search operations. It's designed for easy integration with workflow orchestration tools like Siggy.

## Quick Start

```python
from peppy import PeppyInterface

# Create interface
peppy = PeppyInterface()

# Index a codebase
stats = peppy.index("/path/to/project")
print(f"Indexed {stats.total_files} files with {stats.total_symbols} symbols")

# Find symbols
results = peppy.find_symbols(".*Service", symbol_type="class")
for r in results:
    print(f"{r.name} at {r.to_location()}")

# Search code
usages = peppy.find_usages("AuthService")
for u in usages:
    print(f"{u.to_location()}: {u.content}")
```

## Core Methods

### Indexing

```python
# Index a codebase (cached by default)
stats = peppy.index("/path/to/project")

# Force re-indexing
stats = peppy.index("/path/to/project", force=True)

# Set default codebase for subsequent operations
peppy.set_codebase("/path/to/project")

# Check if indexed
if peppy.is_indexed():
    print("Ready to search!")
```

### Symbol Search

```python
# Find any symbols matching a pattern
results = peppy.find_symbols(".*Controller")

# Filter by symbol type
classes = peppy.find_symbols(".*", symbol_type="class")
functions = peppy.find_symbols("handle.*", symbol_type="function")
methods = peppy.find_symbols("get.*", symbol_type="method")

# Filter by file pattern
ts_classes = peppy.find_symbols(".*", symbol_type="class", file_pattern="*.ts")

# Convenience methods
classes = peppy.find_classes(".*Service")
functions = peppy.find_functions("init.*")
methods = peppy.find_methods("handle.*")

# Find exact definition
definition = peppy.find_definition("UserService")
if definition:
    print(f"Found at {definition.to_location()}")
```

### Grep (Content Search)

```python
# Basic grep
results = peppy.grep("TODO")

# With context lines
results = peppy.grep("import.*from", context=2)

# Filter by file pattern
results = peppy.grep("console.log", file_pattern="*.js")

# Find usages of a symbol
usages = peppy.find_usages("myFunction")
```

### File Operations

```python
# Get all symbols in a file
symbols = peppy.get_file_symbols("/path/to/file.py")

# Get formatted structure overview
structure = peppy.get_file_structure("/path/to/file.py")
print(structure)
```

### Statistics & Overview

```python
# Get detailed statistics
stats = peppy.get_stats()
print(f"Files: {stats.total_files}")
print(f"Symbols: {stats.total_symbols}")
print(f"Types: {stats.symbol_types}")

# Get compact summary
print(stats.summary())

# Get full overview (great for planning)
overview = peppy.get_overview()
print(overview)
```

## Siggy Workflow Integration

The interface provides specialized methods for each Siggy workflow phase:

### Planning Phase

```python
# Get comprehensive planning context
planning_data = peppy.for_planning(
    focus_patterns=["auth", "user", "login"]
)

# Returns:
# {
#     "overview": { ... codebase stats ... },
#     "key_classes": [ { name, location }, ... ],
#     "key_functions": [ { name, location }, ... ],
#     "focus_results": {
#         "auth": { "symbols": [...], "usages": [...] },
#         ...
#     }
# }
```

### Execution Phase

```python
# Get precise location info for making changes
execution_data = peppy.for_execution("UserService")

# Returns:
# {
#     "target": "UserService",
#     "definition": { name, type, file, line, column },
#     "usages": [ ... ],
#     "usage_count": 15,
#     "file_structure": [ ... symbols in the file ... ]
# }
```

### Verification Phase

```python
# Verify that expected changes were made
verification_data = peppy.for_verification(
    expected_symbols=["NewService", "newMethod", "updatedFunction"]
)

# Returns:
# {
#     "stats": { ... updated codebase stats ... },
#     "verification_results": {
#         "NewService": { "found": true, "location": "..." },
#         "newMethod": { "found": true, "location": "..." },
#         ...
#     }
# }
```

## Data Classes

### SearchResult

```python
@dataclass
class SearchResult:
    name: str       # Symbol name
    type: str       # function, class, method, variable, interface, type
    file: str       # File path
    line: int       # Line number
    column: int     # Column number
    context: str    # Optional context

    def to_location(self) -> str:
        """Returns 'file:line' string"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
```

### GrepResult

```python
@dataclass
class GrepResult:
    file: str                    # File path
    line: int                    # Line number
    content: str                 # Matching line content
    context_before: List[str]    # Lines before match
    context_after: List[str]     # Lines after match

    def to_location(self) -> str:
        """Returns 'file:line' string"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
```

### CodebaseStats

```python
@dataclass
class CodebaseStats:
    root: str                        # Codebase root path
    total_files: int                 # Number of indexed files
    total_symbols: int               # Total symbol count
    symbol_types: Dict[str, int]     # Count by symbol type
    file_extensions: Dict[str, int]  # Count by file extension

    def summary(self) -> str:
        """Returns compact summary string"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
```

## MCP Prompts

When running as an MCP server, Peppy exposes prompts for Siggy integration:

| Prompt | Description | Arguments |
|--------|-------------|-----------|
| `peppy-planning` | Get planning phase context | `codebase_path`, `focus_patterns` (optional) |
| `peppy-execution` | Get execution phase context | `codebase_path`, `target` |
| `peppy-verification` | Verify changes | `codebase_path`, `expected_symbols` (optional) |
| `peppy-overview` | Get codebase overview | `codebase_path` |

## Best Practices

### 1. Index Once, Search Many Times

```python
peppy = PeppyInterface()
peppy.index("/project")  # Cache persists

# Multiple searches use cached index
classes = peppy.find_classes()
functions = peppy.find_functions()
usages = peppy.find_usages("something")
```

### 2. Use Specific Filters

```python
# More efficient - filter by type and pattern
results = peppy.find_symbols("Auth.*", symbol_type="class", file_pattern="*.ts")

# Less efficient - search everything
results = peppy.find_symbols(".*")
```

### 3. Use Workflow Helpers for Siggy

```python
# Instead of making multiple calls:
stats = peppy.get_stats()
classes = peppy.find_classes()
functions = peppy.find_functions("main")

# Use the workflow helper:
planning_data = peppy.for_planning()
# Gets all the above in one structured result
```

## See Also

- [Siggy Integration Guide](SIGGY_INTEGRATION.md)
- [Siggy v1.10+ Compatibility](SIGGY_V1.10_COMPATIBILITY.md)
- [Main README](../README.md)

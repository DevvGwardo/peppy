# Peppy - Codebase Indexing Plugin

## Overview
Peppy is a comprehensive codebase indexing and search plugin for Claude Code. It provides efficient code navigation, symbol search, and intelligent grep capabilities.

## Features Implemented

### 1. Core Indexing Engine
- **Multi-language support** using tree-sitter parsers (Python, JavaScript/TypeScript, Go, Rust, Java)
- **Parallel indexing** for fast processing of large codebases
- **Smart filtering** with .gitignore support and common directory exclusions
- **Persistent caching** for instant subsequent searches

### 2. Search Capabilities
- **Symbol search**: Find functions, classes, variables, etc. by name
- **Grep functionality**: Search code content with regex support
- **File filtering**: Filter by file patterns (e.g., "*.py")
- **Context display**: Show surrounding lines for grep results

### 3. MCP Server Integration
- **Seamless Claude Code integration** via Model Context Protocol
- **6 powerful tools** exposed:
  - `index_codebase`: Index a directory
  - `search_symbols`: Find code symbols
  - `grep_code`: Search code content
  - `get_file_symbols`: List symbols in a file
  - `get_statistics`: Get codebase stats
  - `clear_cache`: Manage index cache
- **4 MCP prompts** for Siggy workflow integration:
  - `peppy-planning`: Planning phase context
  - `peppy-execution`: Execution phase context
  - `peppy-verification`: Verification phase checks
  - `peppy-overview`: Codebase overview

### 4. Performance Features
- **Intelligent caching**: Reuse indices across sessions
- **Parallel processing**: Fast indexing with thread pool
- **Lazy loading**: Only parse files when needed
- **Memory efficient**: Stream-based file processing

### 5. PeppyInterface - High-Level API
- **Unified interface** for all indexing and search operations
- **Siggy workflow helpers**: `for_planning()`, `for_execution()`, `for_verification()`
- **Data classes**: `SearchResult`, `GrepResult`, `CodebaseStats`
- **Convenience methods**: `find_classes()`, `find_functions()`, `find_usages()`
- **Method chaining** support for fluent API usage

## Architecture

```
peppy/
├── __init__.py          # Package initialization & exports
├── server.py            # MCP server with tools and prompts
├── indexer.py           # Core indexing engine
├── searcher.py          # Search and grep functionality
├── parsers.py           # Tree-sitter parser utilities
├── cache.py             # Index caching system
└── interface.py         # High-level PeppyInterface API
```

## Usage

### As MCP Server (Recommended)
Add to Claude Code MCP settings and use tools directly in conversations.

### Using PeppyInterface (Python Library)
```python
from peppy import PeppyInterface

peppy = PeppyInterface()
peppy.index("/path/to/code")

# Find symbols
classes = peppy.find_classes(".*Service")
definition = peppy.find_definition("UserService")

# Grep code
usages = peppy.find_usages("myFunction")

# Siggy workflow integration
planning = peppy.for_planning(focus_patterns=["auth", "user"])
execution = peppy.for_execution("UserService")
verification = peppy.for_verification(expected_symbols=["NewFeature"])
```

## Siggy Integration

Peppy provides deep integration with [Siggy](https://github.com/DevvGwardo/siggy-plugin):

- **Planning Phase**: Use `for_planning()` or `peppy-planning` prompt
- **Execution Phase**: Use `for_execution()` or `peppy-execution` prompt
- **Verification Phase**: Use `for_verification()` or `peppy-verification` prompt

See [docs/SIGGY_INTEGRATION.md](docs/SIGGY_INTEGRATION.md) for complete guide.

## Documentation

- [Interface Documentation](docs/INTERFACE.md) - PeppyInterface API guide
- [Siggy Integration](docs/SIGGY_INTEGRATION.md) - Workflow orchestration guide

## Next Steps
- [ ] Add support for more languages (C++, Ruby, PHP, etc.)
- [ ] Implement incremental indexing for faster updates
- [ ] Add LSP-like features (go-to-definition, find references)
- [ ] Web UI for browsing indexed codebases
- [ ] Integration with other editors (VS Code, Vim, etc.)

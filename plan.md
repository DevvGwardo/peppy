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

### 4. Performance Features
- **Intelligent caching**: Reuse indices across sessions
- **Parallel processing**: Fast indexing with thread pool
- **Lazy loading**: Only parse files when needed
- **Memory efficient**: Stream-based file processing

## Architecture

```
peppy/
├── __init__.py          # Package initialization
├── server.py            # MCP server implementation
├── indexer.py           # Core indexing engine
├── searcher.py          # Search and grep functionality
├── parsers.py           # Tree-sitter parser utilities
└── cache.py             # Index caching system
```

## Usage

### As MCP Server (Recommended)
Add to Claude Code MCP settings and use tools directly in conversations.

### As Python Library
```python
from peppy import CodebaseIndexer, CodebaseSearcher

indexer = CodebaseIndexer()
index = indexer.index_codebase("/path/to/code")

searcher = CodebaseSearcher()
results = searcher.search_symbols("/path/to/code", "MyClass")
```

## Next Steps
- [ ] Add support for more languages (C++, Ruby, PHP, etc.)
- [ ] Implement incremental indexing for faster updates
- [ ] Add LSP-like features (go-to-definition, find references)
- [ ] Web UI for browsing indexed codebases
- [ ] Integration with other editors (VS Code, Vim, etc.)

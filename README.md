# Peppy - Codebase Indexing Plugin for Claude Code

Peppy is a powerful codebase indexing and search plugin designed to work seamlessly with Claude Code. It provides efficient code navigation, symbol search, and intelligent grep capabilities across your entire codebase.

## Features

- **🚀 Fast Indexing**: Quickly index large codebases with intelligent caching
- **🔍 Smart Search**: Find functions, classes, variables, and more across multiple languages
- **🌳 Tree-sitter Parsing**: Accurate code understanding using tree-sitter parsers
- **📁 Gitignore Support**: Respects .gitignore patterns automatically
- **🔌 MCP Integration**: Works as an MCP server for Claude Code

## Supported Languages

- Python
- JavaScript/TypeScript
- Go
- Rust
- Java
- And more coming soon!

## Installation

```bash
pip install -e .
```

## Usage with Claude Code

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "peppy": {
      "command": "python",
      "args": ["-m", "peppy.server"]
    }
  }
}
```

## Available Tools

### 1. `index_codebase`
Index a directory to enable fast searching.

**Parameters:**
- `path` (string): Path to the codebase root
- `force_reindex` (boolean, optional): Force re-indexing even if cache exists

### 2. `search_symbols`
Search for code symbols (functions, classes, variables) across the indexed codebase.

**Parameters:**
- `query` (string): Search query (supports regex)
- `symbol_type` (string, optional): Filter by type (function, class, variable, etc.)
- `file_pattern` (string, optional): Filter by file pattern (e.g., "*.py")

### 3. `grep_code`
Perform efficient grep search across the codebase.

**Parameters:**
- `pattern` (string): Search pattern (regex supported)
- `file_pattern` (string, optional): File glob pattern
- `context_lines` (integer, optional): Number of context lines to show

### 4. `get_file_symbols`
Get all symbols defined in a specific file.

**Parameters:**
- `file_path` (string): Path to the file

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```

## How It Works

1. **Indexing**: Peppy scans your codebase, parses files using tree-sitter, and extracts symbols
2. **Caching**: Index data is cached for fast subsequent searches
3. **Search**: Fast lookups using indexed data with optional regex filtering
4. **MCP Protocol**: Exposes functionality as tools that Claude Code can use

## License

MIT

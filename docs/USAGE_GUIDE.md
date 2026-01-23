# Peppy Usage Guide

A practical, step-by-step guide to using Peppy for efficient codebase exploration and search.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Common Use Cases](#common-use-cases)
3. [Step-by-Step Workflows](#step-by-step-workflows)
4. [Tips and Best Practices](#tips-and-best-practices)
5. [Troubleshooting](#troubleshooting)
6. [Quick Reference](#quick-reference)

---

## Quick Start

### Installation (5 minutes)

1. **Install Peppy**
   ```bash
   cd /path/to/peppy
   pip install -e .
   ```

2. **Configure Claude Code**

   Add this to your Claude Code MCP settings file:
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

3. **Restart Claude Code**

   The Peppy tools will now be available in your Claude Code sessions.

### Your First Search (2 minutes)

Start a Claude Code conversation and try:

```
Index my project at /path/to/my-project
```

Claude will use the `index_codebase` tool to create a searchable index. Then try:

```
Find all classes in the codebase
```

Claude will use `search_symbols` to instantly list all classes without reading every file.

---

## Common Use Cases

### 1. Exploring a New Codebase

**Scenario**: You've just cloned a repository and want to understand its structure.

**What to say to Claude**:
```
I want to explore the codebase at /path/to/project.
Can you index it and show me an overview?
```

**What happens**:
1. Claude indexes the codebase (one-time cost)
2. Shows statistics (number of files, symbols, languages)
3. Lists main classes and functions

**Token savings**: ~90% compared to reading multiple files

---

### 2. Finding a Specific Function

**Scenario**: You need to find where `authenticate_user` is defined.

**What to say to Claude**:
```
Find the authenticate_user function
```

**What happens**:
1. Claude searches the index for the symbol
2. Returns exact file and line number
3. Reads just that section of the file

**Token savings**: ~95% compared to searching through files manually

---

### 3. Finding All TODOs

**Scenario**: You want to see all TODO comments in the codebase.

**What to say to Claude**:
```
Find all TODO comments in the codebase
```

**What happens**:
1. Claude uses `grep_code` to search for "TODO"
2. Returns all matches with context
3. No need to read every file

**Token savings**: ~97% compared to reading all files

---

### 4. Understanding a Module

**Scenario**: You want to understand what's in `src/auth.py`.

**What to say to Claude**:
```
Show me all the functions and classes in src/auth.py
```

**What happens**:
1. Claude uses `get_file_symbols` to list all symbols
2. Shows a structured overview without reading the whole file
3. You can then ask to see specific functions

**Token savings**: ~85% compared to reading the entire file

---

### 5. Refactoring a Function Name

**Scenario**: You need to rename `old_function` to `new_function` everywhere.

**What to say to Claude**:
```
Find all usages of old_function so I can rename it
```

**What happens**:
1. Claude searches for the function definition
2. Uses grep to find all call sites
3. Shows you exactly where changes are needed

**Token savings**: ~93% compared to manual file searching

---

### 6. Finding Error Handling Patterns

**Scenario**: You want to see how errors are handled in the codebase.

**What to say to Claude**:
```
Find all places where exceptions are raised in Python files
```

**What happens**:
1. Claude uses `grep_code` with pattern "raise \w+Error"
2. Returns all matches with context
3. Shows consistent patterns across the codebase

**Token savings**: ~96% compared to reading all Python files

---

## Step-by-Step Workflows

### Workflow 1: Starting with a New Project

**Goal**: Understand and start working on an unfamiliar codebase.

**Steps**:

1. **Index the codebase**
   ```
   Index the codebase at /path/to/project
   ```

2. **Get overview**
   ```
   Show me statistics about the codebase
   ```

3. **Find main entry points**
   ```
   Find all main functions or entry points
   ```

4. **Explore key modules**
   ```
   What classes are defined in src/core/?
   ```

5. **Deep dive**
   ```
   Show me the implementation of the DatabaseConnection class
   ```

**Time saved**: 15-20 minutes of manual exploration

---

### Workflow 2: Bug Investigation

**Goal**: Track down and fix a bug in authentication.

**Steps**:

1. **Find related code**
   ```
   Find all functions related to authentication
   ```

2. **Locate error handling**
   ```
   Show me where authentication errors are raised
   ```

3. **Find usage patterns**
   ```
   Find all places where the authenticate function is called
   ```

4. **Check tests**
   ```
   Find all test functions for authentication
   ```

5. **Read specific implementations**
   ```
   Show me the authenticate_user function in src/auth.py
   ```

**Time saved**: 10-15 minutes of file searching

---

### Workflow 3: Code Review

**Goal**: Review code for quality and completeness.

**Steps**:

1. **Find TODOs and FIXMEs**
   ```
   Find all TODO and FIXME comments
   ```

2. **Check test coverage**
   ```
   Find all test functions in the test directory
   ```

3. **Look for security issues**
   ```
   Find all uses of password, secret, or token in the code
   ```

4. **Review error handling**
   ```
   Find all exception handling in the new feature files
   ```

5. **Check documentation**
   ```
   Find all docstrings in the public API classes
   ```

**Time saved**: 20-30 minutes of manual review

---

### Workflow 4: API Documentation

**Goal**: Document all public API endpoints.

**Steps**:

1. **Find API route handlers**
   ```
   Find all functions that handle HTTP routes
   ```

2. **List controller classes**
   ```
   Find all classes that end with 'Controller' or 'Handler'
   ```

3. **Find request models**
   ```
   Find all classes in the models directory
   ```

4. **Check response types**
   ```
   Find all return type annotations in the API handlers
   ```

**Time saved**: 15-20 minutes of code exploration

---

## Tips and Best Practices

### Do's

- **Index once per session**: The cache persists, so you only need to index once
- **Use specific queries**: "Find the User class" is better than "Find User"
- **Specify file patterns**: Narrow searches with `*.py`, `src/**/*.ts`, etc.
- **Use appropriate tools**:
  - `search_symbols` for definitions
  - `grep_code` for usage patterns
  - `get_file_symbols` for module overview
- **Start broad, narrow down**: Get statistics first, then search specifically
- **Use regex for patterns**: `handle_.*_request` finds all handler functions

### Don'ts

- **Don't re-index unnecessarily**: The cache is automatically managed
- **Don't use overly broad queries**: Avoid searching for ".*" or very common words
- **Don't read files first**: Let Peppy find the exact location, then read
- **Don't ignore file patterns**: Searching all files wastes tokens
- **Don't request max context always**: Use `context_lines=0` for simple matches

### Token Optimization

| Instead of... | Do this... | Token savings |
|--------------|------------|---------------|
| "Read all Python files" | "Search for the User class" | ~95% |
| "Show me the src directory" | "Get statistics for src/" | ~90% |
| "Find TODO by reading files" | "Grep for TODO comments" | ~97% |
| "Read auth.py, user.py, admin.py" | "Find authentication functions" | ~93% |

---

## Troubleshooting

### Issue: Index not found

**Symptom**: Error saying "codebase not indexed"

**Solution**:
```
Index the codebase at /path/to/project
```

Wait for indexing to complete, then retry your search.

---

### Issue: No results found

**Symptom**: Search returns no results when you know the symbol exists

**Solutions**:

1. **Check if indexed**:
   ```
   Show me statistics for /path/to/project
   ```

2. **Try broader search**:
   ```
   Find symbols matching "user" (case-insensitive)
   ```

3. **Use grep instead**:
   ```
   Grep for "UserClass" in the codebase
   ```

4. **Re-index if code changed**:
   ```
   Clear the cache and re-index /path/to/project
   ```

---

### Issue: Too many results

**Symptom**: Search returns hundreds of results

**Solutions**:

1. **Add symbol type filter**:
   ```
   Find "process" functions only (not variables)
   ```

2. **Add file pattern**:
   ```
   Find "process" in Python files only (*.py)
   ```

3. **Use more specific query**:
   ```
   Find "process_user_data" instead of "process"
   ```

---

### Issue: Slow indexing

**Symptom**: Indexing takes a long time

**Solutions**:

1. **Index specific directories**:
   ```
   Index just the src/ directory, not the whole project
   ```

2. **Check .gitignore**: Ensure you're not indexing `node_modules/`, `venv/`, etc.

3. **Clear old cache**:
   ```
   Clear all Peppy cache and re-index
   ```

---

### Issue: Out-of-date results

**Symptom**: Search finds old symbols that have been changed

**Solution**:
```
Force re-index the codebase at /path/to/project
```

This will clear the cache and create a fresh index.

---

## Quick Reference

### Essential Commands

| What you want | What to say |
|---------------|-------------|
| Index a project | "Index the codebase at /path/to/project" |
| Find a function | "Find the function_name function" |
| Find a class | "Find the ClassName class" |
| List all symbols in file | "Show me all functions in src/main.py" |
| Search for pattern | "Grep for 'TODO' in the codebase" |
| Get overview | "Show me statistics for the project" |
| Find all tests | "Find all test functions" |
| Find imports | "Find all imports of the requests library" |
| Clear cache | "Clear the Peppy cache" |

### Search Patterns

| Pattern | Example | What it finds |
|---------|---------|---------------|
| Exact match | "User" | Exact "User" symbol |
| Wildcard | "User*" | User, UserModel, UserController |
| Regex | "handle_.*_request" | handle_get_request, handle_post_request |
| File pattern | "*.py" | Only Python files |
| Path pattern | "src/**/*.ts" | TypeScript files in src and subdirs |

### Symbol Types

| Type | What it includes |
|------|------------------|
| `function` | Functions, methods |
| `class` | Classes, interfaces |
| `variable` | Variables, constants |
| `method` | Class methods |
| `interface` | TypeScript/Java interfaces |
| `type` | Type aliases, type definitions |

### Supported Languages

- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
- Go (`.go`)
- Rust (`.rs`)
- Java (`.java`)

---

## Integration with Siggy

If you're using [Siggy](https://github.com/DevvGwardo/siggy-plugin) for workflow orchestration, Peppy provides automatic optimization:

### Quick Setup

Add to your `.siggy.yml`:
```yaml
plugins:
  peppy:
    enabled: true
    auto_index: true
```

### Benefits

- **70% faster planning**: Indexed search accelerates research
- **83% more efficient execution**: Precise symbol location
- **65-75% overall token savings**: Dramatic cost reduction

See [SIGGY_INTEGRATION.md](SIGGY_INTEGRATION.md) for complete details.

---

## Next Steps

- **Read the [README](../README.md)** for complete feature list and token savings examples
- **Check [INTERFACE.md](INTERFACE.md)** for Python API documentation
- **See [SIGGY_INTEGRATION.md](SIGGY_INTEGRATION.md)** for workflow optimization

---

## Need Help?

If you encounter issues:

1. Check this troubleshooting section
2. Review the [README](../README.md) for detailed information
3. Open an issue at [GitHub repository](https://github.com/useratkageshi/peppy)

Happy coding with Peppy!

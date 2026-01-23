# Integrating Peppy with Siggy

## Overview

**Peppy** (codebase indexing) + **Siggy** (workflow orchestration) = A powerful combination for complex coding tasks with massive token savings.

### What Each Plugin Does

| Plugin | Purpose | Key Features |
|--------|---------|--------------|
| **Peppy** | Codebase Intelligence | Fast symbol search, indexed grep, multi-language parsing, persistent cache |
| **Siggy** | Workflow Orchestration | Task planning, persistent execution, automated verification, event logging |

### Why Combine Them?

**Siggy's workflow phases can use Peppy's intelligence to be faster and more token-efficient:**

1. **Planning Phase**: Siggy's Planner uses Glob/Grep/Read to research codebases
   - ✅ With Peppy: Use indexed search for instant symbol lookup (90%+ token savings)

2. **Execution Phase**: Siggy's Executors need to find code locations
   - ✅ With Peppy: Precise location finding without reading multiple files

3. **Verification Phase**: Siggy's Verifier checks completed work
   - ✅ With Peppy: Quick structure validation and symbol checks

## Integration Approaches

### Approach 1: MCP Server Integration (Recommended)

Run Peppy as an MCP server alongside Siggy, so Siggy's agents can use Peppy's tools.

#### Setup

**1. Install both plugins:**
```bash
# Install Peppy
cd /path/to/peppy
pip install -e .

# Install Siggy (assuming you have it)
cd /path/to/siggy-plugin
# Follow Siggy's installation instructions
```

**2. Configure Claude Code MCP settings:**
```json
{
  "mcpServers": {
    "peppy": {
      "command": "python",
      "args": ["-m", "peppy.server"],
      "cwd": "/path/to/peppy"
    }
  }
}
```

**3. Ensure Siggy is configured:**
```bash
# In your project directory
/siggy:init
```

#### Usage Workflow

**Traditional Siggy Workflow (Without Peppy):**
```
/siggy "Add authentication to the API"

Planning Phase:
  - Glob for route files (500 tokens)
  - Read multiple files to understand structure (5,000 tokens)
  - Grep for existing auth patterns (2,000 tokens)
  - Create PROMPT.md (1,000 tokens)
  Total: ~8,500 tokens

Execution Phase:
  - Read files again for each task (3,000 tokens per task × 5 tasks = 15,000)
  - Make changes
  Total: ~15,000 tokens

Total Workflow: ~23,500 tokens
```

**Enhanced Workflow (With Peppy):**
```
Step 1: Index the codebase first
  index_codebase(path="/path/to/project")
  Cost: ~2,000 tokens (one-time)

Step 2: Run Siggy workflow
  /siggy "Add authentication to the API"

Planning Phase (Peppy-enhanced):
  - get_statistics() to understand structure (300 tokens)
  - search_symbols(query=".*Route", symbol_type="class") (400 tokens)
  - search_symbols(query="auth", use_regex=true) (300 tokens)
  - grep_code(pattern="middleware", file_pattern="*.ts") (600 tokens)
  - Create PROMPT.md (1,000 tokens)
  Total: ~2,600 tokens (70% savings!)

Execution Phase (Peppy-enhanced):
  - search_symbols to find exact locations (400 tokens per task × 5 = 2,000)
  - Make changes
  Total: ~2,000 tokens (87% savings!)

Total Workflow: ~6,600 tokens (72% overall savings!)
```

### Approach 2: Enhanced Siggy Agents

Create custom Siggy agents that are Peppy-aware and use Peppy tools by default.

#### Create Peppy-Enhanced Planner

Create a custom planner agent that uses Peppy for research:

**File: `.siggy/agents/peppy-planner.md`**
```markdown
# Peppy-Enhanced Planner Agent

You are an intelligent planning agent that uses Peppy for efficient codebase research.

## Your Mission
Research the codebase efficiently using Peppy's indexed search, then create a detailed PROMPT.md with discrete tasks.

## Tools Available
- **Peppy Tools** (use these FIRST):
  - index_codebase: Index if not already done
  - get_statistics: Understand codebase structure
  - search_symbols: Find functions, classes, variables
  - grep_code: Search code content with context
  - get_file_symbols: List symbols in specific files

- **Standard Tools** (use for actual reading):
  - Read: Read specific files after Peppy finds them
  - Glob: Only if Peppy search doesn't work
  - Grep: Only for non-indexed patterns

## Research Workflow

1. **Check Index**
   - Try get_statistics(codebase_path) first
   - If fails, run index_codebase(path)

2. **Understand Structure**
   - get_statistics() to see file counts, symbol types
   - Identify key patterns (e.g., "50% TypeScript, 200 classes, 500 functions")

3. **Find Relevant Code**
   - Use search_symbols() to find key classes/functions
   - Use grep_code() to find usage patterns
   - Use get_file_symbols() to understand specific files

4. **Deep Dive**
   - Use Read tool to examine specific files Peppy identified
   - Only read what's necessary based on Peppy results

5. **Create Plan**
   - Generate PROMPT.md with specific TASK_N entries
   - Include exact file paths from Peppy results
   - Add verification commands

## Example Research Flow

User Task: "Add rate limiting to API endpoints"

Step 1: Check/Index
→ get_statistics(codebase_path="/project")
  Result: 300 files, 150 TS files, 45 classes

Step 2: Find API Structure
→ search_symbols(query=".*Router|.*Controller", symbol_type="class", file_pattern="*.ts")
  Result: Found ApiRouter (src/routes/api.ts:15), UserController (src/controllers/user.ts:10)

Step 3: Find Existing Middleware
→ search_symbols(query="middleware", file_pattern="*.ts")
  Result: Found authMiddleware, loggingMiddleware in src/middleware/

Step 4: Find Rate Limiting Patterns
→ grep_code(pattern="rate.?limit", file_pattern="*.ts", context_lines=2)
  Result: No existing rate limiting found

Step 5: Read Specific Files
→ Read src/routes/api.ts (lines 10-30 where ApiRouter is defined)
→ Read src/middleware/auth.ts (to understand middleware pattern)

Step 6: Create PROMPT.md
Based on Peppy findings, create tasks:
- TASK_1: Create rate limit middleware (src/middleware/rateLimit.ts)
- TASK_2: Add rate limit to ApiRouter (src/routes/api.ts:20)
- etc.

## Output Format

Create PROMPT.md following Siggy's standard format:
```
# Task: Add Rate Limiting to API

## Problem Summary
[Based on Peppy research findings...]

## TASK_1: Create Rate Limit Middleware
File: src/middleware/rateLimit.ts
Create new rate limiting middleware following the pattern in src/middleware/auth.ts
...

[Additional tasks...]

## Success Criteria
- Rate limiting applied to all API endpoints
- Middleware follows existing patterns
- Tests pass

## Commands to Verify
- npm run build
- npm test
```
```

#### Create Peppy-Enhanced Executor

**File: `.siggy/agents/peppy-executor.md`**
```markdown
# Peppy-Enhanced Executor Agent

You execute a single task efficiently using Peppy for navigation.

## Before Making Changes

1. **Find Exact Locations**
   - search_symbols(query="TargetClass", symbol_type="class")
   - get_file_symbols(file_path="target/file.ts")

2. **Understand Context**
   - grep_code(pattern="related_pattern", context_lines=3)
   - Read only the relevant sections

3. **Make Changes**
   - Use Edit/Write tools for precise modifications

4. **Verify**
   - Run verification commands from PROMPT.md

## Example Execution

TASK_1: Add logout method to AuthService

Step 1: Find AuthService
→ search_symbols(query="AuthService", symbol_type="class")
  Result: src/services/auth.ts:15

Step 2: Get file structure
→ get_file_symbols(file_path="src/services/auth.ts")
  Result: Methods: login (line 20), register (line 45), verifyToken (line 60)

Step 3: Read specific section
→ Read src/services/auth.ts:15-70

Step 4: Make change
→ Edit src/services/auth.ts (add logout method after verifyToken)

Step 5: Verify
→ Bash: npm run build
→ Bash: npm test

Step 6: Report
→ TASK_COMPLETE
```

### Approach 3: Pre-Processing Integration

Add Peppy indexing as a standard pre-step in your Siggy workflows.

#### Create a Wrapper Script

**File: `peppy-siggy-workflow.sh`**
```bash
#!/bin/bash
# Combined Peppy + Siggy workflow

set -e

PROJECT_DIR="${1:-.}"
TASK="${2:-}"

if [ -z "$TASK" ]; then
    echo "Usage: $0 <project_dir> <task>"
    exit 1
fi

echo "🔍 Step 1: Indexing codebase with Peppy..."
claude-code --prompt "index_codebase(path='$PROJECT_DIR')"

echo "📋 Step 2: Running Siggy workflow..."
claude-code --prompt "/siggy $TASK"

echo "✅ Workflow complete!"
```

Usage:
```bash
./peppy-siggy-workflow.sh /path/to/project "Add authentication to API"
```

## Optimization Strategies

### 1. Index Once Per Session

```bash
# At the start of your coding session
index_codebase(path="/project")

# Then run multiple Siggy workflows
/siggy "Task 1"
/siggy "Task 2"
# Index is reused automatically
```

### 2. Use Peppy in PROMPT.md

Include Peppy queries in your manual PROMPT.md files:

```markdown
## TASK_1: Refactor UserService

**Pre-task Research:**
- search_symbols(query="UserService", symbol_type="class")
- get_file_symbols(file_path="src/services/user.ts")
- grep_code(pattern="UserService\.", max_results=20)

**Changes:**
[Based on Peppy findings...]
```

### 3. Create Peppy-First Templates

Create Siggy templates that always use Peppy:

**File: `.siggy/templates/peppy-research.md`**
```markdown
# Research Template (Peppy-First)

## Codebase Overview
→ get_statistics(codebase_path)

## Find Relevant Symbols
→ search_symbols(query="{{SEARCH_PATTERN}}")

## Find Usage Patterns
→ grep_code(pattern="{{GREP_PATTERN}}", context_lines=2)

## Deep Dive
→ Read {{FILE_PATH}} (identified by Peppy)
```

## Token Savings Analysis

### Real-World Example: "Add API Endpoint"

**Standard Siggy (No Peppy):**
- Planning: ~8,000 tokens (extensive globbing and reading)
- Execution: ~12,000 tokens (re-reading files)
- Verification: ~3,000 tokens
- **Total: ~23,000 tokens**

**Peppy + Siggy:**
- Indexing (one-time): ~2,000 tokens
- Planning: ~2,500 tokens (Peppy searches)
- Execution: ~2,000 tokens (targeted reads)
- Verification: ~1,500 tokens
- **Total: ~8,000 tokens (65% savings!)**

### Per-Phase Savings

| Phase | Without Peppy | With Peppy | Savings |
|-------|---------------|------------|---------|
| Planning | 8,000 | 2,500 | 69% |
| Execution | 12,000 | 2,000 | 83% |
| Verification | 3,000 | 1,500 | 50% |
| **Total** | **23,000** | **8,000** | **65%** |

## Best Practices

### ✅ Do's

1. **Index at session start**
   ```
   # First thing in a new session
   index_codebase(path="/project")
   ```

2. **Use Peppy for all research**
   - Planning phase: Use search_symbols and grep_code
   - Execution: Use get_file_symbols to understand structure
   - Verification: Use search_symbols to verify additions

3. **Combine Peppy with Read strategically**
   ```
   # Peppy finds it, Read examines it
   search_symbols(query="AuthService") → src/auth.ts:15
   Read src/auth.ts:10-50  # Only read the relevant section
   ```

4. **Share index across tasks**
   - One index serves many Siggy workflows
   - Clear cache only when codebase changes significantly

5. **Use statistics for planning**
   ```
   get_statistics() → Understand scale → Plan appropriately
   ```

### ❌ Don'ts

1. **Don't skip indexing**
   - Always index before starting Siggy workflows
   - The one-time cost pays off immediately

2. **Don't over-read**
   ```
   # Bad: Read entire file
   Read src/large-file.ts  # 5,000 tokens

   # Good: Peppy + targeted read
   get_file_symbols(file_path="src/large-file.ts")  # Find what you need
   Read src/large-file.ts:100-150  # Read only that section
   ```

3. **Don't re-index unnecessarily**
   - Index persists across Siggy workflows
   - Only re-index after major code changes

4. **Don't ignore Peppy's context limits**
   - Use max_results in grep_code
   - Filter with file_pattern and symbol_type

## Troubleshooting

### Issue: Peppy index not found during Siggy workflow

**Solution:**
```bash
# Re-index manually
index_codebase(path="/project", force_reindex=true)

# Then run Siggy
/siggy "your task"
```

### Issue: Peppy and Siggy both writing to different directories

**Solution:**
Coordinate artifact locations:
```yaml
# .siggy.yml
artifact_dir: ".siggy"

# Peppy uses its own .peppy_cache/
# No conflicts!
```

### Issue: Token budget exceeded even with Peppy

**Solution:**
- Use more aggressive file filtering in Peppy
- Break Siggy tasks into smaller subtasks
- Clear Peppy cache and re-index only /src directory

## Advanced: Custom Integration

### Create a Combined CLI

**File: `peppy-siggy`**
```bash
#!/bin/bash
# Combined Peppy-Siggy CLI

case "$1" in
    index)
        claude-code "index_codebase(path='${2:-.}')"
        ;;
    plan)
        claude-code "/siggy:plan $2"
        ;;
    execute)
        claude-code "/siggy:execute"
        ;;
    full)
        # Index + Full Siggy workflow
        claude-code "index_codebase(path='.')"
        claude-code "/siggy $2"
        ;;
    stats)
        claude-code "get_statistics(codebase_path='${2:-.}')"
        ;;
    *)
        echo "Usage: peppy-siggy {index|plan|execute|full|stats}"
        exit 1
        ;;
esac
```

Usage:
```bash
peppy-siggy full "Add authentication"  # Index + run Siggy
peppy-siggy stats /path/to/project     # Get Peppy stats
```

## Summary

**The combination of Peppy + Siggy gives you:**

✅ **Intelligent Planning** - Peppy's indexed search makes planning 70% faster
✅ **Efficient Execution** - Precise location finding saves 83% of execution tokens
✅ **Better Verification** - Quick structure checks with symbol search
✅ **Persistent Intelligence** - Both use caching for multi-workflow efficiency
✅ **65-75% Overall Token Savings** - Massive reduction in API costs

**When to use:**
- Complex multi-step tasks (Siggy's strength)
- Large codebases (Peppy's strength)
- Multiple related tasks in one session (shared index)
- Tasks requiring codebase understanding (Peppy research)

**Quick Start:**
```bash
# 1. Index your codebase
index_codebase(path="/project")

# 2. Run Siggy with Peppy-enhanced planning
/siggy "Your complex task"

# 3. Profit from 65%+ token savings!
```

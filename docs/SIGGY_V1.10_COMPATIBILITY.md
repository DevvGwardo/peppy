# Peppy + Siggy v1.10.0+ Compatibility Guide

## Overview

Siggy v1.10.0 introduced a major architectural change: **subagent-per-task execution model**. This document explains how Peppy works with this new model and why it's actually better for token efficiency.

## What Changed in Siggy v1.10.0+

### Before (v1.9.x and earlier): Inline Execution

```
Orchestrator Agent
  ├─ Plans tasks
  ├─ Executes TASK_1 inline
  ├─ Executes TASK_2 inline
  └─ Verifies results

Issues:
- Context pollution across tasks
- Sequential execution only
- Large context accumulation
```

### After (v1.10.0+): Subagent-per-Task

```
Orchestrator Agent
  ├─ Plans tasks
  ├─ Spawns Executor Subagent 1 → TASK_1 (fresh context)
  ├─ Spawns Executor Subagent 2 → TASK_2 (fresh context, parallel if independent)
  └─ Spawns Verifier Subagent → Validates

Benefits:
✅ Fresh context per task (no pollution)
✅ Parallel execution possible
✅ Atomic task boundaries
✅ Cleaner failure isolation
```

## Why This is PERFECT for Peppy

### The MCP Server Advantage

**Key Insight:** Peppy runs as an **MCP (Model Context Protocol) server**, which means:

1. **Persistent Index** - Index exists outside any agent's context
2. **Shared Access** - All subagents can query the same index
3. **No Context Overhead** - Index data isn't in conversation context
4. **Parallel Safe** - Multiple subagents can query simultaneously

### Execution Flow with Peppy

```
Session Start
  └─► Peppy Index exists in MCP server (persistent)

Orchestrator spawns Planner Subagent
  └─► Calls Peppy tools: search_symbols(), grep_code()
  └─► Creates PROMPT.md with exact locations

Orchestrator spawns Executor Subagent 1 (fresh context)
  └─► Calls Peppy: search_symbols("TargetClass")
  └─► Gets result from persistent index
  └─► Reads only necessary files
  └─► Makes changes
  └─► Reports: TASK_COMPLETE

Orchestrator spawns Executor Subagent 2 (fresh context, parallel)
  └─► Calls Peppy: get_file_symbols("other/file.ts")
  └─► Gets result from same persistent index
  └─► Makes changes
  └─► Reports: TASK_COMPLETE

Orchestrator spawns Verifier Subagent
  └─► Calls Peppy: grep_code() to verify changes
  └─► Validates against plan
  └─► Reports: VERIFICATION_PASSED
```

### Token Efficiency Improvement

**Subagent Model + Peppy = Even Better Token Savings**

**Without Peppy (v1.10.0+ subagent model):**
- Planner: ~8,000 tokens (research via Glob/Read)
- Executor 1: ~6,000 tokens (fresh context, re-research)
- Executor 2: ~6,000 tokens (fresh context, re-research)
- Verifier: ~3,000 tokens
- **Total: ~23,000 tokens**

**With Peppy (v1.10.0+ subagent model):**
- Index (one-time): ~2,000 tokens
- Planner: ~2,500 tokens (Peppy searches)
- Executor 1: ~1,000 tokens (Peppy navigation + change)
- Executor 2: ~1,000 tokens (Peppy navigation + change, parallel!)
- Verifier: ~1,500 tokens (Peppy validation)
- **Total: ~8,000 tokens (65% savings!)**

**Bonus:** Parallel execution means wall-clock time is also reduced!

## Updated Integration Setup

### 1. Peppy as MCP Server (Required)

```json
// Claude Code MCP settings
{
  "mcpServers": {
    "peppy": {
      "command": "python",
      "args": ["-m", "peppy.server"],
      "env": {
        "PEPPY_CACHE_DIR": "${workspaceFolder}/.peppy_cache"
      }
    }
  }
}
```

### 2. Configure Siggy for Subagent Mode

```yaml
# .siggy.yml
execution:
  mode: subagent        # Use subagent-per-task (v1.10.0+ default)
  parallel: true        # Enable parallel execution
  max_parallel: 3       # Max concurrent executor subagents

agents:
  planner: .siggy/agents/peppy-planner.md     # Optional: Use Peppy-enhanced
  executor: .siggy/agents/peppy-executor.md   # Optional: Use Peppy-enhanced
```

### 3. Optional: Auto-Index on Session Start

```bash
# Copy the Peppy session-start hook
cp integrations/siggy/hooks/peppy-session-start.sh \
   /path/to/siggy/.siggy/hooks/session-start.sh

# Make it executable
chmod +x /path/to/siggy/.siggy/hooks/session-start.sh
```

## Workflow Examples with v1.10.0+

### Example 1: Complex Feature with Parallel Tasks

**Task:** "Add authentication with login, registration, and password reset"

**Execution Flow:**

```
1. User: /siggy "Add authentication with login, registration, password reset"

2. Orchestrator spawns Planner
   → Peppy: get_statistics() - Understand codebase
   → Peppy: search_symbols(".*Router", symbol_type="class") - Find routes
   → Peppy: search_symbols(".*Service", symbol_type="class") - Find services
   → Creates PROMPT.md:
       TASK_1: Create AuthService (src/services/auth.ts)
       TASK_2: Create LoginController (src/controllers/login.ts)
       TASK_3: Create RegisterController (src/controllers/register.ts)
       TASK_4: Create PasswordResetController (src/controllers/reset.ts)
       TASK_5: Add routes (src/routes/auth.ts)

3. Orchestrator spawns 3 parallel Executor Subagents
   → Executor 1 (TASK_1): AuthService
      - Peppy: search_symbols("BaseService") - Find pattern
      - Read src/services/base.ts:10-50
      - Write src/services/auth.ts
      - Verify: npm run build
      - Report: TASK_COMPLETE

   → Executor 2 (TASK_2): LoginController [PARALLEL]
      - Peppy: search_symbols(".*Controller", symbol_type="class") - Find pattern
      - Read src/controllers/base.ts:10-40
      - Write src/controllers/login.ts
      - Verify: npm run build
      - Report: TASK_COMPLETE

   → Executor 3 (TASK_3): RegisterController [PARALLEL]
      - Peppy: get_file_symbols("src/controllers/login.ts") - Similar to TASK_2
      - Write src/controllers/register.ts
      - Verify: npm run build
      - Report: TASK_COMPLETE

4. After first wave completes, spawn next Executor
   → Executor 4 (TASK_4): PasswordResetController
      - Dependencies: TASK_1, TASK_2 complete
      - Peppy: grep_code("password.*reset", context_lines=2) - Find patterns
      - Write src/controllers/reset.ts
      - Report: TASK_COMPLETE

5. Final Executor
   → Executor 5 (TASK_5): Add routes
      - Peppy: get_file_symbols("src/routes/auth.ts") - Check current routes
      - Edit src/routes/auth.ts (add new routes)
      - Report: TASK_COMPLETE

6. Orchestrator spawns Verifier
   → Peppy: search_symbols("Auth.*") - Verify all symbols created
   → Peppy: grep_code("import.*auth", max_results=20) - Check imports
   → Run: npm run build, npm test
   → Report: VERIFICATION_PASSED

Total Time: 3 parallel executors run simultaneously!
Total Tokens: ~8,000 (vs ~30,000 without Peppy)
```

### Example 2: Refactoring Across Multiple Files

**Task:** "Rename UserService to AccountService everywhere"

**Execution Flow:**

```
1. Planner (Peppy-enhanced):
   → Peppy: search_symbols("UserService", symbol_type="class")
      Result: src/services/user.ts:15
   → Peppy: grep_code("UserService", max_results=100)
      Result: 23 usages across 12 files
   → Creates PROMPT.md with 13 tasks (1 definition + 12 usage files)

2. Orchestrator spawns 3 parallel Executors at a time:

   Wave 1 (3 parallel):
   → Executor 1: Edit src/services/user.ts (rename class)
   → Executor 2: Edit src/controllers/user.ts (update import)
   → Executor 3: Edit src/routes/user.ts (update import)

   Wave 2 (3 parallel):
   → Executor 4: Edit src/middleware/auth.ts
   → Executor 5: Edit tests/user.test.ts
   → Executor 6: Edit tests/integration.test.ts

   [continues...]

3. Each Executor uses Peppy:
   → get_file_symbols() to find exact location
   → Read only the relevant sections
   → Make precise edits
   → Verify independently

4. Verifier:
   → Peppy: search_symbols("UserService") - Should return 0 results
   → Peppy: search_symbols("AccountService") - Should return class definition
   → Peppy: grep_code("AccountService") - Verify all usages updated
   → Run tests
```

## Key Differences from v1.9.x Integration

### v1.9.x (Inline Execution)

```python
# Planner did research
peppy.search_symbols("Foo")  # Result in planner context

# Orchestrator executed tasks inline
# - Still had access to planner's results in same context
# - Could reference earlier findings
# - But context accumulated across all tasks
```

### v1.10.0+ (Subagent Model)

```python
# Planner does research
peppy.search_symbols("Foo")  # Result in planner context
# Creates PROMPT.md with findings

# Executor Subagent 1 (FRESH CONTEXT)
# - Does NOT have planner's context
# - Reads PROMPT.md to know what to do
# - Calls Peppy tools again if needed
peppy.search_symbols("Foo")  # Same query, but fresh subagent
# ✅ No problem! Peppy's index is persistent, returns same result

# Executor Subagent 2 (FRESH CONTEXT, PARALLEL)
# - Also calls Peppy independently
peppy.get_file_symbols("bar.ts")
# ✅ Works perfectly! MCP server handles concurrent requests
```

## Best Practices for v1.10.0+

### ✅ Do This

1. **Let each subagent query Peppy independently**
   ```
   # Don't worry about "repeat" queries
   # Each subagent is fresh - let it use Peppy to navigate

   Planner: search_symbols("Foo") → Creates plan
   Executor 1: search_symbols("Foo") → Navigates to implement
   Executor 2: grep_code("Foo") → Finds usages
   ```

2. **Embrace parallel execution**
   ```yaml
   # .siggy.yml
   execution:
     parallel: true
     max_parallel: 3  # Balance speed vs token cost
   ```

3. **Use Peppy in PROMPT.md**
   ```markdown
   ## TASK_1: Modify AuthService

   **Location:** Use `search_symbols(query="AuthService", symbol_type="class")`
   **Pattern Reference:** Use `get_file_symbols(file_path="src/services/base.ts")`

   [task details...]
   ```

4. **Leverage Peppy in verification**
   ```
   Verifier:
     - search_symbols("NewClass") to verify creation
     - grep_code("import.*NewClass") to check integration
     - get_statistics() to validate no regressions
   ```

### ❌ Don't Do This

1. **Don't assume subagents share context**
   ```
   # Bad assumption:
   # "Earlier I found Foo at line 15" (executor has no "earlier")

   # Good approach:
   # "Let me find Foo using Peppy" (executor queries independently)
   ```

2. **Don't skip Peppy queries in executors**
   ```
   # Bad: Assume you know location from plan
   Read src/foo.ts  # Might not be the right file

   # Good: Verify with Peppy first
   search_symbols("Foo") → src/foo.ts:15
   Read src/foo.ts:10-25
   ```

3. **Don't disable parallel execution unnecessarily**
   ```yaml
   # Bad: Forces sequential (slower, same token cost)
   execution:
     parallel: false

   # Good: Use parallel for independent tasks
   execution:
     parallel: true
   ```

## Troubleshooting

### Issue: Executors can't find code that Planner found

**Cause:** Planner created plan but didn't include specific enough details

**Solution:** Enhance planner to include Peppy queries in PROMPT.md
```markdown
## TASK_1: Modify UserService

**To find the file, run:**
```
search_symbols(query="UserService", symbol_type="class")
```

**Expected location:** src/services/user.ts:15
```

### Issue: Parallel executors conflict on same file

**Cause:** Multiple tasks editing the same file simultaneously

**Solution:** Siggy's orchestrator should detect file conflicts and serialize those tasks
```yaml
# PROMPT.md - Mark dependencies
TASK_1: Edit src/auth.ts (lines 10-20)
TASK_2: Edit src/auth.ts (lines 50-60)  # Depends on TASK_1
```

### Issue: Index seems stale for subagents

**Cause:** Codebase changed but index not updated

**Solution:** Re-index before Siggy workflow
```bash
# Manual re-index
index_codebase(path="/project", force_reindex=true)

# Or use session-start hook (auto-indexes)
cp integrations/siggy/hooks/peppy-session-start.sh .siggy/hooks/
```

## Version Compatibility Matrix

| Peppy Version | Siggy Version | Compatibility | Notes |
|---------------|---------------|---------------|-------|
| v1.0.0+ | v1.10.0+ | ✅ Full | Optimal - subagent model + MCP server |
| v1.0.0+ | v1.9.x | ✅ Full | Works - inline execution model |
| v1.0.0+ | < v1.9.0 | ⚠️ Partial | May need manual integration |

**Recommendation:** Use Siggy v1.10.0+ for best performance with Peppy.

## Summary

**Siggy v1.10.0+'s subagent-per-task model is actually BETTER for Peppy because:**

1. ✅ **Fresh contexts prevent pollution** - Each subagent queries Peppy cleanly
2. ✅ **Parallel execution works perfectly** - MCP server handles concurrent queries
3. ✅ **Persistent index survives context resets** - No re-indexing between subagents
4. ✅ **Cleaner separation of concerns** - Navigation (Peppy) vs execution (subagent)
5. ✅ **Better token efficiency** - Small subagent contexts + Peppy's targeted data

**The combination delivers 65-75% token savings on complex workflows while also enabling parallel execution for faster wall-clock time.**

## Learn More

- **[Main Integration Guide](SIGGY_INTEGRATION.md)** - Complete integration documentation
- **[Integration Quick Start](../integrations/siggy/README.md)** - Setup instructions
- **[Siggy v1.10.0 Release Notes](https://github.com/DevvGwardo/siggy-plugin/blob/master/CHANGELOG.md)** - Full changelog

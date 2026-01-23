# Peppy + Siggy Integration

> **📌 Version Compatibility:** This integration is optimized for **Siggy v1.10.0+** with subagent-per-task execution. See **[v1.10+ Compatibility Guide](../../docs/SIGGY_V1.10_COMPATIBILITY.md)** for detailed architecture information.

This directory contains Peppy-enhanced agents for use with the [Siggy plugin](https://github.com/DevvGwardo/siggy-plugin).

## What's Included

### Agents

- **`agents/peppy-planner.md`** - Enhanced planner that uses Peppy for 70% faster codebase research (v1.10.0+ compatible)
- **`agents/peppy-executor.md`** - Enhanced executor that uses Peppy for 80% more efficient execution (v1.10.0+ subagent model)

### Hooks

- **`hooks/peppy-session-start.sh`** - Auto-indexes codebase at session start (optional)

### Documentation

- **`../../docs/SIGGY_INTEGRATION.md`** - Complete integration guide with examples, best practices, and token savings analysis
- **`../../docs/SIGGY_V1.10_COMPATIBILITY.md`** - Siggy v1.10.0+ subagent model compatibility guide

## Quick Setup

### 1. Install Both Plugins

```bash
# Install Peppy
cd /path/to/peppy
pip install -e .

# Install Siggy
# Follow Siggy's installation instructions from their repo
```

### 2. Configure Peppy as MCP Server

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

### 3. Use Enhanced Agents (Optional)

Copy the enhanced agents to your Siggy installation:

```bash
# Copy Peppy-enhanced agents to your Siggy agents directory
cp integrations/siggy/agents/* /path/to/siggy-plugin/.siggy/agents/

# Or symlink them
ln -s /path/to/peppy/integrations/siggy/agents/peppy-planner.md \
      /path/to/siggy-plugin/.siggy/agents/peppy-planner.md
```

### 4. Configure Siggy to Use Peppy Agents

Edit your `.siggy.yml`:

```yaml
agents:
  planner: .siggy/agents/peppy-planner.md  # Use Peppy-enhanced planner
  executor: .siggy/agents/peppy-executor.md  # Use Peppy-enhanced executor
```

## Basic Usage

### Standard Workflow

```bash
# 1. Index your codebase (one-time per session)
index_codebase(path="/path/to/project")

# 2. Run Siggy workflow (now Peppy-enhanced!)
/siggy "Add authentication to API"

# 3. Enjoy 65-75% token savings!
```

### Manual Phase Control

```bash
# Index first
index_codebase(path="/path/to/project")

# Run phases individually
/siggy:plan "Add authentication"
/siggy:execute
/siggy:verify
```

## Token Savings

### Without Peppy Integration

```
Planning: ~8,000 tokens
Execution: ~12,000 tokens
Verification: ~3,000 tokens
Total: ~23,000 tokens
```

### With Peppy Integration

```
Indexing (one-time): ~2,000 tokens
Planning: ~2,500 tokens (-69%)
Execution: ~2,000 tokens (-83%)
Verification: ~1,500 tokens (-50%)
Total: ~8,000 tokens (65% savings!)
```

## Examples

### Example 1: Adding a Feature

```
Task: "Add rate limiting to all API endpoints"

Traditional Siggy:
- Globs for route files
- Reads dozens of files
- Searches manually
= ~25,000 tokens

Peppy + Siggy:
- get_statistics() - overview
- search_symbols() - find routers
- grep_code() - find middleware pattern
- Targeted reads
= ~7,000 tokens (72% savings)
```

### Example 2: Refactoring

```
Task: "Rename UserService to AccountService everywhere"

Traditional Siggy:
- Glob for all files
- Read every file
- Find and replace
= ~35,000 tokens

Peppy + Siggy:
- search_symbols("UserService") - find definition
- grep_code("UserService\\(") - find usages
- Targeted edits
= ~6,000 tokens (83% savings)
```

### Example 3: Bug Fix

```
Task: "Fix authentication bug in login flow"

Traditional Siggy:
- Search for login-related files
- Read auth modules
- Trace execution flow
= ~18,000 tokens

Peppy + Siggy:
- search_symbols("login", symbol_type="function")
- get_file_symbols("src/auth.ts")
- grep_code("authenticate", context_lines=3)
= ~4,500 tokens (75% savings)
```

## Best Practices

### ✅ Do This

1. **Always index at session start**
   ```
   index_codebase(path="/project")
   ```

2. **Let agents use Peppy tools**
   - Planner: search_symbols, grep_code, get_statistics
   - Executor: search_symbols, get_file_symbols

3. **Verify Peppy is working**
   ```
   get_statistics(codebase_path="/project")
   # Should return stats without error
   ```

4. **Share index across multiple workflows**
   - One index serves many Siggy tasks
   - Only re-index when codebase changes significantly

### ❌ Don't Do This

1. **Don't skip indexing**
   - Peppy agents expect an index to exist
   - First search will fail without index

2. **Don't re-index for every task**
   - Index persists across Siggy workflows
   - Wastes tokens to re-index unnecessarily

3. **Don't override Peppy agent logic**
   - Trust the agents to use Peppy first
   - They're optimized for token efficiency

## Troubleshooting

### "No index found" error during planning

```bash
# Solution: Index the codebase first
index_codebase(path="/path/to/project")

# Then retry Siggy
/siggy "your task"
```

### Peppy tools not available in Siggy agents

```bash
# Check MCP configuration
cat ~/.config/claude-code/mcp_settings.json

# Should include:
{
  "mcpServers": {
    "peppy": {
      "command": "python",
      "args": ["-m", "peppy.server"]
    }
  }
}

# Restart Claude Code if needed
```

### Token usage still high

```bash
# Check if enhanced agents are actually being used
# Look for Peppy tool calls in Siggy output

# If not using enhanced agents:
# 1. Verify agent files are in correct location
# 2. Check .siggy.yml points to correct agent files
# 3. Restart Siggy workflow
```

## Advanced Usage

### Create Custom Peppy-Aware Workflows

```yaml
# .siggy/workflows/peppy-workflow.yml
name: Peppy-Enhanced Full Stack Feature
phases:
  - name: index
    agent: peppy-indexer  # Custom agent that just runs index_codebase
  - name: plan
    agent: peppy-planner
  - name: execute
    agent: peppy-executor
  - name: verify
    agent: peppy-verifier
```

### Selective Indexing

```bash
# Index only source code (not node_modules, etc.)
index_codebase(path="/project/src")

# Or exclude patterns
# (requires Peppy enhancement - TODO)
```

## Learn More

- **[Full Integration Guide](../../docs/SIGGY_INTEGRATION.md)** - Comprehensive documentation
- **[Peppy README](../../README.md)** - Peppy features and usage
- **[Siggy Repository](https://github.com/DevvGwardo/siggy-plugin)** - Siggy documentation

## Contributing

Have ideas for better integration? Found a bug?

1. Test your enhancement
2. Submit a PR with examples
3. Include token savings benchmarks

## License

MIT (same as Peppy)

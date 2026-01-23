"""MCP server for Peppy codebase indexing plugin."""

import asyncio
import sys
from pathlib import Path
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, GetPromptResult, Prompt, PromptArgument, PromptMessage

from .indexer import CodebaseIndexer
from .searcher import CodebaseSearcher
from .cache import IndexCache


# Initialize shared instances
cache = IndexCache()
indexer = CodebaseIndexer(cache)
searcher = CodebaseSearcher(cache)

# Create MCP server
app = Server("peppy")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="index_codebase",
            description="Index a codebase directory for fast searching. This scans all files, extracts symbols (functions, classes, etc.), and caches the results. Run this before using search tools.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the codebase root directory"
                    },
                    "force_reindex": {
                        "type": "boolean",
                        "description": "Force re-indexing even if cache exists",
                        "default": False
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="search_symbols",
            description="Search for code symbols (functions, classes, variables, etc.) in an indexed codebase. Supports regex patterns and filtering by symbol type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "codebase_path": {
                        "type": "string",
                        "description": "Path to the indexed codebase root"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (supports regex)"
                    },
                    "symbol_type": {
                        "type": "string",
                        "description": "Filter by symbol type",
                        "enum": ["function", "class", "method", "variable", "interface", "type"]
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to filter (e.g., '*.py', '**/*.js')"
                    },
                    "use_regex": {
                        "type": "boolean",
                        "description": "Treat query as regex pattern",
                        "default": True
                    }
                },
                "required": ["codebase_path", "query"]
            }
        ),
        Tool(
            name="grep_code",
            description="Search for text patterns across all files in the indexed codebase. Like grep but with caching and context support.",
            inputSchema={
                "type": "object",
                "properties": {
                    "codebase_path": {
                        "type": "string",
                        "description": "Path to the indexed codebase root"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern (supports regex)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to filter (e.g., '*.py')"
                    },
                    "context_lines": {
                        "type": "integer",
                        "description": "Number of context lines to show before/after match",
                        "default": 0,
                        "minimum": 0,
                        "maximum": 10
                    },
                    "use_regex": {
                        "type": "boolean",
                        "description": "Treat pattern as regex",
                        "default": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["codebase_path", "pattern"]
            }
        ),
        Tool(
            name="get_file_symbols",
            description="Get all symbols (functions, classes, etc.) defined in a specific file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "codebase_path": {
                        "type": "string",
                        "description": "Path to the indexed codebase root"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file (absolute or relative to codebase)"
                    }
                },
                "required": ["codebase_path", "file_path"]
            }
        ),
        Tool(
            name="get_statistics",
            description="Get statistics about an indexed codebase (file counts, symbol counts, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "codebase_path": {
                        "type": "string",
                        "description": "Path to the indexed codebase root"
                    }
                },
                "required": ["codebase_path"]
            }
        ),
        Tool(
            name="clear_cache",
            description="Clear the index cache for a specific codebase or all codebases.",
            inputSchema={
                "type": "object",
                "properties": {
                    "codebase_path": {
                        "type": "string",
                        "description": "Path to codebase (omit to clear all caches)"
                    }
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls."""

    try:
        if name == "index_codebase":
            path = Path(arguments["path"])
            force_reindex = arguments.get("force_reindex", False)

            if not path.exists():
                return [TextContent(
                    type="text",
                    text=f"Error: Path does not exist: {path}"
                )]

            if not path.is_dir():
                return [TextContent(
                    type="text",
                    text=f"Error: Path is not a directory: {path}"
                )]

            # Run indexing (in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            index = await loop.run_in_executor(
                None,
                indexer.index_codebase,
                path,
                force_reindex
            )

            return [TextContent(
                type="text",
                text=f"Successfully indexed codebase at {path}\n"
                     f"Total files: {index['total_files']}\n"
                     f"Total symbols: {index['symbol_count']}"
            )]

        elif name == "search_symbols":
            codebase_path = Path(arguments["codebase_path"])
            query = arguments["query"]
            symbol_type = arguments.get("symbol_type")
            file_pattern = arguments.get("file_pattern")
            use_regex = arguments.get("use_regex", True)

            results = searcher.search_symbols(
                codebase_path,
                query,
                symbol_type=symbol_type,
                file_pattern=file_pattern,
                use_regex=use_regex
            )

            if not results:
                return [TextContent(
                    type="text",
                    text=f"No symbols found matching '{query}'"
                )]

            # Format results
            output_lines = [f"Found {len(results)} symbols matching '{query}':\n"]
            for result in results[:50]:  # Limit to 50 results in output
                output_lines.append(
                    f"  {result['type']:10} {result['name']:30} "
                    f"{result['file']}:{result['line']}"
                )

            if len(results) > 50:
                output_lines.append(f"\n... and {len(results) - 50} more results")

            return [TextContent(type="text", text="\n".join(output_lines))]

        elif name == "grep_code":
            codebase_path = Path(arguments["codebase_path"])
            pattern = arguments["pattern"]
            file_pattern = arguments.get("file_pattern")
            context_lines = arguments.get("context_lines", 0)
            use_regex = arguments.get("use_regex", True)
            max_results = arguments.get("max_results", 100)

            results = searcher.grep_code(
                codebase_path,
                pattern,
                file_pattern=file_pattern,
                context_lines=context_lines,
                use_regex=use_regex,
                max_results=max_results
            )

            if not results:
                return [TextContent(
                    type="text",
                    text=f"No matches found for pattern '{pattern}'"
                )]

            # Format results
            output_lines = [f"Found {len(results)} matches for '{pattern}':\n"]

            for result in results:
                output_lines.append(f"\n{result['file']}:{result['line']}")

                if result.get("context") and context_lines > 0:
                    ctx = result["context"]
                    # Show context before
                    for line in ctx.get("before", []):
                        output_lines.append(f"  {line['line']:4d} | {line['content']}")
                    # Show match line
                    match = ctx["match"]
                    output_lines.append(f"→ {match['line']:4d} | {match['content']}")
                    # Show context after
                    for line in ctx.get("after", []):
                        output_lines.append(f"  {line['line']:4d} | {line['content']}")
                else:
                    output_lines.append(f"  {result['content']}")

            return [TextContent(type="text", text="\n".join(output_lines))]

        elif name == "get_file_symbols":
            codebase_path = Path(arguments["codebase_path"])
            file_path = arguments["file_path"]

            symbols = searcher.get_file_symbols(codebase_path, file_path)

            if not symbols:
                return [TextContent(
                    type="text",
                    text=f"No symbols found in {file_path}"
                )]

            output_lines = [f"Symbols in {file_path}:\n"]
            for symbol in symbols:
                output_lines.append(
                    f"  {symbol['type']:10} {symbol['name']:30} "
                    f"line {symbol['line']}"
                )

            return [TextContent(type="text", text="\n".join(output_lines))]

        elif name == "get_statistics":
            codebase_path = Path(arguments["codebase_path"])

            stats = searcher.get_statistics(codebase_path)

            if not stats:
                return [TextContent(
                    type="text",
                    text=f"No index found for {codebase_path}. Run index_codebase first."
                )]

            output_lines = [
                f"Statistics for {stats['root']}:",
                f"\nTotal files: {stats['total_files']}",
                f"Total symbols: {stats['total_symbols']}",
                "\nSymbols by type:"
            ]

            for sym_type, count in sorted(stats['symbol_types'].items()):
                output_lines.append(f"  {sym_type:15} {count:5d}")

            output_lines.append("\nFiles by extension:")
            for ext, count in sorted(stats['file_extensions'].items(), key=lambda x: -x[1])[:10]:
                output_lines.append(f"  {ext:15} {count:5d}")

            return [TextContent(type="text", text="\n".join(output_lines))]

        elif name == "clear_cache":
            codebase_path = arguments.get("codebase_path")

            if codebase_path:
                cache.clear(Path(codebase_path))
                return [TextContent(
                    type="text",
                    text=f"Cache cleared for {codebase_path}"
                )]
            else:
                cache.clear()
                return [TextContent(
                    type="text",
                    text="All caches cleared"
                )]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Entry point for the server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()

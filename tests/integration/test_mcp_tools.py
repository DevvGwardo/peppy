"""Integration tests for MCP server tools."""

import pytest
from pathlib import Path
import tempfile
from peppy.server import call_tool


class TestIndexCodebaseTool:
    """Tests for index_codebase tool."""

    @pytest.mark.asyncio
    async def test_mcp_index_codebase_valid_path(self):
        """Indexes successfully."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        result = await call_tool("index_codebase", {"path": str(tmpdir)})

        assert result[0].type == "text"
        assert "Successfully indexed" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_index_codebase_invalid_path(self, mocker):
        """Returns error for non-existent path."""
        result = await call_tool("index_codebase", {"path": "/nonexistent"})

        assert result[0].type == "text"
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_index_codebase_force_reindex(self):
        """Ignores cache when forced."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        result1 = await call_tool("index_codebase", {"path": str(tmpdir)})
        result2 = await call_tool("index_codebase", {"path": str(tmpdir), "force_reindex": True})

        assert "Successfully indexed" in result1[0].text
        assert "Successfully indexed" in result2[0].text


class TestSearchSymbolsTool:
    """Tests for search_symbols tool."""

    @pytest.mark.asyncio
    async def test_mcp_search_symbols_basic(self):
        """Finds symbols correctly."""
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "test.py"
        test_file.write_text("def hello(): pass\ndef world(): pass", encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool("search_symbols", {"codebase_path": str(tmpdir), "query": "hello"})

        assert result[0].type == "text"
        assert "found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_mcp_search_symbols_missing_index(self, mocker):
        """Returns error for unindexed codebase."""
        result = await call_tool(
            "search_symbols", {"codebase_path": "/nonexistent", "query": "test"}
        )

        assert "No symbols found" in result[0].text or "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_search_symbols_with_filters(self):
        """Respects type and file filters."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool(
            "search_symbols",
            {
                "codebase_path": str(tmpdir),
                "query": "test",
                "symbol_type": "function",
            },
        )

        assert "function" in result[0].text


class TestGrepCodeTool:
    """Tests for grep_code tool."""

    @pytest.mark.asyncio
    async def test_mcp_grep_code_basic(self):
        """Finds patterns correctly."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("import os\nimport sys", encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool("grep_code", {"codebase_path": str(tmpdir), "pattern": "import"})

        assert result[0].type == "text"
        assert "import" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_mcp_grep_code_with_context(self):
        """Includes context lines properly."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("line1\nTARGET\nline3", encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool(
            "grep_code",
            {
                "codebase_path": str(tmpdir),
                "pattern": "TARGET",
                "context_lines": 1,
            },
        )

        assert "line1" in result[0].text or "line3" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_grep_code_max_results(self):
        """Respects result limit."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("\n".join(["TARGET"] * 200), encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool(
            "grep_code",
            {
                "codebase_path": str(tmpdir),
                "pattern": "TARGET",
                "max_results": 10,
            },
        )

        assert "10" in result[0].text or "results" in result[0].text


class TestGetFileSymbolsTool:
    """Tests for get_file_symbols tool."""

    @pytest.mark.asyncio
    async def test_mcp_get_file_symbols_valid(self):
        """Returns file symbols."""
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "test.py"
        test_file.write_text("def test(): pass", encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool(
            "get_file_symbols",
            {
                "codebase_path": str(tmpdir),
                "file_path": str(test_file),
            },
        )

        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_mcp_get_file_symbols_invalid(self):
        """Returns empty for non-existent."""
        tmpdir = Path(tempfile.mkdtemp())

        result = await call_tool(
            "get_file_symbols",
            {
                "codebase_path": str(tmpdir),
                "file_path": "nonexistent.py",
            },
        )

        assert "No symbols found" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_get_file_symbols_not_indexed(self):
        """Returns error for unindexed codebase."""
        result = await call_tool(
            "get_file_symbols",
            {
                "codebase_path": "/nonexistent",
                "file_path": "test.py",
            },
        )

        assert "No symbols" in result[0].text


class TestGetStatisticsTool:
    """Tests for get_statistics tool."""

    @pytest.mark.asyncio
    async def test_mcp_get_statistics_valid(self):
        """Returns correct statistics."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool("get_statistics", {"codebase_path": str(tmpdir)})

        assert "Files" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_get_statistics_not_indexed(self):
        """Returns error message."""
        result = await call_tool("get_statistics", {"codebase_path": "/nonexistent"})

        assert "No index" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_get_statistics_correct_counts(self):
        """Validates file/symbol counts."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool("get_statistics", {"codebase_path": str(tmpdir)})

        assert "1" in result[0].text


class TestClearCacheTool:
    """Tests for clear_cache tool."""

    @pytest.mark.asyncio
    async def test_mcp_clear_cache_all(self):
        """Clears all caches."""
        result = await call_tool("clear_cache", {})

        assert result[0].type == "text"
        assert "cleared" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_mcp_clear_cache_specific(self):
        """Clears one codebase cache."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        await call_tool("index_codebase", {"path": str(tmpdir)})
        result = await call_tool("clear_cache", {"codebase_path": str(tmpdir)})

        assert "cleared" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_mcp_clear_cache_no_path(self):
        """Clears all with no argument."""
        result = await call_tool("clear_cache", {})

        assert "cleared" in result[0].text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

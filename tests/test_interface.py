"""Tests for the PeppyInterface."""

import pytest
from pathlib import Path
from peppy import PeppyInterface, create_interface, SearchResult, GrepResult, CodebaseStats


class TestPeppyInterface:
    """Tests for the PeppyInterface class."""

    @pytest.fixture
    def interface(self):
        """Create a fresh interface for each test."""
        return PeppyInterface()

    @pytest.fixture
    def indexed_interface(self, interface):
        """Create an interface with the current directory indexed."""
        interface.index(str(Path.cwd()), force=True)
        return interface

    def test_initialization(self, interface):
        """Test interface initialization."""
        assert interface is not None
        assert interface.indexer is not None
        assert interface.searcher is not None
        assert interface.cache is not None

    def test_create_interface_helper(self):
        """Test the create_interface convenience function."""
        interface = create_interface()
        assert isinstance(interface, PeppyInterface)

    def test_index_codebase(self, interface):
        """Test indexing a codebase."""
        stats = interface.index(str(Path.cwd()), force=True)

        assert isinstance(stats, CodebaseStats)
        assert stats.total_files > 0
        assert stats.total_symbols > 0
        assert len(stats.file_extensions) > 0

    def test_set_codebase(self, interface):
        """Test setting current codebase."""
        result = interface.set_codebase(str(Path.cwd()))
        assert result is interface  # Should return self for chaining
        assert interface._current_codebase == Path.cwd().resolve()

    def test_is_indexed(self, indexed_interface):
        """Test checking if codebase is indexed."""
        assert indexed_interface.is_indexed() is True

    def test_find_symbols(self, indexed_interface):
        """Test finding symbols by pattern."""
        results = indexed_interface.find_symbols("CodebaseIndexer")

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        assert any(r.name == "CodebaseIndexer" for r in results)

    def test_find_definition(self, indexed_interface):
        """Test finding symbol definition."""
        result = indexed_interface.find_definition("CodebaseIndexer")

        assert result is not None
        assert isinstance(result, SearchResult)
        assert result.name == "CodebaseIndexer"
        assert result.type == "class"

    def test_find_classes(self, indexed_interface):
        """Test finding class definitions."""
        results = indexed_interface.find_classes()

        assert len(results) > 0
        assert all(r.type == "class" for r in results)

    def test_find_functions(self, indexed_interface):
        """Test finding function definitions."""
        results = indexed_interface.find_functions()

        assert len(results) > 0
        assert all(r.type == "function" for r in results)

    def test_grep(self, indexed_interface):
        """Test grep functionality."""
        results = indexed_interface.grep("import")

        assert len(results) > 0
        assert all(isinstance(r, GrepResult) for r in results)

    def test_grep_with_context(self, indexed_interface):
        """Test grep with context lines."""
        results = indexed_interface.grep("CodebaseIndexer", context=2)

        assert len(results) > 0
        # At least some results should have context
        has_context = any(r.context_before or r.context_after for r in results)
        assert has_context

    def test_find_usages(self, indexed_interface):
        """Test finding symbol usages."""
        results = indexed_interface.find_usages("cache")

        assert len(results) > 0
        assert all(isinstance(r, GrepResult) for r in results)

    def test_get_file_symbols(self, indexed_interface):
        """Test getting symbols from a specific file."""
        indexer_path = str(Path.cwd() / "peppy" / "indexer.py")
        results = indexed_interface.get_file_symbols(indexer_path)

        assert len(results) > 0
        # Should find the CodebaseIndexer class
        assert any(r.name == "CodebaseIndexer" for r in results)

    def test_get_file_structure(self, indexed_interface):
        """Test getting file structure overview."""
        indexer_path = str(Path.cwd() / "peppy" / "indexer.py")
        structure = indexed_interface.get_file_structure(indexer_path)

        assert "Structure of" in structure
        assert "CodebaseIndexer" in structure

    def test_get_stats(self, indexed_interface):
        """Test getting codebase statistics."""
        stats = indexed_interface.get_stats()

        assert isinstance(stats, CodebaseStats)
        assert stats.total_files > 0
        assert stats.total_symbols > 0

    def test_get_overview(self, indexed_interface):
        """Test getting codebase overview."""
        overview = indexed_interface.get_overview()

        assert "Codebase Overview" in overview
        assert "Files:" in overview
        assert "Symbols:" in overview

    def test_clear_cache(self, indexed_interface):
        """Test clearing cache."""
        assert indexed_interface.is_indexed() is True
        indexed_interface.clear_cache()
        assert indexed_interface.is_indexed() is False


class TestSearchResult:
    """Tests for the SearchResult dataclass."""

    def test_to_location(self):
        """Test location string generation."""
        result = SearchResult(
            name="test_func",
            type="function",
            file="/path/to/file.py",
            line=42,
            column=0
        )

        assert result.to_location() == "/path/to/file.py:42"

    def test_to_dict(self):
        """Test dictionary conversion."""
        result = SearchResult(
            name="test_func",
            type="function",
            file="/path/to/file.py",
            line=42,
            column=5,
            context="some context"
        )

        d = result.to_dict()
        assert d["name"] == "test_func"
        assert d["type"] == "function"
        assert d["file"] == "/path/to/file.py"
        assert d["line"] == 42
        assert d["column"] == 5
        assert d["context"] == "some context"


class TestGrepResult:
    """Tests for the GrepResult dataclass."""

    def test_to_location(self):
        """Test location string generation."""
        result = GrepResult(
            file="/path/to/file.py",
            line=42,
            content="import something"
        )

        assert result.to_location() == "/path/to/file.py:42"

    def test_to_dict(self):
        """Test dictionary conversion."""
        result = GrepResult(
            file="/path/to/file.py",
            line=42,
            content="import something",
            context_before=["# comment"],
            context_after=["next line"]
        )

        d = result.to_dict()
        assert d["file"] == "/path/to/file.py"
        assert d["line"] == 42
        assert d["content"] == "import something"
        assert d["context_before"] == ["# comment"]
        assert d["context_after"] == ["next line"]


class TestCodebaseStats:
    """Tests for the CodebaseStats dataclass."""

    def test_summary(self):
        """Test summary string generation."""
        stats = CodebaseStats(
            root="/path/to/project",
            total_files=100,
            total_symbols=500,
            symbol_types={"function": 200, "class": 50, "method": 150},
            file_extensions={".py": 80, ".js": 20}
        )

        summary = stats.summary()
        assert "Codebase: /path/to/project" in summary
        assert "Files: 100" in summary
        assert "Symbols: 500" in summary

    def test_to_dict(self):
        """Test dictionary conversion."""
        stats = CodebaseStats(
            root="/path/to/project",
            total_files=100,
            total_symbols=500,
            symbol_types={"function": 200},
            file_extensions={".py": 80}
        )

        d = stats.to_dict()
        assert d["root"] == "/path/to/project"
        assert d["total_files"] == 100
        assert d["total_symbols"] == 500


class TestSiggyWorkflowHelpers:
    """Tests for Siggy workflow integration helpers."""

    @pytest.fixture
    def indexed_interface(self):
        """Create an interface with the current directory indexed."""
        interface = PeppyInterface()
        interface.index(str(Path.cwd()), force=True)
        return interface

    def test_for_planning(self, indexed_interface):
        """Test planning phase helper."""
        result = indexed_interface.for_planning()

        assert "overview" in result
        assert "key_classes" in result
        assert "key_functions" in result
        assert "focus_results" in result

    def test_for_planning_with_focus(self, indexed_interface):
        """Test planning with focus patterns."""
        result = indexed_interface.for_planning(focus_patterns=["Indexer", "cache"])

        assert "focus_results" in result
        assert "Indexer" in result["focus_results"]
        assert "cache" in result["focus_results"]

    def test_for_execution(self, indexed_interface):
        """Test execution phase helper."""
        result = indexed_interface.for_execution("CodebaseIndexer")

        assert "target" in result
        assert result["target"] == "CodebaseIndexer"
        assert "definition" in result
        assert "usages" in result
        assert "usage_count" in result

    def test_for_verification(self, indexed_interface):
        """Test verification phase helper."""
        result = indexed_interface.for_verification(
            expected_symbols=["CodebaseIndexer", "CodebaseSearcher"]
        )

        assert "stats" in result
        assert "verification_results" in result
        assert "CodebaseIndexer" in result["verification_results"]
        assert "CodebaseSearcher" in result["verification_results"]

        # Both should be found
        assert result["verification_results"]["CodebaseIndexer"]["found"] is True
        assert result["verification_results"]["CodebaseSearcher"]["found"] is True

    def test_for_verification_missing_symbol(self, indexed_interface):
        """Test verification with missing symbol."""
        result = indexed_interface.for_verification(
            expected_symbols=["NonExistentSymbol123"]
        )

        assert result["verification_results"]["NonExistentSymbol123"]["found"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

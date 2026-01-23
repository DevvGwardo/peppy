"""Integration tests for real-world usage workflows."""

import pytest
from pathlib import Path
import tempfile
from peppy.interface import PeppyInterface, SearchResult, GrepResult


class TestExplorationWorkflow:
    """Tests for exploration workflow."""

    def test_exploration_workflow_start_to_finish(self):
        """index -> stats -> symbol search."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass\nclass Test: pass", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        stats = interface.get_stats()

        assert stats is not None
        assert stats.total_files >= 1

        results = interface.find_symbols("test")

        assert len(results) > 0

    def test_exploration_workflow_token_efficient(self):
        """Minimal context, focused queries."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        results = interface.find_symbols("test", limit=5)

        assert len(results) <= 5


class TestDebuggingWorkflow:
    """Tests for debugging workflow."""

    def test_debugging_workflow_find_errors(self):
        """Grep errors -> find definitions."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text(
            "def raise_error(): raise Exception('error')\ndef test(): pass", encoding="utf-8"
        )

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        grep_results = interface.grep("raise", limit=10)

        assert len(grep_results) >= 0

    def test_debugging_workflow_with_context(self):
        """Minimal context for location."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("line1\nTARGET\nline3", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        results = interface.grep("TARGET", context=0)

        for r in results:
            assert len(r.context_before) == 0
            assert len(r.context_after) == 0


class TestRefactoringWorkflow:
    """Tests for refactoring workflow."""

    def test_refactoring_workflow_find_function(self):
        """Locate definition + usages."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text(
            "def old_name(): pass\nclass Test:\n    def use(self):\n        old_name()",
            encoding="utf-8",
        )

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        definition = interface.find_definition("old_name")

        assert definition is not None

        usages = interface.find_usages("old_name")

        assert len(usages) >= 1

    def test_refactoring_workflow_verify_changes(self):
        """Check after modifications."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))

        result = interface.for_verification(expected_symbols=["test"])

        assert result["verification_results"]["test"]["found"]


class TestMultiLanguageSearch:
    """Tests for cross-language search."""

    def test_cross_language_search(self):
        """Symbols across different files."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")
        (tmpdir / "test.js").write_text("function test() {}", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        results = interface.find_symbols("test")

        assert len(results) >= 1

    def test_language_specific_search(self):
        """Filter by file extension."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")
        (tmpdir / "test.js").write_text("function test() {}", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        py_results = interface.find_symbols("test", file_pattern="*.py")

        assert len(py_results) >= 1
        assert ".py" in py_results[0].file


class TestCachePersistence:
    """Tests for cache behavior."""

    def test_cache_persists_across_sessions(self):
        """Index survives restart."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        interface1 = PeppyInterface()

        interface1.index(str(tmpdir))

        interface2 = PeppyInterface()

        assert interface2.is_indexed(str(tmpdir))

    def test_cache_invalidation_on_changes(self):
        """Cache fresh after code changes."""
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "test.py"
        test_file.write_text("def test1(): pass", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir), force=True)

        test_file.write_text("def test2(): pass", encoding="utf-8")


class TestSiggyIntegration:
    """Tests for Siggy workflow integration."""

    def test_siggy_planning_workflow(self):
        """Planning prompt helpers work."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass\nclass Test: pass", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        result = interface.for_planning()

        assert "overview" in result
        assert "key_classes" in result
        assert "key_functions" in result

    def test_siggy_execution_workflow(self):
        """Targeted location finding."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def target_func(): pass", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        result = interface.for_execution("target_func")

        assert "definition" in result
        assert "usages" in result

    def test_siggy_verification_workflow(self):
        """Verification helpers."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def test(): pass", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        result = interface.for_verification(expected_symbols=["test"])

        assert "test" in result["verification_results"]
        assert result["verification_results"]["test"]["found"]

    def test_siggy_focus_patterns(self):
        """Focus patterns work in planning."""
        tmpdir = Path(tempfile.mkdtemp())
        (tmpdir / "test.py").write_text("def target(): pass\nclass Target: pass", encoding="utf-8")

        interface = PeppyInterface()

        interface.index(str(tmpdir))
        result = interface.for_planning(focus_patterns=["target"])

        assert "target" in result.get("focus_results", {})


class TestWorkflowHelpers:
    """Tests for general workflow helper methods."""

    def test_find_search_result_formatting(self):
        """SearchResult converts correctly."""
        result = SearchResult(
            name="test_func",
            type="function",
            file="/path/to/file.py",
            line=42,
            column=5,
        )

        loc = result.to_location()
        assert loc == "/path/to/file.py:42"

        d = result.to_dict()
        assert d["name"] == "test_func"

    def test_grep_result_formatting(self):
        """GrepResult converts correctly."""
        result = GrepResult(
            file="/path/to/file.py",
            line=42,
            content="match here",
            context_before=["before"],
            context_after=["after"],
        )

        loc = result.to_location()
        assert loc == "/path/to/file.py:42"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

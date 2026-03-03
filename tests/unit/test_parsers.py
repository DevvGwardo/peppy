"""Unit tests for CodeParser (multi-language parsing)."""

import pytest
from pathlib import Path
from peppy.parsers import CodeParser


class TestLanguageDetection:
    """Tests for language detection from file extensions."""

    def test_python_extension_detection(self):
        """Python extensions detected correctly."""
        parser = CodeParser()
        assert parser.get_language_from_extension("test.py") == "python"
        assert parser.get_language_from_extension("/path/to/test.py") == "python"

    def test_javascript_extensions(self):
        """JavaScript extensions detected correctly."""
        parser = CodeParser()
        assert parser.get_language_from_extension("test.js") == "javascript"
        assert parser.get_language_from_extension("test.jsx") == "javascript"

    def test_typescript_extensions(self):
        """TypeScript extensions detected correctly."""
        parser = CodeParser()
        assert parser.get_language_from_extension("test.ts") == "typescript"
        assert parser.get_language_from_extension("test.tsx") == "typescript"

    def test_unknown_extension_returns_none(self):
        """Unknown extensions return None."""
        parser = CodeParser()
        assert parser.get_language_from_extension("test.xyz") is None
        assert parser.get_language_from_extension("README") is None


class TestPythonParsing:
    """Tests for Python code parsing."""

    def test_python_functions_detected(self, sample_codebase):
        """Find functions and their locations."""
        parser = CodeParser()
        file_path = sample_codebase / "python" / "basic.py"

        symbols = parser.parse_file(str(file_path))

        functions = [s for s in symbols if s.type == "function"]
        assert len(functions) >= 2
        assert any(s.name == "hello_world" for s in functions)
        assert any(s.name == "calculate_sum" for s in functions)

    def test_python_classes_detected(self, sample_codebase):
        """Find classes and their locations."""
        parser = CodeParser()
        file_path = sample_codebase / "python" / "basic.py"

        symbols = parser.parse_file(str(file_path))

        classes = [s for s in symbols if s.type == "class"]
        assert len(classes) >= 1
        assert classes[0].name == "Calculator"

    def test_python_nested_classes(self, sample_codebase):
        """Deeply nested class structures."""
        parser = CodeParser()
        file_path = sample_codebase / "python" / "advanced.py"

        symbols = parser.parse_file(str(file_path))

        assert any(s.name == "Outer" for s in symbols)
        assert any(s.name == "Inner" for s in symbols)

    def test_python_decorators_and_async(self, sample_codebase):
        """Decorated and async functions."""
        parser = CodeParser()
        file_path = sample_codebase / "python" / "advanced.py"

        symbols = parser.parse_file(str(file_path))

        assert any(s.name == "fetch_data" for s in symbols)
        assert any(s.type in {"function", "method"} for s in symbols)


class TestJavaScriptParsing:
    """Tests for JavaScript code parsing."""

    def test_javascript_functions(self, sample_codebase):
        """Function declarations and expressions."""
        parser = CodeParser()
        file_path = sample_codebase / "javascript" / "sample.js"

        symbols = parser.parse_file(str(file_path))

        assert any(s.name == "calculateSum" for s in symbols)
        assert any(s.name == "fetchData" for s in symbols)

    def test_javascript_classes(self, sample_codebase):
        """Class definitions."""
        parser = CodeParser()
        file_path = sample_codebase / "javascript" / "sample.js"

        symbols = parser.parse_file(str(file_path))

        classes = [s for s in symbols if s.type == "class"]
        assert any(s.name == "Calculator" for s in classes)

    def test_javascript_arrow_functions(self, sample_codebase):
        """Arrow function syntax."""
        parser = CodeParser()
        file_path = sample_codebase / "javascript" / "sample.js"

        symbols = parser.parse_file(str(file_path))

        assert len(symbols) > 0


class TestTypeScriptParsing:
    """Tests for TypeScript code parsing."""

    def test_typescript_interfaces(self, sample_codebase):
        """Interface declarations."""
        parser = CodeParser()
        file_path = sample_codebase / "typescript" / "sample.ts"

        symbols = parser.parse_file(str(file_path))

        interfaces = [s for s in symbols if s.type == "interface"]
        assert len(interfaces) > 0

    def test_typescript_types(self, sample_codebase):
        """Type aliases."""
        parser = CodeParser()
        file_path = sample_codebase / "typescript" / "sample.ts"

        symbols = parser.parse_file(str(file_path))

        types = [s for s in symbols if s.type == "type"]
        assert len(types) > 0

    def test_typescript_generics(self, sample_codebase):
        """Generic type handling."""
        parser = CodeParser()
        file_path = sample_codebase / "typescript" / "sample.ts"

        symbols = parser.parse_file(str(file_path))

        assert any(s.name == "ApiClient" for s in symbols)


class TestGoParsing:
    """Tests for Go code parsing."""

    def test_go_functions(self, sample_codebase):
        """Function declarations."""
        parser = CodeParser()
        file_path = sample_codebase / "go" / "sample.go"

        symbols = parser.parse_file(str(file_path))

        assert any(s.name == "CalculateSum" for s in symbols)

    def test_go_structs_and_methods(self, sample_codebase):
        """Struct definitions and methods."""
        parser = CodeParser()
        file_path = sample_codebase / "go" / "sample.go"

        symbols = parser.parse_file(str(file_path))

        assert any(s.name == "User" for s in symbols)
        assert any(s.name == "GetUser" for s in symbols)


class TestRustParsing:
    """Tests for Rust code parsing."""

    def test_rust_functions(self, sample_codebase):
        """Function definitions."""
        parser = CodeParser()
        file_path = sample_codebase / "rust" / "sample.rs"

        symbols = parser.parse_file(str(file_path))

        assert any(s.name == "calculate_sum" for s in symbols)

    def test_rust_structs_and_impls(self, sample_codebase):
        """Struct and impl blocks."""
        parser = CodeParser()
        file_path = sample_codebase / "rust" / "sample.rs"

        symbols = parser.parse_file(str(file_path))

        assert any(s.name == "User" for s in symbols)


class TestFallbackParser:
    """Tests for fallback regex-based parser."""

    def test_fallback_python_parsing(self, tmp_path, mocker):
        """Regex-based Python parsing when tree-sitter unavailable."""
        mocker.patch("peppy.parsers.TREE_SITTER_AVAILABLE", False)

        parser = CodeParser()
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_func():\n    pass\n", encoding="utf-8")

        symbols = parser.parse_file(str(test_file))

        assert len(symbols) > 0

    def test_fallback_handles_syntax_errors(self, sample_codebase, mocker):
        """Invalid syntax doesn't crash fallback parser."""
        mocker.patch("peppy.parsers.TREE_SITTER_AVAILABLE", False)

        parser = CodeParser()
        file_path = sample_codebase / "python" / "errors.py"

        symbols = parser.parse_file(str(file_path))

        assert isinstance(symbols, list)


class TestParserEdgeCases:
    """Tests for parser edge cases."""

    def test_parser_empty_file(self, tmp_path):
        """Empty files return empty symbols."""
        parser = CodeParser()
        test_file = tmp_path / "empty.py"
        test_file.write_text("", encoding="utf-8")

        symbols = parser.parse_file(str(test_file))

        assert len(symbols) == 0

    def test_parser_unicode_handling(self, tmp_path):
        """Unicode in symbol names."""
        parser = CodeParser()
        test_file = tmp_path / "unicode.py"
        test_file.write_text(
            "def привет_world():\n    pass\ndef こんにちは():\n    pass\n", encoding="utf-8"
        )

        symbols = parser.parse_file(str(test_file))

        assert len(symbols) > 0


@pytest.fixture
def sample_codebase():
    """Fixture for sample codebase path."""
    return Path(__file__).parent.parent / "fixtures" / "sample_codebase"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

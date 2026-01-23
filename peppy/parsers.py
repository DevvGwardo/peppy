"""Tree-sitter parser utilities for extracting code symbols."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_go
    import tree_sitter_rust
    import tree_sitter_java
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class Symbol:
    """Represents a code symbol (function, class, variable, etc.)."""

    name: str
    type: str  # function, class, method, variable, etc.
    file_path: str
    line: int
    column: int
    end_line: int
    end_column: int
    context: Optional[str] = None  # The actual code snippet


class CodeParser:
    """Parser for extracting symbols from code using tree-sitter."""

    # Language-specific queries for extracting symbols
    QUERIES = {
        "python": """
            (function_definition name: (identifier) @function)
            (class_definition name: (identifier) @class)
            (assignment left: (identifier) @variable)
        """,
        "javascript": """
            (function_declaration name: (identifier) @function)
            (class_declaration name: (identifier) @class)
            (method_definition name: (property_identifier) @method)
            (variable_declarator name: (identifier) @variable)
        """,
        "typescript": """
            (function_declaration name: (identifier) @function)
            (class_declaration name: (type_identifier) @class)
            (method_definition name: (property_identifier) @method)
            (interface_declaration name: (type_identifier) @interface)
            (type_alias_declaration name: (type_identifier) @type)
        """,
        "go": """
            (function_declaration name: (identifier) @function)
            (method_declaration name: (field_identifier) @method)
            (type_declaration (type_spec name: (type_identifier) @type))
        """,
        "rust": """
            (function_item name: (identifier) @function)
            (struct_item name: (type_identifier) @struct)
            (enum_item name: (type_identifier) @enum)
            (impl_item type: (type_identifier) @impl)
        """,
        "java": """
            (method_declaration name: (identifier) @method)
            (class_declaration name: (identifier) @class)
            (interface_declaration name: (identifier) @interface)
        """,
    }

    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
    }

    def __init__(self):
        """Initialize the parser with tree-sitter languages."""
        self.parsers = {}
        self.languages = {}

        if not TREE_SITTER_AVAILABLE:
            return

        # Initialize parsers for each language
        language_map = {
            "python": tree_sitter_python,
            "javascript": tree_sitter_javascript,
            "typescript": tree_sitter_typescript,
            "go": tree_sitter_go,
            "rust": tree_sitter_rust,
            "java": tree_sitter_java,
        }

        for lang_name, lang_module in language_map.items():
            try:
                language = Language(lang_module.language())
                parser = Parser(language)
                self.languages[lang_name] = language
                self.parsers[lang_name] = parser
            except Exception as e:
                print(f"Warning: Failed to initialize {lang_name} parser: {e}")

    def get_language_from_extension(self, file_path: str) -> Optional[str]:
        """Determine the language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None if not supported
        """
        ext = os.path.splitext(file_path)[1].lower()
        return self.LANGUAGE_EXTENSIONS.get(ext)

    def parse_file(self, file_path: str) -> List[Symbol]:
        """Parse a file and extract symbols.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of extracted symbols
        """
        if not TREE_SITTER_AVAILABLE:
            return self._parse_file_fallback(file_path)

        language = self.get_language_from_extension(file_path)
        if not language or language not in self.parsers:
            return self._parse_file_fallback(file_path)

        try:
            with open(file_path, "rb") as f:
                code = f.read()

            parser = self.parsers[language]
            tree = parser.parse(code)

            return self._extract_symbols(tree.root_node, code.decode("utf-8"), file_path, language)

        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return self._parse_file_fallback(file_path)

    def _extract_symbols(self, root_node: 'Node', code: str, file_path: str, language: str) -> List[Symbol]:
        """Extract symbols from a tree-sitter AST.

        Args:
            root_node: Root node of the AST
            code: Source code string
            file_path: Path to the source file
            language: Programming language

        Returns:
            List of symbols
        """
        symbols = []

        # Walk the tree and extract symbols
        def walk_tree(node: 'Node', parent_type: Optional[str] = None):
            node_type = node.type

            # Check for function definitions
            if node_type in ['function_definition', 'function_declaration', 'function_item', 'method_declaration', 'method_definition']:
                name_node = self._find_name_node(node)
                if name_node:
                    symbol_type = 'method' if parent_type == 'class' else 'function'
                    symbols.append(self._create_symbol(name_node, symbol_type, file_path, code))

            # Check for class definitions
            elif node_type in ['class_definition', 'class_declaration', 'struct_item', 'enum_item']:
                name_node = self._find_name_node(node)
                if name_node:
                    symbols.append(self._create_symbol(name_node, 'class', file_path, code))
                    parent_type = 'class'

            # Check for interface/type definitions
            elif node_type in ['interface_declaration', 'type_alias_declaration']:
                name_node = self._find_name_node(node)
                if name_node:
                    symbols.append(self._create_symbol(name_node, 'interface', file_path, code))

            # Recurse into children
            for child in node.children:
                walk_tree(child, parent_type)

        walk_tree(root_node)
        return symbols

    def _find_name_node(self, node: 'Node') -> Optional['Node']:
        """Find the name node within a definition node."""
        for child in node.children:
            if child.type in ['identifier', 'type_identifier', 'property_identifier', 'field_identifier']:
                return child
            # Recursively search in named children
            if child.is_named:
                result = self._find_name_node(child)
                if result:
                    return result
        return None

    def _create_symbol(self, node: 'Node', symbol_type: str, file_path: str, code: str) -> Symbol:
        """Create a Symbol object from a tree-sitter node."""
        start_point = node.start_point
        end_point = node.end_point
        name = code[node.start_byte:node.end_byte]

        return Symbol(
            name=name,
            type=symbol_type,
            file_path=file_path,
            line=start_point[0] + 1,  # Convert to 1-indexed
            column=start_point[1],
            end_line=end_point[0] + 1,
            end_column=end_point[1],
            context=None
        )

    def _parse_file_fallback(self, file_path: str) -> List[Symbol]:
        """Fallback parser using simple regex patterns.

        Used when tree-sitter is not available or parsing fails.

        Args:
            file_path: Path to the file

        Returns:
            List of symbols extracted using simple pattern matching
        """
        import re

        symbols = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            language = self.get_language_from_extension(file_path)

            if language == "python":
                # Simple regex for Python functions and classes
                for i, line in enumerate(lines):
                    # Match function definitions
                    match = re.match(r'^\s*def\s+(\w+)\s*\(', line)
                    if match:
                        symbols.append(Symbol(
                            name=match.group(1),
                            type='function',
                            file_path=file_path,
                            line=i + 1,
                            column=match.start(1),
                            end_line=i + 1,
                            end_column=match.end(1)
                        ))

                    # Match class definitions
                    match = re.match(r'^\s*class\s+(\w+)', line)
                    if match:
                        symbols.append(Symbol(
                            name=match.group(1),
                            type='class',
                            file_path=file_path,
                            line=i + 1,
                            column=match.start(1),
                            end_line=i + 1,
                            end_column=match.end(1)
                        ))

        except Exception as e:
            print(f"Warning: Fallback parsing failed for {file_path}: {e}")

        return symbols

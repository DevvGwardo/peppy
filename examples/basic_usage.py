"""Basic usage examples for Peppy."""

from pathlib import Path
from peppy import CodebaseIndexer, CodebaseSearcher
from peppy.cache import IndexCache


def main():
    """Demonstrate basic Peppy usage."""

    # Initialize cache, indexer, and searcher
    cache = IndexCache()
    indexer = CodebaseIndexer(cache)
    searcher = CodebaseSearcher(cache)

    # Example: Index the current directory
    codebase_path = Path.cwd()
    print(f"Indexing codebase at: {codebase_path}")

    # Index the codebase
    index = indexer.index_codebase(codebase_path)
    print(f"\nIndexed {index['total_files']} files with {index['symbol_count']} symbols")

    # Get statistics
    stats = searcher.get_statistics(codebase_path)
    print(f"\nStatistics:")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Total symbols: {stats['total_symbols']}")
    print(f"\n  Symbol types:")
    for sym_type, count in sorted(stats['symbol_types'].items()):
        print(f"    {sym_type}: {count}")

    # Search for symbols
    print("\n" + "=" * 60)
    print("Searching for symbols containing 'index'...")
    results = searcher.search_symbols(codebase_path, "index", use_regex=False)
    for result in results[:10]:
        print(f"  {result['type']:10} {result['name']:30} {result['file']}:{result['line']}")

    # Grep for code patterns
    print("\n" + "=" * 60)
    print("Grepping for 'def ' pattern...")
    grep_results = searcher.grep_code(
        codebase_path,
        r"def \w+",
        file_pattern="*.py",
        context_lines=1,
        max_results=5
    )
    for result in grep_results:
        print(f"\n{result['file']}:{result['line']}")
        if result.get('context'):
            ctx = result['context']
            for line in ctx.get('before', []):
                print(f"  {line['line']:4d} | {line['content']}")
            match = ctx['match']
            print(f"→ {match['line']:4d} | {match['content']}")
            for line in ctx.get('after', []):
                print(f"  {line['line']:4d} | {line['content']}")


if __name__ == "__main__":
    main()

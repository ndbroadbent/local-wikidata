"""
Command-line interface for local-wikidata.

Usage:
    python -m src.cli import [--dump PATH] [--db PATH]
    python -m src.cli get <entity_id>
    python -m src.cli search <query> [--limit N]
    python -m src.cli stats
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .config import settings
from .database import get_entity, get_stats, search_entities
from .importer import import_dump


def cmd_import(args: argparse.Namespace) -> int:
    """Run the import command."""
    dump_path = Path(args.dump) if args.dump else None
    db_path = Path(args.db) if args.db else None

    try:
        import_dump(dump_path=dump_path, db_path=db_path)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nImport interrupted. Progress saved - run again to resume.")
        return 130


def cmd_get(args: argparse.Namespace) -> int:
    """Get an entity by ID."""
    entity = asyncio.run(get_entity(args.entity_id))
    if entity:
        print(json.dumps(entity, indent=2))
        return 0
    else:
        print(f"Entity {args.entity_id} not found", file=sys.stderr)
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """Search for entities."""
    results = asyncio.run(search_entities(args.query, args.limit))
    for r in results:
        label = r.get("label") or "(no label)"
        desc = r.get("description") or "(no description)"
        print(f"{r['id']}: {label} - {desc}")
    if not results:
        print("No results found")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show database statistics."""
    stats = asyncio.run(get_stats())
    print(f"Total entities: {stats['total']:,}")
    for entity_type, count in stats.get("by_type", {}).items():
        print(f"  {entity_type}: {count:,}")
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="local-wikidata: Self-hosted Wikidata mirror",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import Wikidata dump")
    import_parser.add_argument(
        "--dump",
        help=f"Path to bz2 dump file (default: {settings.dump_path})",
    )
    import_parser.add_argument(
        "--db",
        help=f"Path to SQLite database (default: {settings.database_path})",
    )

    # Get command
    get_parser = subparsers.add_parser("get", help="Get entity by ID")
    get_parser.add_argument("entity_id", help="Entity ID (e.g., Q152017)")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search entities")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--limit", "-n", type=int, default=10, help="Max results (default: 10)"
    )

    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")

    args = parser.parse_args()

    if args.command == "import":
        return cmd_import(args)
    elif args.command == "get":
        return cmd_get(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "stats":
        return cmd_stats(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

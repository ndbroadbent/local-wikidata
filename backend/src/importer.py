"""
Wikidata JSON dump importer.

Streams compressed bz2 dumps and imports to SQLite.
Idempotent: can be resumed, uses upserts.
"""

import bz2
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from .config import settings
from .schema import SCHEMA

# Import configuration
BATCH_SIZE = 10000
REPORT_INTERVAL = 100000


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize database with schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    conn.commit()
    return conn


def load_progress(progress_path: Path) -> dict[str, Any]:
    """Load import progress from file."""
    if progress_path.exists():
        with open(progress_path) as f:
            return json.load(f)
    return {"bytes_read": 0, "entities_imported": 0, "last_id": None}


def save_progress(progress_path: Path, progress: dict[str, Any]) -> None:
    """Save import progress to file."""
    with open(progress_path, "w") as f:
        json.dump(progress, f)


def parse_entity(line: str) -> dict[str, Any] | None:
    """Parse a single entity line from the dump."""
    line = line.strip()
    if not line or line in ("[", "]"):
        return None
    # Remove trailing comma if present
    if line.endswith(","):
        line = line[:-1]
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def extract_entity_data(entity: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant fields from entity."""
    return {
        "id": entity.get("id"),
        "type": entity.get("type"),
        "labels_json": json.dumps(entity.get("labels", {})),
        "descriptions_json": json.dumps(entity.get("descriptions", {})),
        "aliases_json": json.dumps(entity.get("aliases", {})),
        "claims_json": json.dumps(entity.get("claims", {})),
        "sitelinks_json": json.dumps(entity.get("sitelinks", {})),
        "modified": entity.get("modified"),
    }


def import_dump(
    dump_path: Path | None = None,
    db_path: Path | None = None,
    progress_path: Path | None = None,
) -> None:
    """
    Import Wikidata JSON dump to SQLite.

    Args:
        dump_path: Path to the bz2 compressed dump file
        db_path: Path to the SQLite database
        progress_path: Path to the progress tracking file
    """
    # Use defaults from settings if not provided
    dump_path = dump_path or Path(settings.dump_path)
    db_path = db_path or Path(settings.database_path)
    progress_path = progress_path or db_path.with_suffix(".progress.json")

    print("Starting Wikidata import")
    print(f"  Dump: {dump_path}")
    print(f"  Database: {db_path}")
    print(f"  Progress: {progress_path}")

    if not dump_path.exists():
        raise FileNotFoundError(f"Dump file not found: {dump_path}")

    conn = init_db(db_path)
    progress = load_progress(progress_path)

    start_bytes = progress["bytes_read"]
    entities_imported = progress["entities_imported"]

    print(f"Resuming from byte {start_bytes:,}, {entities_imported:,} entities imported")

    batch: list[dict[str, Any]] = []
    bytes_read = 0
    start_time = time.time()
    last_report_time = start_time

    with bz2.open(dump_path, "rt", encoding="utf-8") as f:
        # Skip to resume point (approximate - we'll re-process some)
        if start_bytes > 0:
            print("Seeking to approximate resume point...")
            skipped = 0
            while skipped < start_bytes:
                line = f.readline()
                if not line:
                    break
                skipped += len(line.encode("utf-8"))
            print(f"Skipped ~{skipped:,} bytes")

        for line in f:
            bytes_read += len(line.encode("utf-8"))

            entity = parse_entity(line)
            if entity and entity.get("id"):
                data = extract_entity_data(entity)
                batch.append(data)

                if len(batch) >= BATCH_SIZE:
                    # Upsert batch
                    conn.executemany(
                        """
                        INSERT OR REPLACE INTO entities
                        (id, type, labels_json, descriptions_json, aliases_json,
                         claims_json, sitelinks_json, modified)
                        VALUES (:id, :type, :labels_json, :descriptions_json,
                                :aliases_json, :claims_json, :sitelinks_json, :modified)
                        """,
                        batch,
                    )
                    conn.commit()

                    entities_imported += len(batch)
                    batch = []

                    # Save progress periodically
                    if entities_imported % REPORT_INTERVAL == 0:
                        progress = {
                            "bytes_read": start_bytes + bytes_read,
                            "entities_imported": entities_imported,
                            "last_id": data["id"],
                        }
                        save_progress(progress_path, progress)

                        elapsed = time.time() - last_report_time
                        rate = REPORT_INTERVAL / elapsed if elapsed > 0 else 0
                        total_elapsed = time.time() - start_time

                        print(
                            f"Imported {entities_imported:,} entities "
                            f"({rate:.0f}/sec, last: {data['id']}, "
                            f"elapsed: {total_elapsed / 3600:.1f}h)"
                        )
                        last_report_time = time.time()

        # Final batch
        if batch:
            conn.executemany(
                """
                INSERT OR REPLACE INTO entities
                (id, type, labels_json, descriptions_json, aliases_json,
                 claims_json, sitelinks_json, modified)
                VALUES (:id, :type, :labels_json, :descriptions_json,
                        :aliases_json, :claims_json, :sitelinks_json, :modified)
                """,
                batch,
            )
            conn.commit()
            entities_imported += len(batch)

    # Final progress save
    progress = {
        "bytes_read": start_bytes + bytes_read,
        "entities_imported": entities_imported,
        "last_id": batch[-1]["id"] if batch else progress.get("last_id"),
        "completed": True,
    }
    save_progress(progress_path, progress)

    total_time = time.time() - start_time
    print("\nImport complete!")
    print(f"Total entities: {entities_imported:,}")
    print(f"Total time: {total_time / 3600:.1f} hours")

    conn.close()


if __name__ == "__main__":
    import_dump()

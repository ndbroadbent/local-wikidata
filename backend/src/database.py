"""Database operations for local Wikidata mirror."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import settings

# Schema for the database
SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    labels_json TEXT,
    descriptions_json TEXT,
    aliases_json TEXT,
    claims_json TEXT,
    sitelinks_json TEXT,
    modified TEXT,
    imported_at TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    id,
    label_en,
    description_en,
    aliases_en,
    content=entities,
    content_rowid=rowid
);

CREATE TRIGGER IF NOT EXISTS entities_ai AFTER INSERT ON entities BEGIN
    INSERT INTO entities_fts(rowid, id, label_en, description_en, aliases_en)
    VALUES (
        new.rowid,
        new.id,
        json_extract(new.labels_json, '$.en.value'),
        json_extract(new.descriptions_json, '$.en.value'),
        json_extract(new.aliases_json, '$.en')
    );
END;

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
"""


def get_connection() -> sqlite3.Connection:
    """Get a database connection, creating the database if needed."""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _parse_entity_row(row: sqlite3.Row) -> dict[str, Any]:
    """Parse a database row into an entity dict."""
    return {
        "id": row["id"],
        "type": row["type"],
        "labels": json.loads(row["labels_json"]) if row["labels_json"] else {},
        "descriptions": json.loads(row["descriptions_json"]) if row["descriptions_json"] else {},
        "aliases": json.loads(row["aliases_json"]) if row["aliases_json"] else {},
        "claims": json.loads(row["claims_json"]) if row["claims_json"] else {},
        "sitelinks": json.loads(row["sitelinks_json"]) if row["sitelinks_json"] else {},
        "modified": row["modified"],
    }


async def get_entity(entity_id: str) -> dict[str, Any] | None:
    """Fetch an entity by ID."""
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id.upper(),))
        row = cur.fetchone()
        if row:
            return _parse_entity_row(row)
        # TODO: Implement write-through cache (fetch from Wikidata API)
        return None
    finally:
        conn.close()


async def search_entities(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search entities by label or description."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT e.id, e.type,
                   json_extract(e.labels_json, '$.en.value') as label,
                   json_extract(e.descriptions_json, '$.en.value') as description
            FROM entities_fts fts
            JOIN entities e ON e.rowid = fts.rowid
            WHERE entities_fts MATCH ?
            LIMIT ?
            """,
            (query, limit),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


async def get_stats() -> dict[str, Any]:
    """Get database statistics."""
    conn = get_connection()
    try:
        cur = conn.execute("SELECT type, COUNT(*) as count FROM entities GROUP BY type")
        type_counts = dict(cur.fetchall())

        cur = conn.execute("SELECT COUNT(*) FROM entities")
        total = cur.fetchone()[0]

        return {"total": total, "by_type": type_counts}
    finally:
        conn.close()

"""Database schema for local Wikidata mirror."""

SCHEMA = """
-- Wikidata local mirror schema
-- SQLite with FTS5 for full-text search

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,           -- Q123 or P456
    type TEXT NOT NULL,            -- item or property
    labels_json TEXT,              -- {"en": {"value": "Label"}, ...}
    descriptions_json TEXT,        -- {"en": {"value": "Description"}, ...}
    aliases_json TEXT,             -- {"en": [{"value": "alias1"}, ...], ...}
    claims_json TEXT,              -- Full claims/statements
    sitelinks_json TEXT,           -- Wikipedia links etc
    modified TEXT,                 -- Last modified timestamp from Wikidata
    imported_at TEXT DEFAULT (datetime('now'))
);

-- Full-text search on English labels and descriptions
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    id,
    label_en,
    description_en,
    aliases_en,
    content=entities,
    content_rowid=rowid
);

-- Trigger to keep FTS in sync on INSERT
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

-- Trigger to keep FTS in sync on DELETE
CREATE TRIGGER IF NOT EXISTS entities_ad AFTER DELETE ON entities BEGIN
    INSERT INTO entities_fts(entities_fts, rowid, id, label_en, description_en, aliases_en)
    VALUES ('delete', old.rowid, old.id,
        json_extract(old.labels_json, '$.en.value'),
        json_extract(old.descriptions_json, '$.en.value'),
        json_extract(old.aliases_json, '$.en')
    );
END;

-- Trigger to keep FTS in sync on UPDATE
CREATE TRIGGER IF NOT EXISTS entities_au AFTER UPDATE ON entities BEGIN
    INSERT INTO entities_fts(entities_fts, rowid, id, label_en, description_en, aliases_en)
    VALUES ('delete', old.rowid, old.id,
        json_extract(old.labels_json, '$.en.value'),
        json_extract(old.descriptions_json, '$.en.value'),
        json_extract(old.aliases_json, '$.en')
    );
    INSERT INTO entities_fts(rowid, id, label_en, description_en, aliases_en)
    VALUES (
        new.rowid,
        new.id,
        json_extract(new.labels_json, '$.en.value'),
        json_extract(new.descriptions_json, '$.en.value'),
        json_extract(new.aliases_json, '$.en')
    );
END;

-- Index for type filtering
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
"""

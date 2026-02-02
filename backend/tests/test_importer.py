"""Tests for the importer module."""

import json

from src.importer import extract_entity_data, parse_entity


def test_parse_entity_valid() -> None:
    """Test parsing a valid entity line."""
    line = '{"id": "Q1", "type": "item", "labels": {"en": {"value": "Universe"}}},'
    entity = parse_entity(line)
    assert entity is not None
    assert entity["id"] == "Q1"
    assert entity["type"] == "item"


def test_parse_entity_without_comma() -> None:
    """Test parsing entity without trailing comma."""
    line = '{"id": "Q1", "type": "item"}'
    entity = parse_entity(line)
    assert entity is not None
    assert entity["id"] == "Q1"


def test_parse_entity_empty() -> None:
    """Test parsing empty lines."""
    assert parse_entity("") is None
    assert parse_entity("[") is None
    assert parse_entity("]") is None
    assert parse_entity("  ") is None


def test_parse_entity_invalid_json() -> None:
    """Test parsing invalid JSON."""
    assert parse_entity("{invalid json}") is None


def test_extract_entity_data() -> None:
    """Test extracting data from entity."""
    entity = {
        "id": "Q152017",
        "type": "item",
        "labels": {"en": {"value": "Paihia"}},
        "descriptions": {"en": {"value": "town in New Zealand"}},
        "aliases": {"en": [{"value": "Paihia, New Zealand"}]},
        "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5119"}}}}]},
        "sitelinks": {"enwiki": {"title": "Paihia"}},
        "modified": "2024-01-01T00:00:00Z",
    }

    data = extract_entity_data(entity)

    assert data["id"] == "Q152017"
    assert data["type"] == "item"
    assert data["modified"] == "2024-01-01T00:00:00Z"

    # Check JSON fields are serialized
    labels = json.loads(data["labels_json"])
    assert labels["en"]["value"] == "Paihia"


def test_extract_entity_data_minimal() -> None:
    """Test extracting data from minimal entity."""
    entity = {"id": "Q1", "type": "item"}

    data = extract_entity_data(entity)

    assert data["id"] == "Q1"
    assert data["type"] == "item"
    assert json.loads(data["labels_json"]) == {}
    assert data["modified"] is None

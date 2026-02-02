"""FastAPI application for local-wikidata."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import get_entity, get_stats, search_entities

app = FastAPI(
    title="local-wikidata",
    description="Self-hosted Wikidata mirror API",
    version="0.1.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/entity/{entity_id}")
async def get_entity_by_id(entity_id: str) -> dict:
    """
    Get an entity by its Wikidata ID.

    Args:
        entity_id: Wikidata entity ID (e.g., Q152017 or P31)

    Returns:
        Entity data with labels, descriptions, claims, etc.
    """
    entity = await get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    return entity


@app.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
) -> dict:
    """
    Search for entities by label or description.

    Args:
        q: Search query string
        limit: Maximum number of results (1-100)

    Returns:
        List of matching entities
    """
    results = await search_entities(q, limit)
    return {"query": q, "results": results}


@app.get("/stats")
async def stats() -> dict:
    """
    Get database statistics.

    Returns:
        Total entity count and breakdown by type
    """
    return await get_stats()

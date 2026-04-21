"""Routes for the local character registry."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file, abort

from core.character_registry import get_registry

logger = logging.getLogger(__name__)

characters_bp = Blueprint("characters", __name__, url_prefix="/api/characters")


@characters_bp.get("")
@characters_bp.get("/")
def list_characters():
    """List/search characters.

    Query params:
        q: free-text search across display_name, aliases, character_tag.
        series: filter by series_key or series alias (GI, HSR, ...).
        limit: max results (default 50, capped at 200).
    """
    q = request.args.get("q", "", type=str)
    series = request.args.get("series", "", type=str) or None
    limit = min(max(request.args.get("limit", 50, type=int), 1), 200)
    reg = get_registry()
    results = reg.find(query=q, series_filter=series, limit=limit)
    return jsonify({
        "characters": [r.to_dict() for r in results],
        "count": len(results),
        "query": q,
        "series_filter": series,
    })


@characters_bp.get("/series")
def list_series():
    reg = get_registry()
    return jsonify({"series": reg.list_series()})


@characters_bp.get("/<key>")
def get_character(key: str):
    reg = get_registry()
    rec = reg.get(key)
    if rec is None:
        return jsonify({"error": "not_found", "key": key}), 404
    collisions = reg.detect_collisions(rec.display_name)
    return jsonify({
        "character": rec.to_dict(),
        "collisions": [c.to_dict() for c in collisions if c.key != rec.key],
    })


@characters_bp.get("/<key>/thumbnail")
def get_thumbnail(key: str):
    reg = get_registry()
    rec = reg.get(key)
    if rec is None:
        abort(404)
    if not rec.thumbnail:
        abort(404)
    # Resolve relative to repo root (4 levels up from this file)
    repo_root = Path(__file__).resolve().parents[3]
    thumb_path = (repo_root / rec.thumbnail).resolve()
    # Security: ensure path stays under repo root
    try:
        thumb_path.relative_to(repo_root)
    except ValueError:
        abort(403)
    if not thumb_path.exists() or not thumb_path.is_file():
        abort(404)
    return send_file(str(thumb_path))


@characters_bp.post("/reload")
def reload_registry():
    """Force-reload the registry from disk (admin/dev convenience)."""
    reg = get_registry()
    reg.reload()
    return jsonify({"reloaded": True, "count": len(reg.list_all())})


@characters_bp.post("/resolve")
def resolve_query():
    """Resolve a free-form query to a single character record."""
    payload = request.get_json(silent=True) or {}
    q = (payload.get("query") or "").strip()
    if not q:
        return jsonify({"error": "query_required"}), 400
    reg = get_registry()
    rec = reg.resolve_query(q)
    if rec is None:
        return jsonify({"resolved": False, "query": q})
    return jsonify({"resolved": True, "query": q, "character": rec.to_dict()})

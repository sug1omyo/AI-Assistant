"""
Skills CRUD router — /api/skills/*

Provides endpoints for listing, fetching, activating, and deactivating
runtime skills via the FastAPI path.
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.skills.registry import get_skill_registry
from core.skills.session import get_session_skill, set_session_skill, clear_session_skill
from core.extensions import logger

router = APIRouter()


class ActivateSkillRequest(BaseModel):
    skill_id: str


def _get_session_id(request: Request) -> Optional[str]:
    """Extract session_id from the request state (set by middleware) or cookies."""
    # FastAPI session middleware stores session in request.state or cookies
    sid = getattr(request.state, 'session_id', None)
    if sid:
        return sid
    return request.cookies.get('session_id')


@router.get("/api/skills")
async def list_skills(include_disabled: bool = False, tag: Optional[str] = None):
    """List available runtime skills."""
    registry = get_skill_registry()

    if include_disabled:
        skills = registry.list_all()
    else:
        skills = registry.list_ui_visible()

    if tag:
        tags = [t.strip() for t in tag.split(',')]
        skills = [s for s in skills if any(t in s.tags for t in tags)]

    result = []
    for s in skills:
        result.append({
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'default_model': s.default_model,
            'default_thinking_mode': s.default_thinking_mode,
            'default_context': s.default_context,
            'preferred_tools': s.preferred_tools,
            'blocked_tools': s.blocked_tools,
            'tags': s.tags,
            'enabled': s.enabled,
            'ui_visible': s.ui_visible,
        })

    return {'skills': result, 'total': len(result)}


@router.get("/api/skills/{skill_id}")
async def get_skill(skill_id: str):
    """Fetch a single skill by id."""
    registry = get_skill_registry()
    skill = registry.get(skill_id)
    if skill is None:
        skill = registry.get_by_name(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f'Skill not found: {skill_id}')

    return {
        'skill': {
            'id': skill.id,
            'name': skill.name,
            'description': skill.description,
            'prompt_fragments': skill.prompt_fragments,
            'default_model': skill.default_model,
            'default_thinking_mode': skill.default_thinking_mode,
            'default_context': skill.default_context,
            'preferred_tools': skill.preferred_tools,
            'blocked_tools': skill.blocked_tools,
            'trigger_keywords': skill.trigger_keywords,
            'tags': skill.tags,
            'enabled': skill.enabled,
            'ui_visible': skill.ui_visible,
            'builtin': skill.builtin,
            'priority': skill.priority,
        }
    }


@router.post("/api/skills/activate")
async def activate_skill(body: ActivateSkillRequest, request: Request):
    """Set the active skill for the current session."""
    skill_id = body.skill_id.strip()
    if not skill_id:
        raise HTTPException(status_code=400, detail='skill_id is required')

    registry = get_skill_registry()
    skill = registry.get(skill_id)
    if skill is None:
        skill = registry.get_by_name(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f'Skill not found: {skill_id}')
    if not skill.enabled:
        raise HTTPException(status_code=400, detail=f'Skill is disabled: {skill.id}')

    session_id = _get_session_id(request)
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())

    set_session_skill(session_id, skill.id)
    logger.info(f"[Skills] Activated skill '{skill.id}' for session {session_id[:8]}...")

    return {
        'success': True,
        'skill_id': skill.id,
        'skill_name': skill.name,
        'session_id': session_id,
    }


@router.post("/api/skills/deactivate")
async def deactivate_skill(request: Request):
    """Clear the active skill for the current session."""
    session_id = _get_session_id(request)
    if not session_id:
        return {'success': True, 'had_active': False}

    had_active = clear_session_skill(session_id)
    if had_active:
        logger.info(f"[Skills] Deactivated skill for session {session_id[:8]}...")

    return {'success': True, 'had_active': had_active}


@router.get("/api/skills/active")
async def get_active_skill(request: Request):
    """Get the currently active skill for this session."""
    session_id = _get_session_id(request)
    if not session_id:
        return {'skill_id': None, 'active': False}

    active_id = get_session_skill(session_id)
    if not active_id:
        return {'skill_id': None, 'active': False}

    registry = get_skill_registry()
    skill = registry.get(active_id)
    if skill is None:
        clear_session_skill(session_id)
        return {'skill_id': None, 'active': False}

    return {
        'skill_id': skill.id,
        'skill_name': skill.name,
        'active': True,
    }

"""
Shared API dependencies.

Re-exports commonly used dependencies and provides pagination helpers.
"""

from typing import Optional

from fastapi import Query

from app.core.database import get_db
from app.core.security import (
    get_current_active_user,
    get_current_user,
)


async def pagination_params(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
) -> dict:
    """Standard pagination dependency.

    Returns a dict with validated page and page_size, plus a computed offset.
    """
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
    }

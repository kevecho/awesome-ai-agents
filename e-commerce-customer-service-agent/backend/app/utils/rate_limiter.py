"""
Rate limiting middleware using Redis sliding window.

Provides per-IP and per-user rate limiting for API endpoints.
"""

from typing import Optional

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.utils.cache import increment_counter


async def check_rate_limit(
    request: Request,
    user_id: Optional[int] = None,
) -> None:
    """Check if the current request exceeds rate limits.

    Uses a sliding window counter in Redis. Identifies callers by
    user ID (if authenticated) or client IP.

    Args:
        request: FastAPI request object.
        user_id: Authenticated user ID, or None to use IP-based limiting.

    Raises:
        HTTPException 429: If rate limit is exceeded.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    identifier = f"user:{user_id}" if user_id else f"ip:{request.client.host}"
    key = f"rate_limit:{identifier}"

    try:
        count = await increment_counter(key, ttl=settings.RATE_LIMIT_WINDOW_SECONDS)
    except Exception:
        # Fail open if Redis is unavailable
        return

    if count > settings.RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(settings.RATE_LIMIT_WINDOW_SECONDS)},
        )

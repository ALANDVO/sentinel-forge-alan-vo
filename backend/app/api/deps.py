"""FastAPI dependencies for database sessions and authentication."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.services.database import Database


def get_db(request: Request) -> Session:
    """Yield a database session from the app's Database instance."""
    db: Database = request.app.state.db
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()


class AuthContext:
    """Lightweight authentication context (stepping stone to full OIDC)."""

    def __init__(self, user: Optional[str], role: str):
        self.user = user
        self.role = role

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None


def _check_api_key(request: Request) -> Optional[str]:
    """Extract and validate an API key from the request headers."""
    settings = request.app.state.settings
    if not settings.api_key:
        return None
    header_val = request.headers.get("X-API-Key") or request.headers.get(
        "Authorization", ""
    ).removeprefix("Bearer ").strip()
    if header_val and header_val == settings.api_key:
        return "api_user"
    return None


def get_current_user(
    request: Request,
) -> Optional[AuthContext]:
    """Resolve the current user from demo mode, API key, or session.

    Returns None if unauthenticated (endpoints that require auth should
    use ``require_auth`` instead).
    """
    settings = request.app.state.settings
    # Demo mode: auto-authenticate to a demo admin on localhost only.
    if settings.demo_mode_active():
        return AuthContext(user="demo_user", role="admin")

    user = _check_api_key(request)
    if user:
        return AuthContext(user=user, role="admin")

    return None


def require_auth(
    ctx: Annotated[Optional[AuthContext], Depends(get_current_user)],
) -> AuthContext:
    """Dependency that rejects unauthenticated requests with 401."""
    if ctx is None or not ctx.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return ctx
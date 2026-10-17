"""Authentication endpoints.

Full OIDC/Keycloak SSO is a planned future milestone. In the meantime, this
module exposes a verify endpoint that reflects the current auth context
(demo mode auto-auth or API key validation) and a logout endpoint that
clears any session state.

Production deployment requires OIDC; demo mode is strictly localhost-only.
"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import AuthContext, get_current_user
from app.models.schemas import AuthVerifyResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/verify", response_model=AuthVerifyResponse)
async def verify_auth(
    ctx: Annotated[Optional[AuthContext], Depends(get_current_user)],
) -> AuthVerifyResponse:
    """Return the current authentication status."""
    if ctx is not None and ctx.is_authenticated:
        return AuthVerifyResponse(
            authenticated=True, user=ctx.user, role=ctx.role
        )
    return AuthVerifyResponse(authenticated=False)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> dict:
    """Clear auth session state."""
    response.delete_cookie("session")
    return {"status": "logged_out"}
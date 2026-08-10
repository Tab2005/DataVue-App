"""Teams module (teams + invites)."""

from .router import router
from .invites_router import router as invites_router

__all__ = ["router", "invites_router"]

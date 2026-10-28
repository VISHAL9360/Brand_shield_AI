from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    RequireRole,
    get_current_user,
    require_role,
    security_bearer,
)
from app.domain.enums import UserRole
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_async_session

# Strict Type-Annotated Dependencies for FastAPI Route Handlers
# NOTE for Frontend DX: When ENVIRONMENT != 'production', clients may supply the
# optional development header 'X-Demo-Role: CREATOR | REVIEWER | ADMINISTRATOR'
# to automatically authenticate as that role without a JWT token.
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(RequireRole(UserRole.ADMINISTRATOR))]
ReviewerUser = Annotated[User, Depends(RequireRole(UserRole.REVIEWER, UserRole.ADMINISTRATOR))]
CreatorUser = Annotated[User, Depends(RequireRole(UserRole.CREATOR, UserRole.ADMINISTRATOR))]
AuditorUser = Annotated[User, Depends(RequireRole(UserRole.REVIEWER, UserRole.ADMINISTRATOR))]

__all__ = [
    "AdminUser",
    "AuditorUser",
    "CreatorUser",
    "CurrentUser",
    "RequireRole",
    "ReviewerUser",
    "SessionDep",
    "get_async_session",
    "get_current_user",
    "require_role",
    "security_bearer",
]


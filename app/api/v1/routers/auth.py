"""
BrandShield AI - Authentication & Cryptographic Session Router.
Handles Argon2id user registration, JWT token generation, token refresh cycles,
and current user profile resolution with full cryptographic audit logging.
"""

from datetime import datetime, timezone
from typing import Annotated, Any
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictProblem, NotFoundProblem, UnauthorizedProblem
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.domain.enums import AuditAction, UserRole
from app.domain.schemas.user import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserRead,
    UserRegisterRequest,
)
from app.infrastructure.db.models import User, Workspace
from app.infrastructure.db.session import get_async_session
from app.services.audit_service import AuditService

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Registers a new tenant actor with Argon2id password hashing and audit chain commitment.
    """
    # Resolve or provision tenant workspace
    workspace: Workspace | None = None
    if payload.workspace_id:
        workspace = await session.get(Workspace, payload.workspace_id)
        if not workspace:
            raise NotFoundProblem(
                detail=f"Workspace with ID {payload.workspace_id} not found.",
                resource_type="Workspace",
                resource_id=str(payload.workspace_id),
            )
    else:
        # Default or provision workspace by slug/name
        ws_slug = payload.workspace_slug or f"ws-{uuid.uuid4().hex[:8]}"
        ws_name = payload.workspace_name or "Default Workspace"
        existing_ws_query = select(Workspace).where(Workspace.slug == ws_slug)
        res = await session.execute(existing_ws_query)
        workspace = res.scalar_one_or_none()
        if not workspace:
            workspace = Workspace(name=ws_name, slug=ws_slug)
            session.add(workspace)
            await session.flush()
            await AuditService.record_event(
                session=session,
                action=AuditAction.WORKSPACE_CREATED,
                workspace_id=workspace.id,
                payload={"workspace_id": str(workspace.id), "slug": ws_slug, "name": ws_name},
            )

    # Check for existing user with identical email within workspace
    existing_user_query = select(User).where(
        User.workspace_id == workspace.id,
        User.email == payload.email,
    )
    existing_res = await session.execute(existing_user_query)
    if existing_res.scalar_one_or_none():
        raise ConflictProblem(
            detail=f"User with email '{payload.email}' already exists in this workspace.",
        )

    # Compute Argon2id hash
    hashed_pwd = hash_password(payload.password)

    new_user = User(
        workspace_id=workspace.id,
        email=payload.email,
        hashed_password=hashed_pwd,
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    session.add(new_user)
    await session.flush()

    # Commit event to cryptographic audit ledger
    await AuditService.record_event(
        session=session,
        action=AuditAction.USER_REGISTERED,
        workspace_id=workspace.id,
        actor_id=new_user.id,
        payload={
            "user_id": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role),
            "registered_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    await session.commit()
    await session.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
@router.post("/token", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TokenResponse:
    """
    Authenticates user credentials using Argon2id verification and returns signed JWT tokens.
    """
    query = select(User).where(User.email == payload.email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        # Log failed authentication attempt for intrusion detection
        if user:
            await AuditService.record_event(
                session=session,
                action=AuditAction.USER_LOGIN_FAILED,
                workspace_id=user.workspace_id,
                actor_id=user.id,
                payload={"email": payload.email, "reason": "invalid_credentials"},
            )
            await session.commit()
        raise UnauthorizedProblem(detail="Incorrect email or password.")

    if not user.is_active:
        raise UnauthorizedProblem(detail="Account is inactive or revoked.")

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        workspace_id=user.workspace_id,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        workspace_id=user.workspace_id,
    )

    # Log successful login
    await AuditService.record_event(
        session=session,
        action=AuditAction.USER_LOGIN,
        workspace_id=user.workspace_id,
        actor_id=user.id,
        payload={"email": user.email, "role": user.role.value if hasattr(user.role, "value") else str(user.role)},
    )
    await session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TokenResponse:
    """
    Exchanges a valid refresh token for a newly issued access token.
    """
    token_data = decode_jwt_token(payload.refresh_token, expected_type="refresh")
    user_id_str = token_data.get("sub")
    if not user_id_str:
        raise UnauthorizedProblem(detail="Invalid refresh token claims.")

    user = await session.get(User, uuid.UUID(user_id_str))
    if not user or not user.is_active:
        raise UnauthorizedProblem(detail="User session invalid or terminated.")

    new_access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        workspace_id=user.workspace_id,
    )
    new_refresh_token = create_refresh_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        workspace_id=user.workspace_id,
    )

    await AuditService.record_event(
        session=session,
        action=AuditAction.TOKEN_REFRESHED,
        workspace_id=user.workspace_id,
        actor_id=user.id,
        payload={"email": user.email},
    )
    await session.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
async def get_current_actor(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Resolves the authenticated actor identity and associated workspace bounds.
    """
    return current_user


@router.get("/demo-tokens", summary="One-Click Frontend Role Switcher Demo Tokens")
async def get_demo_tokens(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, Any]:
    """
    Returns pre-signed, ready-to-use JWT access tokens and user profile objects
    for all 3 RBAC roles (CREATOR, REVIEWER, ADMINISTRATOR) in a single JSON call.
    Enables instant 1-click role switching in the React frontend during evaluation.
    """
    roles = [UserRole.CREATOR, UserRole.REVIEWER, UserRole.ADMINISTRATOR]
    result: dict[str, Any] = {}

    # Resolve active workspace or create default
    ws_q = select(Workspace).limit(1)
    ws_res = await session.execute(ws_q)
    ws = ws_res.scalars().first()
    if not ws:
        ws = Workspace(name="Acme FinTech Global", slug="acme-fintech")
        session.add(ws)
        await session.flush()

    for role in roles:
        role_str = role.value if hasattr(role, "value") else str(role)
        u_q = (
            select(User)
            .where(User.role == role, User.is_active == True)
            .order_by(User.created_at.asc())
            .limit(1)
        )
        u_res = await session.execute(u_q)
        user = u_res.scalars().first()
        if not user:
            email = f"{role_str.lower()}@brandshield.ai"
            name = f"Demo {role_str.capitalize()}"
            user = User(
                workspace_id=ws.id,
                email=email,
                hashed_password=hash_password("DemoSecure2026!"),
                full_name=name,
                role=role,
                is_active=True,
            )
            session.add(user)
            await session.flush()

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            workspace_id=user.workspace_id,
        )

        role_payload = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "role": role_str,
            "user": UserRead.model_validate(user).model_dump(mode="json"),
        }
        result[role_str.lower()] = role_payload
        result[role_str] = role_payload

    return result

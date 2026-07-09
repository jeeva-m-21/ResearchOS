"""Authentication API routes"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from api.dependencies.auth import (
    blacklist_token,
    get_current_org_with_membership,
    get_current_user,
    jwt_manager,
)
from api.schemas.auth import (
    APIKeyCreateRequest,
    APIKeyResponse,
    LoginRequest,
    LogoutRequest,
    OrganizationMembership,
    RefreshTokenRequest,
    TokenResponse,
    UserProfile,
)
from infrastructure.auth.jwt import TokenData
from infrastructure.auth.password import PasswordManager
from infrastructure.database import db

router = APIRouter()

# API key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def authenticate_api_key(
    api_key: str = Depends(api_key_header)
) -> Optional[TokenData]:
    """Authenticate via API key"""
    if not api_key:
        return None

    # Get API key from database
    api_key_data = await db.fetch_one(
        """
        SELECT
            ak.id,
            ak.organization_id,
            ak.user_id,
            ak.name,
            ak.last_used_at,
            ak.expires_at
        FROM api_keys ak
        WHERE ak.key_hash = crypt($1, ak.key_hash)
        AND ak.deleted_at IS NULL
        """,
        api_key
    )

    if not api_key_data:
        return None

    # Check if API key is expired
    if api_key_data["expires_at"] and api_key_data["expires_at"] < datetime.utcnow():
        return None

    # Update last used timestamp
    await db.execute(
        """
        UPDATE api_keys
        SET last_used_at = NOW()
        WHERE id = $1
        """,
        api_key_data["id"]
    )

    return TokenData(
        user_id=api_key_data["user_id"],
        organization_id=api_key_data["organization_id"]
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    # Get user from database
    user = await db.fetch_one(
        """
        SELECT id, email, password_hash, name
        FROM users
        WHERE email = $1

        """,
        request.email
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not PasswordManager.verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Determine organization context
    organization_id = request.organization_id
    if not organization_id:
        # Get user's first organization
        first_org = await db.fetch_one(
            """
            SELECT organization_id
            FROM organization_members
            WHERE user_id = $1
            LIMIT 1
            """,
            user["id"]
        )
        if first_org:
            organization_id = first_org["organization_id"]

    token_data = TokenData(user_id=user["id"], organization_id=organization_id)

    # Create tokens
    access_token = jwt_manager.create_access_token(token_data)
    refresh_token = jwt_manager.create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=jwt_manager.access_token_expire_minutes * 60
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    # Verify refresh token
    token_data = jwt_manager.verify_token(request.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check token type
    token_type = jwt_manager.get_token_type(request.refresh_token)
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Create new tokens
    access_token = jwt_manager.create_access_token(token_data)
    refresh_token = jwt_manager.create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=jwt_manager.access_token_expire_minutes * 60
    )

@router.post("/logout")
async def logout(request: LogoutRequest):
    """Logout and revoke refresh token"""
    # Add refresh token to blacklist
    blacklist_token(request.refresh_token)

    return {"message": "Logged out successfully"}

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreateRequest,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Create a new API key"""
    # Generate API key
    api_key_value = f"rok_{uuid4().hex}"
    api_key_id = uuid4()

    # Hash API key for storage
    await db.execute(
        """
        INSERT INTO api_keys (
            id,
            organization_id,
            user_id,
            name,
            key_hash,
            expires_at
        ) VALUES ($1, $2, $3, $4, crypt($5, gen_salt('bf')), $6)
        """,
        api_key_id,
        organization_id,
        user.user_id,
        request.name,
        api_key_value,
        request.expires_at
    )

    return APIKeyResponse(
        id=api_key_id,
        name=request.name,
        key=api_key_value,  # Only shown once
        organization_id=organization_id,
        created_at=datetime.utcnow().isoformat(),
        expires_at=request.expires_at,
        last_used_at=None
    )

@router.get("/profile", response_model=UserProfile)
async def get_profile(
    user: TokenData = Depends(get_current_user),
):
    """Get current user profile"""
    user_data = await db.fetch_one(
        """
        SELECT id, email, name, avatar_url, created_at
        FROM users
        WHERE id = $1
        """,
        user.user_id
    )

    if user_data:
        user_data = dict(user_data)
        # Convert datetime to ISO format string
        if user_data.get('created_at'):
            user_data['created_at'] = user_data['created_at'].isoformat()

    return UserProfile(**user_data)

@router.get("/organizations", response_model=list[OrganizationMembership])
async def get_organizations(
    user: TokenData = Depends(get_current_user),
):
    """Get user's organizations"""
    organizations = await db.fetch_all(
        """
        SELECT
            om.organization_id,
            o.name as organization_name,
            o.slug as organization_slug,
            om.role,
            om.joined_at
        FROM organization_members om
        JOIN organizations o ON om.organization_id = o.id
        WHERE om.user_id = $1
        ORDER BY om.joined_at DESC
        """,
        user.user_id
    )

    result = []
    for org in organizations:
        org_dict = dict(org)
        # Convert datetime to ISO format string
        if org_dict.get('joined_at'):
            org_dict['joined_at'] = org_dict['joined_at'].isoformat()
        result.append(OrganizationMembership(**org_dict))

    return result

# Add API key authentication as an alternative to JWT
async def get_authenticated_user(
    token_data: Optional[TokenData] = Depends(get_current_user),
    api_key_data: Optional[TokenData] = Depends(authenticate_api_key),
) -> Optional[TokenData]:
    """Get authenticated user from either JWT or API key"""
    return token_data or api_key_data

# Export dependencies for use in other routes
get_authenticated_user_dep = get_authenticated_user

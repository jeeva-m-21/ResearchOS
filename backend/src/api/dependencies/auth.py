"""FastAPI dependencies for authentication and authorization"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from infrastructure.auth.jwt import JWTManager, TokenData
from infrastructure.database import db

security = HTTPBearer()
jwt_manager = JWTManager()

# In-memory token blacklist for logout (in production, use Redis)
_token_blacklist = set()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current user from JWT token"""
    token = credentials.credentials

    # Check if token is blacklisted
    if token in _token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    token_data = jwt_manager.verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    token_type = jwt_manager.get_token_type(token)
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data

async def get_current_org(
    token_data: TokenData = Depends(get_current_user)
) -> Optional[UUID]:
    """Get current organization from token"""
    return token_data.organization_id

async def get_current_org_with_membership(
    token_data: TokenData = Depends(get_current_user),
) -> Optional[UUID]:
    """Get current organization with membership validation"""
    if not token_data.organization_id:
        return None

    # Verify user belongs to organization
    exists = await db.fetch_val(
        """
        SELECT 1 FROM organization_members
        WHERE organization_id = $1 AND user_id = $2
        """,
        token_data.organization_id,
        token_data.user_id
    )

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization",
        )

    return token_data.organization_id

async def require_role(
    organization_id: UUID = Depends(get_current_org_with_membership),
    token_data: TokenData = Depends(get_current_user),
    required_role: str = "member"
) -> None:
    """Require minimum role for accessing resource"""

    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
        )

    # Get user's role in organization
    user_role = await db.fetch_val(
        """
        SELECT role FROM organization_members
        WHERE organization_id = $1 AND user_id = $2
        """,
        organization_id,
        token_data.user_id
    )

    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBOTEN,
            detail="User is not a member of this organization",
        )

    # Define role hierarchy
    role_hierarchy = {
        "viewer": 0,
        "member": 1,
        "admin": 2,
        "owner": 3
    }

    if role_hierarchy.get(user_role, -1) < role_hierarchy.get(required_role, -1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}, User role: {user_role}",
        )

def blacklist_token(token: str) -> None:
    """Add token to blacklist"""
    _token_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in _token_blacklist

"""Pydantic schemas for authentication"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    organization_id: Optional[UUID] = Field(
        None, description="Organization to log into"
    )


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    """Logout request schema"""
    refresh_token: str = Field(..., description="Refresh token to revoke")


class APIKeyCreateRequest(BaseModel):
    """API key creation request schema"""
    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")


class APIKeyResponse(BaseModel):
    """API key response schema"""
    id: UUID = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    key: str = Field(..., description="API key (only shown once)")
    organization_id: UUID = Field(..., description="Organization ID")
    created_at: str = Field(..., description="Creation timestamp")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    last_used_at: Optional[str] = Field(None, description="Last used timestamp")


class UserProfile(BaseModel):
    """User profile response schema"""
    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: str = Field(..., description="Account creation timestamp")


class OrganizationMembership(BaseModel):
    """Organization membership response schema"""
    organization_id: UUID = Field(..., description="Organization ID")
    organization_name: str = Field(..., description="Organization name")
    organization_slug: str = Field(..., description="Organization slug")
    role: str = Field(..., description="User role in organization")
    joined_at: str = Field(..., description="Membership timestamp")

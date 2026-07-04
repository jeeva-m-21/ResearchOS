"""Authentication middleware for FastAPI"""
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.dependencies.auth import (
    is_token_blacklisted,
)
from src.infrastructure.auth.jwt import JWTManager

jwt_manager = JWTManager()

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware that adds user context to requests"""

    def __init__(self, app, exclude_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/auth/login",
            "/auth/refresh",
            "/auth/register",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Try to authenticate
        try:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")

                # Check if token is blacklisted
                if is_token_blacklisted(token):
                    # Skip setting user context for blacklisted tokens
                    # Actual validation will fail in dependencies
                    pass
                else:
                    # Set user context on request state
                    token_data = jwt_manager.verify_token(token)
                    if token_data:
                        request.state.user = token_data.user_id
                        if token_data.organization_id:
                            request.state.organization = token_data.organization_id

        except Exception:
            # Authentication failed, but let dependencies handle it
            pass

        # Continue with request
        response = await call_next(request)

        return response


class OrganizationMiddleware(BaseHTTPMiddleware):
    """Organization context middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get organization from header or query param
        organization_id = None

        # Check X-Organization-ID header
        org_header = request.headers.get("X-Organization-ID")
        if org_header:
            try:
                organization_id = UUID(org_header)
            except ValueError:
                pass

        # Also check query parameter
        if not organization_id:
            org_query = request.query_params.get("organization_id")
            if org_query:
                try:
                    organization_id = UUID(org_query)
                except ValueError:
                    pass

        # Set organization on request state
        if organization_id:
            request.state.organization = organization_id

        response = await call_next(request)

        return response

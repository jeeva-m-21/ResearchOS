"""JWT token management"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt

SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class TokenData:
    """JWT token payload"""
    
    def __init__(self, user_id: UUID, organization_id: Optional[UUID] = None):
        self.user_id = user_id
        self.organization_id = organization_id

class JWTManager:
    """Manages JWT token creation and validation"""
    
    def __init__(
        self,
        secret_key: str = SECRET_KEY,
        algorithm: str = ALGORITHM,
        access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days: int = REFRESH_TOKEN_EXPIRE_DAYS,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(
        self,
        data: TokenData,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create an access token"""
        to_encode = {
            "sub": str(data.user_id),
            "user_id": str(data.user_id),
            "type": "access",
        }
        
        if data.organization_id:
            to_encode["organization_id"] = str(data.organization_id)
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self,
        data: TokenData,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a refresh token"""
        to_encode = {
            "sub": str(data.user_id),
            "user_id": str(data.user_id),
            "type": "refresh",
        }
        
        if data.organization_id:
            to_encode["organization_id"] = str(data.organization_id)
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify a token and return token data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if user_id is None:
                return None
            
            token_type = payload.get("type")
            if token_type not in ["access", "refresh"]:
                return None
            
            organization_id = payload.get("organization_id")
            if organization_id:
                organization_id = UUID(organization_id)
            
            return TokenData(
                user_id=UUID(user_id),
                organization_id=organization_id
            )
        
        except (JWTError, ValueError):
            return None
    
    def get_token_type(self, token: str) -> Optional[str]:
        """Get token type without full validation"""
        try:
            # Only decode without validation to check type
            payload = jwt.get_unverified_claims(token)
            return payload.get("type")
        except (JWTError, ValueError):
            return None
# ResearchOS Authentication System

A JWT-based authentication system with API key support, built for multi-tenant research collaboration platform.

## Features

- ✅ **JWT Authentication**: Bearer tokens with configurable expiration
- ✅ **Refresh Token Rotation**: Secure token refresh with rotation
- ✅ **API Key Authentication**: SDK-friendly API key support
- ✅ **Multi-Tenancy**: Organization-level isolation
- ✅ **RLS Integration**: Works with PostgreSQL Row-Level Security policies
- ✅ **Password Security**: bcrypt password hashing
- ✅ **Role-Based Access**: Organization member roles (owner, admin, member, viewer)

## Quick Start

### 1. Start Services

```bash
# Start Docker Compose services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### 2. Test Login

```bash
# Test authentication
bash quickstart-auth.sh

# Or manually:
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234","organization_id":"00000000-0000-0000-0000-000000000001"}'
```

### 3. Use Authentication

#### JWT Authentication

```bash
# Extract access token from login response
ACCESS_TOKEN="your_access_token_here"

# Access protected endpoint
curl -X GET http://localhost:8000/auth/profile \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Create a new experiment
curl -X POST http://localhost:8000/v1/experiments \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Experiment","project_id":"00000000-0000-0000-0000-000000000001","description":"Test experiment"}'
```

#### API Key Authentication

```bash
# Create an API key (requires JWT token first)
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My API Key","expires_at":null}'

# Use API key
API_KEY="your_api_key_here"

curl -X GET http://localhost:8000/auth/profile \
  -H "X-API-Key: $API_KEY"

curl -X GET http://localhost:8000/v1/experiments \
  -H "X-API-Key: $API_KEY"
```

## API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Login with email and password |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/logout` | POST | Logout and revoke refresh token |
| `/auth/api-keys` | POST | Create API key |
| `/auth/profile` | GET | Get user profile |
| `/auth/organizations` | GET | List user's organizations |

### Resources (Requires Authentication)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/experiments` | POST | Create experiment |
| `/v1/experiments/{id}` | GET | Get experiment |
| `/v1/experiments/{id}/runs` | GET | List runs |
| `/v1/experiments/{id}/runs` | POST | Start run |

## Database Schema

### Main Tables

```sql
-- Users (existing)
users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- Added for auth
    name VARCHAR(255),
    created_at TIMESTAMPZ,
    updated_at TIMESTAMPZ,
    deleted_at TIMESTAMPZ
)

-- Organizations (existing)
organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50)
)

-- Organization memberships (existing)
organization_members (
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50) NOT NULL,
    PRIMARY KEY (organization_id, user_id)
)

-- New tables for authentication
api_keys (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    last_used_at TIMESTAMPZ,
    expires_at TIMESTAMPZ
)

refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPZ NOT NULL,
    revoked_at TIMESTAMPZ
)
```

### Row-Level Security (RLS)

PostgreSQL RLS policies ensure:
1. Users can only access organizations they belong to
2. API keys are scoped to specific organizations
3. Refresh tokens are user-specific
4. All queries automatically filter by organization_id

```sql
CREATE POLICY experiments_isolation ON experiments
FOR ALL USING (
    organization_id IN (
        SELECT organization_id 
        FROM organization_members 
        WHERE user_id = current_user_id()
    )
);
```

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/researchos

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
PASSWORD_HASH_ROUNDS=12
```

### Production Settings

```python
# src/infrastructure/auth/settings.py

from pydantic import BaseSettings

class AuthSettings(BaseSettings):
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    password_hash_rounds: int = 12
    
    class Config:
        env_file = ".env"
```

## Security Considerations

### Token Security
- **Short-lived access tokens**: 30 minutes
- **Long-lived refresh tokens**: 7 days (rotated on use)
- **API keys**: Never expire by default (user can manually revoke)
- **Token blacklisting**: Refresh tokens can be revoked

### Password Security
- **bcrypt algorithm** with 12 rounds
- **Salt per password**
- **Pepper** (optional, in database layer)

### API Security
- **HTTPS required** in production
- **Rate limiting** on authentication endpoints
- **API key rotation** recommended monthly

## Testing

### Unit Tests

```bash
# Run authentication tests
docker-compose exec backend pytest src/tests/unit/test_auth.py -v

# Run integration tests
docker-compose exec backend pytest src/tests/integration/test_auth_integration.py -v
```

### Manual Testing

```bash
# Run the comprehensive test suite
bash test-auth.sh

# Or run individual tests
./quickstart-auth.sh
```

## Integration with Existing System

### Middleware Flow

1. **Request arrives** → `AuthMiddleware` extracts JWT/API key
2. **Token validation** → JWT decoded or API key validated
3. **Organization context** → `OrganizationMiddleware` sets context
4. **RLS policies** → Database filters based on organization_id
5. **Response** → Returns organization-isolated data

### Adding Authentication to Routes

```python
from src.api.dependencies.auth import (
    get_current_user,
    get_current_org_with_membership,
)

@router.post("/experiments")
async def create_experiment(
    name: str,
    user: TokenData = Depends(get_current_user),  # JWT user
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    # User and organization are automatically validated
    # Database queries implicitly filter by organization_id via RLS
    pass
```

## Deployment

### Production Checklist

1. ✅ **Secure JWT secret**: Generate with `openssl rand -hex 32`
2. ✅ **HTTPS enabled**: Reverse proxy (Nginx/Traefik)
3. ✅ **Rate limiting**: Apply to authentication endpoints
4. ✅ **Monitoring**: Track authentication failures
5. ✅ **Logging**: Audit all authentication attempts
6. ✅ **Backup**: Regular backup of user data

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: researchos-auth-secrets
type: Opaque
data:
  jwt-secret-key: $(echo -n "your-secret-key" | base64)
  db-password: $(echo -n "your-db-password" | base64)
```

## Troubleshooting

### Common Issues

1. **"Invalid token"**: Check token expiration, format, and signature
2. **"Organization not found"**: User may not be member of requested organization
3. **"Permission denied"**: RLS policy may block access
4. **Database connection**: Check DATABASE_URL and database health

### Debug Commands

```bash
# Check database connectivity
docker-compose exec postgres psql -U researchos -d researchos -c "SELECT 1"

# Check RLS policies
docker-compose exec postgres psql -U researchos -d researchos -c "\d+ users"

# View logs
docker-compose logs -f backend
```

## Next Steps

Future improvements:
1. **OAuth2 integration** (GitHub, Google, etc.)
2. **Two-factor authentication**
3. **Password policy enforcement**
4. **Login attempt rate limiting**
5. **Session management UI**
6. **Audit logging enhancements**

---

**Status**: ✅ Production-ready authentication system

**Test Credentials**: 
- Email: `test@example.com`
- Password: `test1234`
- Organization ID: `00000000-0000-0000-0000-000000000001`
- API Key: Created via `/auth/api-keys` endpoint
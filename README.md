# Hub Auth - Centralized Authentication Service

Hub Auth is a centralized authentication service that validates JWT tokens from Microsoft Azure AD (MSAL) for all your backend services. It provides a single source of truth for authentication across your microservices architecture.

## Features

- **JWT Token Validation**: Validates MSAL tokens from Azure AD using public key verification
- **User Synchronization**: Automatically syncs Azure AD users to local database
- **Service Client Management**: API key-based authentication for backend services
- **Comprehensive Logging**: Tracks all validation requests with detailed metrics
- **REST API**: Simple HTTP API for token validation
- **Reusable Client Library**: Easy integration with other Django projects
- **Django Admin**: Full admin interface for managing users, service clients, and logs

## Architecture

```
React/Postman (MSAL Token) 
    ↓
Backend Service (employee_manage, etc.)
    ↓
Hub Auth Service (validates token)
    ↓
Azure AD (verifies signature with public keys)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Azure AD

1. Register an application in Azure AD
2. Note the **Tenant ID**, **Client ID**, and **Client Secret**
3. Configure API permissions (optional, only needed if calling Graph API)

### 3. Update Settings

Edit `hub_auth/settings.py`:

```python
# Azure AD Configuration
AZURE_AD_TENANT_ID = 'your-tenant-id'
AZURE_AD_CLIENT_ID = 'your-client-id'  
AZURE_AD_CLIENT_SECRET = 'your-client-secret'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hub_auth_db',
        'USER': 'your-db-user',
        'PASSWORD': 'your-db-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Create Service Client

```python
python manage.py shell

from authentication.models import ServiceClient
import secrets

client = ServiceClient.objects.create(
    name='employee_manage',
    description='Employee management service',
    api_key=secrets.token_urlsafe(32),
    is_active=True
)
print(f"API Key: {client.api_key}")
```

Save the API key - you'll need it for other services.

### 7. Start Server

```bash
python manage.py runserver 8000
```

## API Endpoints

### POST /api/auth/validate/

Validate a JWT token (main endpoint).

**Headers:**
```
X-API-Key: <your-service-api-key>
Content-Type: application/json
```

**Request Body:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJub25jZSI6...",
  "service_name": "employee_manage"
}
```

**Response (200 OK):**
```json
{
  "is_valid": true,
  "user": {
    "id": 1,
    "username": "jsmith@company.com",
    "email": "jsmith@company.com",
    "display_name": "John Smith",
    "azure_ad_object_id": "abc123...",
    "is_active": true,
    "is_staff": false
  },
  "token_claims": {
    "oid": "abc123...",
    "upn": "jsmith@company.com",
    "name": "John Smith",
    ...
  },
  "validation_id": "uuid"
}
```

**Response (401 Unauthorized):**
```json
{
  "is_valid": false,
  "error_message": "Token has expired",
  "user": null,
  "token_claims": null
}
```

### GET /api/auth/validate-simple/

Simple token validation using Authorization header.

**Headers:**
```
Authorization: Bearer <token>
X-API-Key: <your-service-api-key>
```

**Response:**
```json
{
  "is_valid": true,
  "user": {
    "id": 1,
    "username": "jsmith@company.com",
    "email": "jsmith@company.com",
    "display_name": "John Smith",
    "is_active": true
  }
}
```

## Integration with Other Services

### Option 1: Using the Client Library

Copy `authentication/client.py` to your project and use:

```python
# In your Django settings.py
HUB_AUTH_URL = 'http://localhost:8000'
HUB_AUTH_API_KEY = 'your-api-key-from-hub-auth'
HUB_AUTH_SERVICE_NAME = 'employee_manage'

# In your views or middleware
from hub_auth_client import HubAuthClient

client = HubAuthClient(
    hub_auth_url=settings.HUB_AUTH_URL,
    api_key=settings.HUB_AUTH_API_KEY,
    service_name=settings.HUB_AUTH_SERVICE_NAME
)

# Extract token from request
token = request.headers.get('Authorization', '').replace('Bearer ', '')

# Validate
is_valid, user_data, error = client.validate_token(token)

if is_valid:
    # Token is valid, user_data contains user information
    print(f"Authenticated user: {user_data['display_name']}")
else:
    # Token is invalid
    return JsonResponse({'error': error}, status=401)
```

### Option 2: Using Django Authentication Backend

```python
# In your Django settings.py
INSTALLED_APPS = [
    ...
]

AUTHENTICATION_BACKENDS = [
    'path.to.DjangoHubAuthBackend',  # Copy from authentication/client.py
    'django.contrib.auth.backends.ModelBackend',
]

HUB_AUTH_URL = 'http://localhost:8000'
HUB_AUTH_API_KEY = 'your-api-key'
HUB_AUTH_SERVICE_NAME = 'employee_manage'

# In your views
from django.contrib.auth import authenticate

def my_view(request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = authenticate(request=request, token=token)
    
    if user:
        # User authenticated successfully
        request.user = user
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
```

### Option 3: REST Framework Authentication Class

```python
# authentication.py in your service
from rest_framework import authentication, exceptions
from hub_auth_client import HubAuthClient
from django.conf import settings

class HubAuthAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]
        
        client = HubAuthClient(
            hub_auth_url=settings.HUB_AUTH_URL,
            api_key=settings.HUB_AUTH_API_KEY,
            service_name=settings.HUB_AUTH_SERVICE_NAME
        )
        
        is_valid, user_data, error = client.validate_token(token)
        
        if not is_valid:
            raise exceptions.AuthenticationFailed(error)
        
        # Get or create local user based on user_data
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data.get('email', ''),
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
            }
        )
        
        return (user, None)

# In your views.py
from rest_framework.views import APIView
from rest_framework.response import Response

class MyProtectedView(APIView):
    authentication_classes = [HubAuthAuthentication]
    
    def get(self, request):
        return Response({
            'message': f'Hello {request.user.username}'
        })
```

## React Integration with MSAL.js

### 1. Install MSAL

```bash
npm install @azure/msal-browser @azure/msal-react
```

### 2. Configure MSAL

```javascript
// authConfig.js
export const msalConfig = {
  auth: {
    clientId: "your-azure-ad-client-id",
    authority: "https://login.microsoftonline.com/your-tenant-id",
    redirectUri: "http://localhost:3000",
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  }
};

export const loginRequest = {
  scopes: ["User.Read"]
};
```

### 3. Use MSAL in React

```javascript
// index.js
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { msalConfig } from "./authConfig";

const msalInstance = new PublicClientApplication(msalConfig);

ReactDOM.render(
  <MsalProvider instance={msalInstance}>
    <App />
  </MsalProvider>,
  document.getElementById("root")
);
```

### 4. Make Authenticated API Calls

```javascript
// api.js
import { useMsal } from "@azure/msal-react";

export function useApi() {
  const { instance, accounts } = useMsal();
  
  const callApi = async (endpoint, options = {}) => {
    // Get access token
    const request = {
      scopes: ["User.Read"],
      account: accounts[0]
    };
    
    const response = await instance.acquireTokenSilent(request);
    const token = response.accessToken;
    
    // Call your backend with token
    const result = await fetch(`http://localhost:8001/api/${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return result.json();
  };
  
  return { callApi };
}
```

## Postman Integration

### 1. Get Azure AD Token

**Request:**
```
POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={client-id}
&client_secret={client-secret}
&scope=https://graph.microsoft.com/.default
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJub25jZSI6...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 2. Call Your API

**Request:**
```
GET http://localhost:8001/api/employees/
Authorization: Bearer {access_token}
```

Your backend will validate the token with hub_auth automatically.

## Admin Interface

Access at `http://localhost:8000/admin/`

### Users
- View all synced Azure AD users
- See last token validation time
- Manage user permissions

### Service Clients
- Create/manage API keys for services
- View validation statistics and success rates
- Enable/disable service access

### Token Validation Logs
- View all validation attempts
- Filter by service, user, validity
- Monitor performance and errors

## Token Validation Flow

1. **React/Postman** → Gets token from Azure AD using MSAL
2. **Backend Service** → Receives request with `Authorization: Bearer {token}`
3. **Backend** → Sends token to Hub Auth: `POST /api/auth/validate/`
4. **Hub Auth** → Validates token:
   - Decodes JWT header to get `kid` (key ID)
   - Fetches Azure AD public keys from JWKS endpoint
   - Verifies signature using public key
   - Validates expiration, audience, issuer
   - Syncs user to database
5. **Hub Auth** → Returns validation result + user data
6. **Backend** → Proceeds with request or returns 401

## Security Best Practices

- **API Keys**: Rotate service API keys regularly
- **HTTPS**: Use HTTPS in production for all endpoints
- **Token Expiry**: Azure AD tokens typically expire in 1 hour
- **Database**: Use strong PostgreSQL password
- **Secrets**: Store Azure AD credentials in environment variables
- **CORS**: Limit `CORS_ALLOWED_ORIGINS` to your actual domains
- **Rate Limiting**: Consider adding rate limiting in production

## Troubleshooting

### "Invalid signature" error
- Verify `AZURE_AD_TENANT_ID` and `AZURE_AD_CLIENT_ID` match your Azure AD app
- Ensure token audience (`aud` claim) matches your client ID

### "Token from wrong tenant" error
- Check that token's `tid` claim matches `AZURE_AD_TENANT_ID`

### "Hub auth service unavailable" error
- Verify hub_auth is running on the configured port
- Check network connectivity between services
- Verify `HUB_AUTH_URL` is correct

### User not syncing
- Check that token contains required claims: `oid`, `tid`, `upn`
- Review hub_auth logs for errors

## Production Deployment

### Environment Variables

```bash
# .env file
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
ALLOWED_HOSTS=hub-auth.yourcompany.com

DATABASE_URL=postgresql://user:pass@localhost/hub_auth_db

AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "hub_auth.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Nginx Configuration

```nginx
upstream hub_auth {
    server localhost:8000;
}

server {
    listen 80;
    server_name hub-auth.yourcompany.com;

    location / {
        proxy_pass http://hub_auth;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## License

MIT

## Support

For issues or questions, contact your development team.

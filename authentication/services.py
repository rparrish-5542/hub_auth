# hub_auth/authentication/services.py
"""JWT Token validation service for MSAL tokens."""
import logging
import time
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import jwt
from jwt import PyJWKClient
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MSALTokenValidator:
    """Validates JWT tokens issued by Azure AD / Microsoft Identity Platform."""
    
    def __init__(self):
        self.tenant_id = settings.AZURE_AD_TENANT_ID
        self.client_id = settings.AZURE_AD_CLIENT_ID
        self.issuer = f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
        self.jwks_uri = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        
        # Initialize JWK client for fetching public keys
        self.jwks_client = PyJWKClient(self.jwks_uri, cache_keys=True, max_cached_keys=16)
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate a JWT token from MSAL.
        
        Args:
            token: The JWT token string (without 'Bearer ' prefix)
        
        Returns:
            Tuple of (is_valid, decoded_token, error_message)
        """
        start_time = time.time()
        
        try:
            # First, decode without verification to get the kid (key ID)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                return False, None, "Token missing 'kid' in header"
            
            # Get the signing key from Azure AD's JWKS endpoint
            signing_key = self.jwks_client.get_signing_key(kid)
            
            # Decode and validate the token
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            
            # Additional validation checks
            validation_result, error_msg = self._additional_validation(decoded_token)
            
            if not validation_result:
                return False, decoded_token, error_msg
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Token validated successfully in {elapsed_ms}ms for user: {decoded_token.get('upn') or decoded_token.get('unique_name')}")
            
            return True, decoded_token, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidAudienceError:
            return False, None, "Invalid audience"
        except jwt.InvalidIssuerError:
            return False, None, "Invalid issuer"
        except jwt.InvalidSignatureError:
            return False, None, "Invalid signature"
        except jwt.DecodeError as e:
            return False, None, f"Token decode error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}", exc_info=True)
            return False, None, f"Validation error: {str(e)}"
    
    def _additional_validation(self, decoded_token: Dict) -> Tuple[bool, Optional[str]]:
        """
        Perform additional validation beyond JWT standard claims.
        
        Args:
            decoded_token: The decoded JWT payload
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check token version
        if decoded_token.get('ver') != '2.0':
            return False, "Unsupported token version"
        
        # Ensure token has required claims
        required_claims = ['oid', 'tid']  # Object ID and Tenant ID
        for claim in required_claims:
            if claim not in decoded_token:
                return False, f"Missing required claim: {claim}"
        
        # Verify tenant ID matches expected
        if decoded_token.get('tid') != self.tenant_id:
            return False, "Token from wrong tenant"
        
        # Check if token is for the correct application
        # Token can have 'aud' as client_id or 'azp' (authorized party)
        aud = decoded_token.get('aud')
        azp = decoded_token.get('azp')
        
        if aud != self.client_id and azp != self.client_id:
            # For delegated permissions, appid might be present
            appid = decoded_token.get('appid')
            if appid != self.client_id:
                logger.warning(f"Token audience mismatch. Expected: {self.client_id}, Got aud: {aud}, azp: {azp}, appid: {appid}")
        
        return True, None
    
    def extract_user_info(self, decoded_token: Dict) -> Dict:
        """
        Extract user information from decoded token.
        
        Args:
            decoded_token: The decoded JWT payload
        
        Returns:
            Dictionary with user information
        """
        return {
            'azure_ad_object_id': decoded_token.get('oid'),
            'azure_ad_tenant_id': decoded_token.get('tid'),
            'user_principal_name': decoded_token.get('upn') or decoded_token.get('unique_name'),
            'email': decoded_token.get('email') or decoded_token.get('preferred_username'),
            'display_name': decoded_token.get('name'),
            'given_name': decoded_token.get('given_name'),
            'family_name': decoded_token.get('family_name'),
            'job_title': decoded_token.get('jobTitle'),
            'department': decoded_token.get('department'),
            'employee_id': decoded_token.get('employeeId'),
            'roles': decoded_token.get('roles', []),
            'groups': decoded_token.get('groups', []),
        }
    
    def get_token_expiry(self, decoded_token: Dict) -> Optional[datetime]:
        """Get token expiration datetime."""
        exp = decoded_token.get('exp')
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None


class UserSyncService:
    """Service to sync Azure AD users to local database."""
    
    def __init__(self):
        self.validator = MSALTokenValidator()
    
    def sync_user_from_token(self, decoded_token: Dict) -> 'User':
        """
        Sync user from token claims to local database.
        
        Args:
            decoded_token: Decoded JWT token payload
        
        Returns:
            User model instance
        """
        from .models import User
        
        user_info = self.validator.extract_user_info(decoded_token)
        azure_ad_object_id = user_info['azure_ad_object_id']
        
        if not azure_ad_object_id:
            raise ValueError("Token missing required 'oid' claim")
        
        # Get or create user
        user, created = User.objects.get_or_create(
            azure_ad_object_id=azure_ad_object_id,
            defaults={
                'username': user_info.get('user_principal_name') or azure_ad_object_id,
                'email': user_info.get('email', ''),
                'user_principal_name': user_info.get('user_principal_name'),
                'azure_ad_tenant_id': user_info.get('azure_ad_tenant_id'),
                'display_name': user_info.get('display_name'),
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'job_title': user_info.get('job_title'),
                'department': user_info.get('department'),
                'employee_id': user_info.get('employee_id'),
                'is_active': True,
            }
        )
        
        # Update existing user if not newly created
        if not created:
            update_fields = []
            
            # Update fields that might have changed
            if user_info.get('email') and user.email != user_info['email']:
                user.email = user_info['email']
                update_fields.append('email')
            
            if user_info.get('display_name') and user.display_name != user_info['display_name']:
                user.display_name = user_info['display_name']
                update_fields.append('display_name')
            
            if user_info.get('job_title') and user.job_title != user_info['job_title']:
                user.job_title = user_info['job_title']
                update_fields.append('job_title')
            
            if user_info.get('department') and user.department != user_info['department']:
                user.department = user_info['department']
                update_fields.append('department')
            
            # Always update last validation time
            user.last_token_validation = timezone.now()
            update_fields.append('last_token_validation')
            update_fields.append('updated_at')
            
            if update_fields:
                user.save(update_fields=update_fields)
        
        logger.info(f"{'Created' if created else 'Updated'} user: {user.username} (OID: {azure_ad_object_id})")
        
        return user

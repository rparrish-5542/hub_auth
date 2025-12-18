# hub_auth_client/validators/msal.py
"""
Validator for MSAL JWT tokens.
"""
import time
import jwt
import logging
from typing import Dict, Any, Optional, List, Tuple
from jwt import PyJWKClient

from hub_auth_client.validators.base import BaseTokenValidator
from hub_auth_client.utils.jwt_helpers import strip_bearer, decode_unverified, get_kid

logger = logging.getLogger(__name__)


class MSALTokenValidator(BaseTokenValidator):
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        validate_audience: bool = True,
        validate_issuer: bool = True,
        leeway: int = 0,
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.validate_audience = validate_audience
        self.validate_issuer = validate_issuer
        self.leeway = leeway

        self.issuer_v1 = f"https://sts.windows.net/{tenant_id}/"
        self.issuer_v2 = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        self.jwks_uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"

        self.jwks_client = PyJWKClient(self.jwks_uri)

    def validate_token(
        self,
        token: str,
        required_scopes: Optional[List[str]] = None,
        required_roles: Optional[List[str]] = None,
        require_all_scopes: bool = False,
        require_all_roles: bool = False,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        start = time.time()
        token = strip_bearer(token)

        try:
            unverified = decode_unverified(token)
            signing_key = self.jwks_client.get_signing_key(get_kid(token))

            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={
                    "verify_aud": False,
                    "verify_iss": False,
                },
                leeway=self.leeway,
            )

            if self.validate_audience:
                aud = decoded.get("aud")
                if aud not in {self.client_id, f"api://{self.client_id}"}:
                    return False, decoded, f"Invalid audience: {aud}"

            if self.validate_issuer:
                iss = decoded.get("iss")
                if iss not in {self.issuer_v1, self.issuer_v2}:
                    return False, decoded, f"Invalid issuer: {iss}"

            if decoded.get("tid") != self.tenant_id:
                return False, decoded, "Token from wrong tenant"

            error = self._validate_claims(
                decoded,
                required_scopes,
                required_roles,
                require_all_scopes,
                require_all_roles,
            )
            if error:
                return False, decoded, error

            self._log_success(decoded, start)
            return True, decoded, None

        except Exception as exc:
            logger.exception("MSAL token validation failed")
            return False, None, str(exc)

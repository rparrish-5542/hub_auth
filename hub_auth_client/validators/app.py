# hub_auth_client/validators/app.py
"""
Validator for application tokens using a shared secret.
"""
import jwt
from typing import Dict, Any, Optional, List, Tuple

from hub_auth_client.validators.base import BaseTokenValidator
from hub_auth_client.utils.jwt_helpers import strip_bearer


class AppTokenValidator(BaseTokenValidator):
    """Validator for application tokens using a shared secret."""
    def __init__(
        self,
        secret: str,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        algorithms=None,
        leeway: int = 0,
        require_exp: bool = True,
    ):
        self.secret = secret
        self.issuer = issuer
        self.audience = audience
        self.algorithms = algorithms or ["HS256"]
        self.leeway = leeway
        self.require_exp = require_exp

    def validate_token(
        self,
        token: str,
        required_scopes=None,
        required_roles=None,
        require_all_scopes=False,
        require_all_roles=False,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        token = strip_bearer(token)

        try:
            decoded = jwt.decode(
                token,
                self.secret,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_exp": self.require_exp,
                    "verify_aud": bool(self.audience),
                    "verify_iss": bool(self.issuer),
                },
                leeway=self.leeway,
            )

            error = self._validate_claims(
                decoded,
                required_scopes,
                required_roles,
                require_all_scopes,
                require_all_roles,
            )
            if error:
                return False, decoded, error

            return True, decoded, None

        except Exception as exc:
            return False, None, str(exc)

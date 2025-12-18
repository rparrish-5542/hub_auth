import time
import logging
from typing import Dict, Any, Optional, List, Tuple

from hub_auth_client.utils.jwt_helpers import strip_bearer
from hub_auth_client.utils.claims import validate_scopes, validate_roles

logger = logging.getLogger(__name__)


class BaseTokenValidator:
    def _validate_claims(
        self,
        decoded_token: Dict[str, Any],
        required_scopes: Optional[List[str]],
        required_roles: Optional[List[str]],
        require_all_scopes: bool,
        require_all_roles: bool,
    ) -> Optional[str]:
        if required_scopes:
            error = validate_scopes(decoded_token, required_scopes, require_all_scopes)
            if error:
                return error

        if required_roles:
            error = validate_roles(decoded_token, required_roles, require_all_roles)
            if error:
                return error

        return None

    def _log_success(self, decoded_token: Dict[str, Any], start_time: float) -> None:
        elapsed_ms = int((time.time() - start_time) * 1000)
        user = (
            decoded_token.get("upn")
            or decoded_token.get("unique_name")
            or decoded_token.get("oid")
            or decoded_token.get("sub")
        )
        logger.info("Token validated in %sms for user %s", elapsed_ms, user)

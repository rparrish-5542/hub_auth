import logging
import time
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

logger = logging.getLogger(__name__)

_app_token_cache = {"token": None, "expires_at": 0}


class MicrosoftGraphService:
    """
    Handles all Microsoft Graph API interactions.
    """

    GRAPH_PROFILE_MAPPING = {
        "department": "department",
        "job_title": "jobTitle",
        "given_name": "givenName",
        "office_location": "officeLocation",
        "full_name": "displayName",
        "employee_id": "employeeId",
        "email": "mail",
        # manager fetched separately
    }

    def get_app_token(self):
        """Get app-only token from Azure AD, cached until expiry."""
        now = int(time.time())
        if _app_token_cache["token"] and _app_token_cache["expires_at"] > now + 30:
            return _app_token_cache["token"]

        token_url = f"https://login.microsoftonline.com/{settings.TENANT_ID}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }

        try:
            resp = requests.post(
                token_url,
                data=data,
                auth=HTTPBasicAuth(settings.CLIENT_ID, settings.CLIENT_SECRET),
                timeout=5,
            )
            resp.raise_for_status()
            token_data = resp.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            _app_token_cache.update({
                "token": access_token,
                "expires_at": now + int(expires_in),
            })
            return access_token
        except requests.RequestException as e:
            logger.error("Failed to obtain app token: %s", e)
            return None

    def fetch_user_data(self, azure_oid: str) -> dict:
        access_token = self.get_app_token()
        if not access_token:
            logger.warning("No app token available, cannot fetch Graph data.")
            return {}

        headers = {"Authorization": f"Bearer {access_token}"}
        fields = ",".join(self.GRAPH_PROFILE_MAPPING.values())
        url = f"https://graph.microsoft.com/v1.0/users/{azure_oid}?$select={fields}"

        try:
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error("Graph API request failed for OID %s: %s", azure_oid, e)
            return {}

    def fetch_manager_name(self, azure_oid: str) -> str:
        access_token = self.get_app_token()
        if not access_token:
            return ""

        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"https://graph.microsoft.com/v1.0/users/{azure_oid}/manager"

        try:
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            return resp.json().get("displayName", "")
        except requests.RequestException as e:
            logger.warning("Failed to fetch manager for OID %s: %s", azure_oid, e)
            return ""

    def combine_graph_data(self, azure_oid: str) -> dict:
        user_data = self.fetch_user_data(azure_oid)
        manager_name = self.fetch_manager_name(azure_oid)

        mapped_data = {
            local: user_data.get(graph_key, "")
            for local, graph_key in self.GRAPH_PROFILE_MAPPING.items()
        }
        mapped_data["manager_name"] = manager_name
        return mapped_data

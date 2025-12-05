#hub/hub_auth/services/sync_service.py

"""Services for syncing User and UserProfile data with Microsoft Graph."""

from django.contrib.auth import get_user_model
from django.db import transaction
from hub.employee.models import UserProfile
from .graph_service import MicrosoftGraphService

User = get_user_model()


class SyncableModel:
    """Base class for models that can be synced with external data."""
    model = None
    DEFAULT_FIELDS = {}

    @classmethod
    def sync(cls, lookup: dict, defaults: dict):
        instance, created = cls.model.objects.get_or_create(**lookup)
        updated = False
        combined_data = {**cls.DEFAULT_FIELDS, **defaults}

        for field, value in combined_data.items():
            if hasattr(instance, field) and getattr(instance, field, None) != value:
                setattr(instance, field, value)
                updated = True

        if updated:
            instance.save()
        return instance


class SyncableUser(SyncableModel):
    model = User
    DEFAULT_FIELDS = {
        "username": "",
        "email": "",
        "first_name": "",
        "last_name": "",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    }


class SyncableUserProfile(SyncableModel):
    model = UserProfile
    DEFAULT_FIELDS = {
        "phone_number": "",
        "internal_extension": "",
        "is_admin_approved": False,
        "theme_preference": "light",
        "full_name": "",
        "department": None,
        "job_title": "",
        "given_name": "",
        "office_location": "",
        "employee_id": "",
        "email": "",
    }

    @classmethod
    @transaction.atomic
    def sync_from_graph(cls, graph_data: dict):
        mapping = MicrosoftGraphService.GRAPH_PROFILE_MAPPING

        email = graph_data.get(mapping.get("email")) or graph_data.get("userPrincipalName")
        if not email:
            raise ValueError(f"No email found in Graph data: {graph_data}")

        user_defaults = {
            "username": email.split("@")[0],
            "email": email,
            "first_name": graph_data.get("givenName", ""),
            "last_name": graph_data.get("surname", ""),
        }
        user = SyncableUser.sync({"email": email}, user_defaults)

        profile_defaults = {
            local: graph_data.get(remote)
            for local, remote in mapping.items()
        }
        profile_defaults["email"] = email
        profile = cls.sync({"user": user}, profile_defaults)
        return user, profile


class UserProfileService:
    """Orchestrates syncing User and UserProfile based on Graph data."""

    def __init__(self, graph_service: MicrosoftGraphService):
        self.graph_service = graph_service

    @transaction.atomic
    def sync_user_profile(self, azure_oid: str, email: str = None) -> User:
        graph_data = self.graph_service.combine_graph_data(azure_oid)
        email = graph_data.get("email") or email
        if not email:
            raise ValueError("No email found to sync user profile.")

        user_defaults = {
            "username": email,
            "email": email,
            "first_name": graph_data.get("given_name", ""),
            "last_name": graph_data.get("surname", ""),
            "is_active": True,
        }
        user = SyncableUser.sync({"email": email}, user_defaults)

        profile_defaults = {
            **graph_data,
            "user": user,
            "full_name": graph_data.get("full_name"),
            "department": graph_data.get("department"),
        }
        SyncableUserProfile.sync({"user": user}, profile_defaults)

        return user

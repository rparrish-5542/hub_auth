# hub_auth/authentication/serializers.py
"""Serializers for authentication API."""
from rest_framework import serializers
from .models import User, TokenValidation, ServiceClient


class TokenValidationRequestSerializer(serializers.Serializer):
    """Serializer for token validation requests."""
    
    token = serializers.CharField(
        required=True,
        help_text="JWT token from MSAL (without 'Bearer ' prefix)"
    )
    service_name = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Name of the service requesting validation"
    )


class UserInfoSerializer(serializers.ModelSerializer):
    """Serializer for user information."""
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'azure_ad_object_id',
            'user_principal_name',
            'display_name',
            'first_name',
            'last_name',
            'job_title',
            'department',
            'office_location',
            'employee_id',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_token_validation',
        ]
        read_only_fields = fields


class TokenValidationResponseSerializer(serializers.Serializer):
    """Serializer for token validation responses."""
    
    is_valid = serializers.BooleanField()
    error_message = serializers.CharField(required=False, allow_null=True)
    user = UserInfoSerializer(required=False, allow_null=True)
    token_claims = serializers.DictField(required=False, allow_null=True)
    validation_id = serializers.UUIDField(required=False)


class ServiceClientSerializer(serializers.ModelSerializer):
    """Serializer for service clients."""
    
    class Meta:
        model = ServiceClient
        fields = [
            'id',
            'name',
            'description',
            'is_active',
            'allowed_origins',
            'total_validations',
            'successful_validations',
            'failed_validations',
            'last_used',
            'created_at',
        ]
        read_only_fields = ['id', 'total_validations', 'successful_validations', 'failed_validations', 'last_used', 'created_at']


class TokenValidationLogSerializer(serializers.ModelSerializer):
    """Serializer for token validation logs."""
    
    user_display = serializers.CharField(source='user.display_name', read_only=True, allow_null=True)
    
    class Meta:
        model = TokenValidation
        fields = [
            'id',
            'user',
            'user_display',
            'service_name',
            'ip_address',
            'token_oid',
            'token_upn',
            'is_valid',
            'validation_timestamp',
            'error_message',
            'validation_time_ms',
        ]
        read_only_fields = fields

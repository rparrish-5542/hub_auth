# hub_auth/authentication/models.py
"""Models for authentication service."""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Extended user model for Azure AD integration."""
    
    # Azure AD fields
    azure_ad_object_id = models.CharField(
        max_length=255, 
        unique=True, 
        null=True, 
        blank=True,
        db_index=True,
        help_text="Azure AD Object ID (oid claim)"
    )
    azure_ad_tenant_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Azure AD Tenant ID"
    )
    user_principal_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        db_index=True,
        help_text="User Principal Name from Azure AD"
    )
    
    # Profile fields
    display_name = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    office_location = models.CharField(max_length=255, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    
    # Timestamps
    last_token_validation = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=['azure_ad_object_id', 'is_active']),
            models.Index(fields=['employee_id']),
        ]
    
    def __str__(self):
        return self.display_name or self.username or self.email


class TokenValidation(models.Model):
    """Log of token validation requests."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='token_validations')
    
    # Request details
    service_name = models.CharField(max_length=100, help_text="Name of service requesting validation")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Token details
    token_oid = models.CharField(max_length=255, blank=True, null=True, help_text="Object ID from token")
    token_upn = models.CharField(max_length=255, blank=True, null=True, help_text="UPN from token")
    token_app_id = models.CharField(max_length=255, blank=True, null=True, help_text="Application ID from token")
    
    # Validation result
    is_valid = models.BooleanField(default=False)
    validation_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Performance
    validation_time_ms = models.IntegerField(null=True, blank=True, help_text="Time taken to validate in milliseconds")
    
    class Meta:
        verbose_name = "Token Validation"
        verbose_name_plural = "Token Validations"
        ordering = ['-validation_timestamp']
        indexes = [
            models.Index(fields=['service_name', 'validation_timestamp']),
            models.Index(fields=['is_valid', 'validation_timestamp']),
        ]
    
    def __str__(self):
        status = "Valid" if self.is_valid else "Invalid"
        return f"{status} - {self.service_name} - {self.validation_timestamp}"


class ServiceClient(models.Model):
    """Registered services that can use hub_auth for validation."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # API Key for service-to-service authentication
    api_key = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    allowed_origins = models.TextField(
        help_text="Comma-separated list of allowed origins/domains",
        blank=True,
        null=True
    )
    
    # Stats
    total_validations = models.IntegerField(default=0)
    successful_validations = models.IntegerField(default=0)
    failed_validations = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Service Client"
        verbose_name_plural = "Service Clients"
        ordering = ['name']
    
    def __str__(self):
        return self.name


"""
Configuration models for storing Azure AD credentials in database.

This allows managing MSAL configuration through Django admin instead of environment variables.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class AzureADConfiguration(models.Model):
    """
    Store Azure AD configuration in database.
    
    Allows managing MSAL credentials through Django admin instead of environment variables.
    Only one active configuration should exist at a time.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Configuration name (e.g., 'Production', 'Development')"
    )
    
    tenant_id = models.CharField(
        max_length=100,
        help_text="Azure AD Tenant ID (GUID)",
        validators=[
            RegexValidator(
                regex=r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
                message='Must be a valid GUID format',
                flags=0
            )
        ]
    )
    
    client_id = models.CharField(
        max_length=100,
        help_text="Azure AD Application (Client) ID (GUID)",
        validators=[
            RegexValidator(
                regex=r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
                message='Must be a valid GUID format',
                flags=0
            )
        ]
    )
    
    client_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Azure AD Client Secret (optional, for service-to-service auth)"
    )
    
    # Token validation settings
    allowed_audiences = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed audience values (default: [client_id])"
    )
    
    token_version = models.CharField(
        max_length=10,
        choices=[
            ('1.0', 'v1.0'),
            ('2.0', 'v2.0'),
        ],
        default='2.0',
        help_text="Azure AD token version"
    )
    
    # Validation settings
    validate_audience = models.BooleanField(
        default=True,
        help_text="Whether to validate the token audience (aud claim)"
    )
    
    validate_issuer = models.BooleanField(
        default=True,
        help_text="Whether to validate the token issuer (iss claim)"
    )
    
    token_leeway = models.IntegerField(
        default=0,
        help_text="Number of seconds of leeway for token expiration validation"
    )
    
    # Exempt paths (URLs that don't require authentication)
    exempt_paths = models.JSONField(
        default=list,
        blank=True,
        help_text="URL patterns to exempt from authentication (e.g., ['/admin/', '/health/'])"
    )
    
    # Status
    is_active = models.BooleanField(
        default=False,
        help_text="Whether this configuration is active (only one should be active)"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Description of this configuration"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Azure AD Configuration"
        verbose_name_plural = "Azure AD Configurations"
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        status = "✓ Active" if self.is_active else "Inactive"
        return f"{self.name} ({status})"
    
    def clean(self):
        """Ensure only one configuration is active at a time."""
        if self.is_active:
            # Check if another active config exists
            active_configs = AzureADConfiguration.objects.filter(is_active=True)
            if self.pk:
                active_configs = active_configs.exclude(pk=self.pk)
            
            if active_configs.exists():
                raise ValidationError(
                    f"Configuration '{active_configs.first().name}' is already active. "
                    f"Only one configuration can be active at a time."
                )
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_allowed_audiences(self):
        """Get allowed audiences, defaulting to client_id if not set."""
        if self.allowed_audiences:
            return self.allowed_audiences
        return [self.client_id]
    
    def get_exempt_paths(self):
        """Get exempt paths as a list."""
        if self.exempt_paths:
            return self.exempt_paths
        return []
    
    def get_validator_config(self):
        """
        Get configuration dict for MSALTokenValidator.
        
        Returns:
            dict: Configuration for MSALTokenValidator
        """
        return {
            'tenant_id': self.tenant_id,
            'client_id': self.client_id,
            'allowed_audiences': self.get_allowed_audiences(),
            'token_version': self.token_version,
            'validate_audience': self.validate_audience,
            'validate_issuer': self.validate_issuer,
            'token_leeway': self.token_leeway,
        }
    
    @classmethod
    def get_active_config(cls):
        """
        Get the active Azure AD configuration.
        
        Returns:
            AzureADConfiguration or None
        """
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            # Shouldn't happen due to validation, but handle it
            return cls.objects.filter(is_active=True).first()
    
    @classmethod
    def get_validator(cls):
        """
        Get a configured MSALTokenValidator instance using active config.
        
        Returns:
            MSALTokenValidator or None if no active config
        """
        config = cls.get_active_config()
        if not config:
            return None
        
        from hub_auth_client import MSALTokenValidator
        
        return MSALTokenValidator(**config.get_validator_config())


class AzureADConfigurationHistory(models.Model):
    """
    Audit log for Azure AD configuration changes.
    
    Tracks when configurations are created, modified, activated, or deactivated.
    """
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('activated', 'Activated'),
        ('deactivated', 'Deactivated'),
        ('deleted', 'Deleted'),
    ]
    
    configuration = models.ForeignKey(
        AzureADConfiguration,
        on_delete=models.CASCADE,
        related_name='history',
        null=True,
        blank=True
    )
    
    configuration_name = models.CharField(
        max_length=100,
        help_text="Name of the configuration (stored for deleted configs)"
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )
    
    tenant_id = models.CharField(max_length=100)
    client_id = models.CharField(max_length=100)
    
    changed_by = models.CharField(
        max_length=100,
        blank=True,
        help_text="User who made the change"
    )
    
    changed_at = models.DateTimeField(auto_now_add=True)
    
    details = models.TextField(
        blank=True,
        help_text="Additional details about the change"
    )
    
    class Meta:
        verbose_name = "Configuration History"
        verbose_name_plural = "Configuration History"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.configuration_name} - {self.action} at {self.changed_at}"

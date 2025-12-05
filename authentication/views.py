# hub_auth/authentication/views.py
"""API views for token validation."""
import time
import logging
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db import transaction

from .models import User, TokenValidation, ServiceClient
from .serializers import (
    TokenValidationRequestSerializer,
    TokenValidationResponseSerializer,
    UserInfoSerializer,
    ServiceClientSerializer,
    TokenValidationLogSerializer
)
from .services import MSALTokenValidator, UserSyncService
from .permissions import ServiceClientPermission

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])  # Protected by API key check inside
def validate_token(request):
    """
    Validate a JWT token from MSAL.
    
    This is the main endpoint that other services will call to validate tokens.
    Requires an API key from a registered service client.
    
    POST /api/auth/validate/
    Headers:
        X-API-Key: <service_api_key>
    Body:
        {
            "token": "eyJ0eXAiOiJKV1QiLCJub25jZSI6...",
            "service_name": "employee_manage"
        }
    
    Response:
        {
            "is_valid": true,
            "user": {user_info},
            "token_claims": {decoded_token},
            "validation_id": "uuid"
        }
    """
    start_time = time.time()
    
    # Validate API key
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return Response(
            {'error': 'Missing X-API-Key header'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        service_client = ServiceClient.objects.get(api_key=api_key, is_active=True)
    except ServiceClient.DoesNotExist:
        logger.warning(f"Invalid API key attempted from IP: {get_client_ip(request)}")
        return Response(
            {'error': 'Invalid or inactive API key'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Update service client last used
    service_client.last_used = timezone.now()
    service_client.total_validations += 1
    service_client.save(update_fields=['last_used', 'total_validations'])
    
    # Validate request data
    serializer = TokenValidationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    service_name = serializer.validated_data['service_name']
    
    # Validate the token
    validator = MSALTokenValidator()
    is_valid, decoded_token, error_message = validator.validate_token(token)
    
    # Calculate validation time
    validation_time_ms = int((time.time() - start_time) * 1000)
    
    # Sync user if token is valid
    user = None
    if is_valid and decoded_token:
        try:
            sync_service = UserSyncService()
            user = sync_service.sync_user_from_token(decoded_token)
        except Exception as e:
            logger.error(f"Error syncing user from token: {str(e)}", exc_info=True)
            error_message = f"User sync error: {str(e)}"
            is_valid = False
    
    # Log the validation attempt
    try:
        validation_log = TokenValidation.objects.create(
            user=user,
            service_name=service_name,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get('User-Agent', '')[:500],
            token_oid=decoded_token.get('oid') if decoded_token else None,
            token_upn=decoded_token.get('upn') if decoded_token else None,
            token_app_id=decoded_token.get('appid') if decoded_token else None,
            is_valid=is_valid,
            error_message=error_message,
            validation_time_ms=validation_time_ms
        )
        
        # Update service client stats
        if is_valid:
            service_client.successful_validations += 1
        else:
            service_client.failed_validations += 1
        service_client.save(update_fields=['successful_validations', 'failed_validations'])
        
    except Exception as e:
        logger.error(f"Error logging validation: {str(e)}", exc_info=True)
        validation_log = None
    
    # Build response
    response_data = {
        'is_valid': is_valid,
        'error_message': error_message,
        'user': UserInfoSerializer(user).data if user else None,
        'token_claims': decoded_token if is_valid else None,
        'validation_id': validation_log.id if validation_log else None
    }
    
    response_serializer = TokenValidationResponseSerializer(response_data)
    
    if is_valid:
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(response_serializer.data, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def validate_token_simple(request):
    """
    Simple GET endpoint to validate token from Authorization header.
    
    GET /api/auth/validate-simple/
    Headers:
        Authorization: Bearer <token>
        X-API-Key: <service_api_key>
    
    Response:
        {
            "is_valid": true,
            "user": {minimal_user_info}
        }
    """
    # Check API key
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return Response({'error': 'Missing X-API-Key header'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        service_client = ServiceClient.objects.get(api_key=api_key, is_active=True)
    except ServiceClient.DoesNotExist:
        return Response({'error': 'Invalid API key'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Extract token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Invalid Authorization header format'}, status=status.HTTP_400_BAD_REQUEST)
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    # Validate token
    validator = MSALTokenValidator()
    is_valid, decoded_token, error_message = validator.validate_token(token)
    
    if is_valid and decoded_token:
        try:
            sync_service = UserSyncService()
            user = sync_service.sync_user_from_token(decoded_token)
            
            return Response({
                'is_valid': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'display_name': user.display_name,
                    'is_active': user.is_active
                }
            })
        except Exception as e:
            logger.error(f"Error syncing user: {str(e)}", exc_info=True)
            return Response({'is_valid': False, 'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({'is_valid': False, 'error': error_message}, status=status.HTTP_401_UNAUTHORIZED)


class ServiceClientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing service clients (admin only)."""
    
    queryset = ServiceClient.objects.all()
    serializer_class = ServiceClientSerializer
    permission_classes = [ServiceClientPermission]
    
    @action(detail=True, methods=['post'])
    def regenerate_api_key(self, request, pk=None):
        """Regenerate API key for a service client."""
        import secrets
        
        service_client = self.get_object()
        new_api_key = secrets.token_urlsafe(32)
        service_client.api_key = new_api_key
        service_client.save(update_fields=['api_key', 'updated_at'])
        
        return Response({
            'message': 'API key regenerated successfully',
            'api_key': new_api_key
        })


class TokenValidationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing token validation logs (admin only)."""
    
    queryset = TokenValidation.objects.all().select_related('user')
    serializer_class = TokenValidationLogSerializer
    permission_classes = [ServiceClientPermission]
    filterset_fields = ['service_name', 'is_valid', 'user']
    search_fields = ['service_name', 'token_upn', 'ip_address']
    ordering = ['-validation_timestamp']


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


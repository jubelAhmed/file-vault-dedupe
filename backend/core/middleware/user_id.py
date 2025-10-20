"""
UserId middleware for extracting and validating UserId header from requests.
"""
import re
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class UserIdMiddleware(MiddlewareMixin):
    """
    Middleware to extract and validate UserId header from requests.
    
    This middleware:
    1. Extracts UserId from HTTP header
    2. Validates UserId format
    3. Attaches user_id to request object for use in views
    4. Returns 401 error if UserId is missing or invalid
    """
    
    # UserId validation pattern (alphanumeric, underscore, hyphen, 3-50 chars)
    USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
    
    def process_request(self, request):
        """
        Process incoming request to extract and validate UserId.
        
        Args:
            request: Django HttpRequest object
            
        Returns:
            JsonResponse: Error response if UserId is invalid, None if valid
        """
        # Skip UserId validation for certain paths (health checks, static files, etc.)
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Extract UserId from header
        user_id = request.headers.get('UserId') or request.headers.get('userid')
        
        if not user_id:
            return JsonResponse(
                {
                    'error': 'UserId header is required',
                    'message': 'Please include a valid UserId header in your request'
                },
                status=401
            )
        
        # Validate UserId format
        if not self.USER_ID_PATTERN.match(user_id):
            return JsonResponse(
                {
                    'error': 'Invalid UserId format',
                    'message': 'UserId must be 3-50 characters long and contain only letters, numbers, underscores, and hyphens'
                },
                status=401
            )
        
        # Attach user_id to request for use in views
        request.user_id = user_id
        
        return None
    
    def process_response(self, request, response):
        """
        Process outgoing response (optional - can add response headers here).
        
        Args:
            request: Django HttpRequest object
            response: Django HttpResponse object
            
        Returns:
            HttpResponse: Modified response
        """
        # Add UserId to response headers for debugging (optional)
        if hasattr(request, 'user_id'):
            response['X-User-Id'] = request.user_id
        
        return response


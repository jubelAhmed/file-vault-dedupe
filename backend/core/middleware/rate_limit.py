"""
Rate limiting middleware for controlling API request frequency.

This custom middleware is designed specifically for UserId header-based rate limiting,
which is more suitable than DRF's UserRateThrottle for this architecture since:
1. We use UserId headers instead of Django authentication
2. We need custom response format and path skipping
3. We want full control over rate limiting behavior
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import time
import threading


class RateLimitMiddleware(MiddlewareMixin):
    """
    Custom rate limiting middleware for UserId header-based systems.
    
    Features:
    - UserId header-based rate limiting (not Django auth)
    - Configurable via environment variables
    - Path-based skipping (health, admin, static files)
    - Thread-safe in-memory storage
    - Automatic cleanup of old timestamps
    
    Configuration:
    - RATE_LIMIT_CALLS: Maximum calls per time window (default: 2)
    - RATE_LIMIT_WINDOW: Time window in seconds (default: 1)
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.calls = {}  # {user_id: [timestamps]}
        self.lock = threading.Lock()  # Thread safety
        self.MAX_CALLS = getattr(settings, 'RATE_LIMIT_CALLS', 2)
        self.TIME_WINDOW = getattr(settings, 'RATE_LIMIT_WINDOW', 1)  # seconds
    
    def process_request(self, request):
        """
        Check rate limit for the user.
        
        Args:
            request: Django HttpRequest object
            
        Returns:
            JsonResponse: Rate limit exceeded response, None if within limits
        """
        # Skip rate limiting for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Only apply rate limiting if user_id is available
        if not hasattr(request, 'user_id'):
            return None
        
        user_id = request.user_id
        now = time.time()
        
        # Thread-safe rate limiting
        with self.lock:
            # Clean old calls outside the time window
            if user_id in self.calls:
                self.calls[user_id] = [
                    timestamp for timestamp in self.calls[user_id]
                    if now - timestamp < self.TIME_WINDOW
                ]
            else:
                self.calls[user_id] = []
            
            # Check if user has exceeded rate limit
            if len(self.calls[user_id]) >= self.MAX_CALLS:
                return JsonResponse(
                    {
                        'error': 'Call Limit Reached',
                        'message': f'Maximum {self.MAX_CALLS} calls per {self.TIME_WINDOW} second(s) allowed',
                        'retry_after': self.TIME_WINDOW,
                        'current_calls': len(self.calls[user_id]),
                        'user_id': user_id
                    },
                    status=429
                )
            
            # Record this call
            self.calls[user_id].append(now)
        
        return None


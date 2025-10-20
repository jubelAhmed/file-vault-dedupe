from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache
import time

class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware using Django cache.
    Suitable for multi-container deployments (Redis/Memcached).
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.MAX_CALLS = getattr(settings, 'RATE_LIMIT_CALLS', 2)
        self.TIME_WINDOW = getattr(settings, 'RATE_LIMIT_WINDOW', 1)
        self.CACHE_PREFIX = 'rate-limit'

    def process_request(self, request):
        # Skip certain paths
        skip_paths = ['/admin/', '/static/', '/media/', '/health/', '/favicon.ico']
        if any(request.path.startswith(path) for path in skip_paths):
            return None

        # Get user_id from request attribute or header
        user_id = getattr(request, 'user_id', None) or request.META.get('HTTP_USERID')
        if not user_id:
            return None

        now = time.time()
        cache_key = f"{self.CACHE_PREFIX}:{user_id}"

        # Retrieve timestamps from cache
        timestamps = cache.get(cache_key, [])
        # Keep only timestamps within the window
        timestamps = [ts for ts in timestamps if now - ts < self.TIME_WINDOW]

        # Rate limit exceeded?
        if len(timestamps) >= self.MAX_CALLS:
            response = JsonResponse(
                {
                    'error': 'Call Limit Reached',
                    'message': f'Maximum {self.MAX_CALLS} calls per {self.TIME_WINDOW} second(s) allowed',
                    'retry_after': self.TIME_WINDOW,
                    'current_calls': len(timestamps),
                    'user_id': user_id
                },
                status=429
            )
            response['Retry-After'] = self.TIME_WINDOW
            return response

        # Record this request and save back to cache
        timestamps.append(now)
        cache.set(cache_key, timestamps, timeout=self.TIME_WINDOW)

        return None
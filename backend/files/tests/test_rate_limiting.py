"""
Test cases for rate limiting functionality.
"""
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class RateLimitTestCase(APITestCase):
    """Test rate limiting functionality."""
    
    def setUp(self):
        self.client = APIClient()
        self.user_id = "testuser123"
        self.small_file = SimpleUploadedFile(
            "test.txt", 
            b"Hello", 
            content_type="text/plain"
        )
    
    @override_settings(RATE_LIMIT_CALLS=2, RATE_LIMIT_WINDOW=1)
    def test_rate_limiting(self):
        """Test rate limiting enforcement."""
        # Make requests up to the limit
        response1 = self.client.get('/api/files/', HTTP_UserId=self.user_id)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        response2 = self.client.get('/api/files/', HTTP_UserId=self.user_id)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Third request should be rate limited
        response3 = self.client.get('/api/files/', HTTP_UserId=self.user_id)
        self.assertEqual(response3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response3.json())
        self.assertEqual(response3.json()['error'], 'Call Limit Reached')
    
    @override_settings(RATE_LIMIT_CALLS=2, RATE_LIMIT_WINDOW=1)
    def test_rate_limiting_per_user(self):
        """Test that rate limiting is per user."""
        user1_id = "user1"
        user2_id = "user2"
        
        # User1 hits rate limit
        self.client.get('/api/files/', HTTP_UserId=user1_id)
        self.client.get('/api/files/', HTTP_UserId=user1_id)
        response1 = self.client.get('/api/files/', HTTP_UserId=user1_id)
        self.assertEqual(response1.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # User2 should still be able to make requests
        response2 = self.client.get('/api/files/', HTTP_UserId=user2_id)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
    
    def test_rate_limiting_skip_paths(self):
        """Test that rate limiting is skipped for certain paths."""
        # Health check should not be rate limited
        for _ in range(10):
            response = self.client.get('/health/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

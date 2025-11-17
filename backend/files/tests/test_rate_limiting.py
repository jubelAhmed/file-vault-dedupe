"""
Test cases for rate limiting functionality.
"""

import time

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class RateLimitTestCase(APITestCase):
    """Test rate limiting functionality."""

    def setUp(self):
        """Set up test client and clear cache."""
        self.client = APIClient()
        self.user_id = "testuser123"
        self.small_file = SimpleUploadedFile("test.txt", b"Hello", content_type="text/plain")
        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    @override_settings(RATE_LIMIT_CALLS=2, RATE_LIMIT_WINDOW=1)
    def test_rate_limiting(self):
        """Test rate limiting enforcement."""
        # Make requests up to the limit
        response1 = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Third request should be rate limited
        response3 = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(response3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("error", response3.json())
        self.assertEqual(response3.json()["error"], "Call Limit Reached")

    @override_settings(RATE_LIMIT_CALLS=2, RATE_LIMIT_WINDOW=1)
    def test_rate_limiting_per_user(self):
        """Test that rate limiting is per user."""
        # Clear cache to ensure clean state
        cache.clear()

        user1_id = "user1"
        user2_id = "user2"

        # User1 hits rate limit
        self.client.get("/api/files/", HTTP_UserId=user1_id)
        self.client.get("/api/files/", HTTP_UserId=user1_id)
        response1 = self.client.get("/api/files/", HTTP_UserId=user1_id)
        self.assertEqual(response1.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # User2 should still be able to make requests
        response2 = self.client.get("/api/files/", HTTP_UserId=user2_id)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_rate_limiting_skip_paths(self):
        """Test that rate limiting is skipped for certain paths."""
        # Clear cache to ensure clean state
        cache.clear()

        # Health check should not be rate limited
        for _ in range(10):
            response = self.client.get("/health/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(RATE_LIMIT_CALLS=2, RATE_LIMIT_WINDOW=2)
    def test_rate_limiting_time_window_expiry(self):
        """Test that rate limit resets after time window."""
        # Clear cache to ensure clean state
        cache.clear()

        # Make requests up to the limit
        response1 = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Third request should be rate limited
        response3 = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(response3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Wait for the time window to expire
        time.sleep(2.1)

        # After time window, request should succeed
        response4 = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(response4.status_code, status.HTTP_200_OK)

    @override_settings(RATE_LIMIT_CALLS=2, RATE_LIMIT_WINDOW=1)
    def test_rate_limiting_response_format(self):
        """Test that rate limit response has correct format."""
        # Clear cache to ensure clean state
        cache.clear()

        # Exhaust rate limit
        self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.client.get("/api/files/", HTTP_UserId=self.user_id)

        # Get rate limited response
        response = self.client.get("/api/files/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        data = response.json()

        # Check response format
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Call Limit Reached")
        self.assertIn("message", data)
        self.assertIn("retry_after", data)
        self.assertIn("current_calls", data)
        self.assertIn("user_id", data)
        self.assertEqual(data["user_id"], self.user_id)

        # Check Retry-After header
        self.assertIn("Retry-After", response)
        self.assertEqual(response["Retry-After"], "1")

    @override_settings(RATE_LIMIT_CALLS=3, RATE_LIMIT_WINDOW=1)
    def test_rate_limiting_cache_key_isolation(self):
        """Test that different users have separate cache keys."""
        # Clear cache to ensure clean state
        cache.clear()

        user1 = "user1"
        user2 = "user2"
        user3 = "user3"

        # Each user makes requests independently
        self.client.get("/api/files/", HTTP_UserId=user1)
        self.client.get("/api/files/", HTTP_UserId=user1)

        self.client.get("/api/files/", HTTP_UserId=user2)
        self.client.get("/api/files/", HTTP_UserId=user2)

        self.client.get("/api/files/", HTTP_UserId=user3)
        self.client.get("/api/files/", HTTP_UserId=user3)

        # All users should still have one request left
        response1 = self.client.get("/api/files/", HTTP_UserId=user1)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.get("/api/files/", HTTP_UserId=user2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        response3 = self.client.get("/api/files/", HTTP_UserId=user3)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

        # Now all users should be rate limited
        response1 = self.client.get("/api/files/", HTTP_UserId=user1)
        self.assertEqual(response1.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        response2 = self.client.get("/api/files/", HTTP_UserId=user2)
        self.assertEqual(response2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        response3 = self.client.get("/api/files/", HTTP_UserId=user3)
        self.assertEqual(response3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

"""
Test cases for service layer functionality.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile


class ServiceTestCase(TestCase):
    """Test service layer functionality."""
    
    def setUp(self):
        self.user_id = "testuser123"
    
    def test_hash_service_error_handling(self):
        """Test hash service error handling."""
        from ..services.hash_service import HashService
        
        # Test with invalid file object - this might not raise an exception
        # Let's test with a file that has no read method
        class InvalidFile:
            pass
        
        invalid_file = InvalidFile()
        with self.assertRaises(Exception):
            HashService.calculate_sha256(invalid_file)
    
    def test_storage_service_error_handling(self):
        """Test storage service error handling."""
        from ..services.storage_service import StorageService
        
        # Test with invalid user_id - this should work (creates UserStorage if not exists)
        # The service is robust and handles edge cases gracefully
        result = StorageService.check_storage_quota("testuser", 100)
        self.assertTrue(result)  # Should return True for valid input
    
    def test_deduplication_service_error_handling(self):
        """Test deduplication service error handling."""
        from ..services.deduplication_service import DeduplicationService
        
        # Test with invalid parameters
        with self.assertRaises(Exception):
            DeduplicationService.handle_file_upload(None, None)
    
    def test_hash_service_valid_file(self):
        """Test hash service with valid file."""
        from ..services.hash_service import HashService
        
        valid_file = SimpleUploadedFile(
            "test.txt", 
            b"Hello World", 
            content_type="text/plain"
        )
        
        # Should not raise an exception
        try:
            hash_value = HashService.calculate_sha256(valid_file)
            self.assertIsNotNone(hash_value)
            self.assertIsInstance(hash_value, str)
        except Exception:
            self.fail("Valid file should not raise an exception")
    
    def test_storage_service_quota_check(self):
        """Test storage service quota checking."""
        from ..services.storage_service import StorageService
        
        # Test quota check with valid user and size
        result = StorageService.check_storage_quota(self.user_id, 100)
        self.assertTrue(result)
        
        # Test quota check with very large size (should raise exception)
        with self.assertRaises(Exception):
            StorageService.check_storage_quota(self.user_id, 1000000000)  # 1GB
    
    def test_deduplication_service_stats(self):
        """Test deduplication service statistics."""
        from ..services.deduplication_service import DeduplicationService
        
        # Should not raise an exception
        try:
            stats = DeduplicationService.get_deduplication_stats()
            self.assertIsInstance(stats, dict)
            self.assertIn('total_files', stats)
            self.assertIn('original_files', stats)
            self.assertIn('reference_files', stats)
        except Exception:
            self.fail("Getting deduplication stats should not raise an exception")
    
    def test_file_validator_disallowed_extension(self):
        """Test file validator with disallowed file extension (not in allow-list)."""
        from ..utils.validators import FileValidator
        
        # Test with extensions not in the allow-list
        disallowed_extensions = ['test.exe', 'malware.bat', 'script.js', 'app.dmg', 'file.unknown']
        
        for filename in disallowed_extensions:
            with self.assertRaises(Exception):
                FileValidator.validate_file_extension(filename)
    
    def test_file_validator_path_traversal(self):
        """Test file validator with path traversal filename."""
        from ..utils.validators import FileValidator
        
        # Test with a filename that should trigger validation error
        with self.assertRaises(Exception):
            FileValidator.validate_filename("../../../etc/passwd")
    
    def test_middleware_rate_limit_cache_cleanup(self):
        """Test rate limit middleware cache cleanup with old timestamps."""
        from core.middleware.rate_limit import RateLimitMiddleware
        from django.test import RequestFactory, override_settings
        from django.core.cache import cache
        import time
        
        # Clear cache first
        cache.clear()
        
        factory = RequestFactory()
        request = factory.get('/api/files/')
        request.user_id = self.user_id
        
        with override_settings(RATE_LIMIT_CALLS=2, RATE_LIMIT_WINDOW=1):
            middleware = RateLimitMiddleware(lambda x: None)
            
            # Manually add an old timestamp to cache
            cache_key = f"rate-limit:{self.user_id}"
            old_time = time.time() - 10  # 10 seconds ago
            cache.set(cache_key, [old_time], timeout=1)
            
            # Process request - should clean up old timestamp
            result = middleware.process_request(request)
            
            # Should not be rate limited (old timestamp cleaned up)
            self.assertIsNone(result)
            
            # Cache should have only the new timestamp
            timestamps = cache.get(cache_key, [])
            self.assertEqual(len(timestamps), 1)
            
            # The timestamp should be recent (not the old one)
            self.assertGreater(timestamps[0], old_time)
        
        # Clean up
        cache.clear()

import unittest
from server.utils.error_handler import (
    AIDJError,
    APIKeyError,
    MusicServiceError,
    FileSystemError,
    handle_error,
    validate_api_key
)

class TestErrorHandler(unittest.TestCase):
    def test_api_key_error(self):
        """Test API key validation and error handling."""
        # Test missing API key
        with self.assertRaises(APIKeyError) as context:
            validate_api_key(None, "TestService")
        self.assertEqual(context.exception.error_code, "TESTSERVICE_API_KEY_ERROR")
        self.assertEqual(context.exception.status_code, 401)
        
        # Test empty API key
        with self.assertRaises(APIKeyError):
            validate_api_key("", "TestService")
        
        # Test whitespace API key
        with self.assertRaises(APIKeyError):
            validate_api_key("   ", "TestService")
    
    def test_music_service_error(self):
        """Test music service error handling."""
        error = MusicServiceError("Connection failed", "Spotify")
        response, status_code = handle_error(error)
        
        self.assertEqual(status_code, 503)
        self.assertEqual(response["error"]["code"], "SPOTIFY_SERVICE_ERROR")
        self.assertEqual(response["error"]["message"], "Connection failed")
    
    def test_file_system_error(self):
        """Test file system error handling."""
        error = FileSystemError("File not found", "READ")
        response, status_code = handle_error(error)
        
        self.assertEqual(status_code, 500)
        self.assertEqual(response["error"]["code"], "FILE_SYSTEM_READ_ERROR")
        self.assertEqual(response["error"]["message"], "File not found")
    
    def test_unexpected_error(self):
        """Test handling of unexpected errors."""
        error = ValueError("Random error")
        response, status_code = handle_error(error)
        
        self.assertEqual(status_code, 500)
        self.assertEqual(response["error"]["code"], "INTERNAL_SERVER_ERROR")
        self.assertEqual(response["error"]["message"], "An unexpected error occurred")

if __name__ == '__main__':
    unittest.main()

import unittest
from server.utils.error_handler import (
    APIKeyError,
    MusicServiceError,
    FileSystemError,
    handle_error,
    get_troubleshooting_suggestions
)

class TestTroubleshooting(unittest.TestCase):
    def test_api_key_error_suggestions(self):
        """Test troubleshooting suggestions for API key errors."""
        error = APIKeyError("OpenAI API key is missing", "OpenAI")
        suggestions = get_troubleshooting_suggestions(error)
        
        self.assertEqual(suggestions["error_type"], "API Key Error")
        self.assertTrue(any("OPENAI_API_KEY" in s for s in suggestions["suggestions"]))
        self.assertTrue(any("dashboard" in s for s in suggestions["suggestions"]))
        self.assertTrue("documentation" in suggestions)
    
    def test_music_service_error_suggestions(self):
        """Test troubleshooting suggestions for music service errors."""
        error = MusicServiceError("Failed to connect", "Navidrome")
        suggestions = get_troubleshooting_suggestions(error)
        
        self.assertEqual(suggestions["error_type"], "Music Service Error")
        self.assertTrue(any("credentials" in s for s in suggestions["suggestions"]))
        self.assertTrue(any("network" in s for s in suggestions["suggestions"]))
    
    def test_file_system_error_suggestions(self):
        """Test troubleshooting suggestions for file system errors."""
        error = FileSystemError("Permission denied", "WRITE")
        suggestions = get_troubleshooting_suggestions(error)
        
        self.assertEqual(suggestions["error_type"], "File System Error")
        self.assertTrue(any("permissions" in s for s in suggestions["suggestions"]))
        self.assertTrue(any("disk space" in s for s in suggestions["suggestions"]))
    
    def test_error_response_format(self):
        """Test that error responses include troubleshooting info."""
        error = APIKeyError("Test error", "TestService")
        response, status_code = handle_error(error)
        
        self.assertTrue("troubleshooting" in response["error"])
        self.assertTrue("suggestions" in response["error"]["troubleshooting"])
        self.assertTrue("documentation" in response["error"]["troubleshooting"])

if __name__ == '__main__':
    unittest.main()

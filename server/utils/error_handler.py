import logging
import traceback
from functools import wraps
from flask import jsonify
from typing import Optional, Dict, Any, Type

# Configure logging
logger = logging.getLogger(__name__)

class AIDJError(Exception):
    """Base exception class for AI DJ application."""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

class APIKeyError(AIDJError):
    """Raised when there are issues with API keys."""
    def __init__(self, message: str, service: str):
        super().__init__(
            message=message,
            error_code=f"{service.upper()}_API_KEY_ERROR",
            status_code=401
        )

class MusicServiceError(AIDJError):
    """Raised when there are issues with music services."""
    def __init__(self, message: str, service: str):
        super().__init__(
            message=message,
            error_code=f"{service.upper()}_SERVICE_ERROR",
            status_code=503
        )

class FileSystemError(AIDJError):
    """Raised when there are issues with file operations."""
    def __init__(self, message: str, operation: str):
        super().__init__(
            message=message,
            error_code=f"FILE_SYSTEM_{operation.upper()}_ERROR",
            status_code=500
        )

def get_troubleshooting_suggestions(error: Exception) -> Dict[str, Any]:
    """Get troubleshooting suggestions for common errors."""
    if isinstance(error, APIKeyError):
        service = error.error_code.split('_')[0].lower()
        return {
            "error_type": "API Key Error",
            "suggestions": [
                f"Check if {service.upper()}_API_KEY is set in your .env file",
                f"Verify the {service} API key is valid in your {service} dashboard",
                "Restart the application to reload environment variables",
                f"Check if your {service} account has sufficient credits/permissions"
            ],
            "documentation": f"See docs/troubleshooting.md#1-{service}-api-key-error"
        }
    
    elif isinstance(error, MusicServiceError):
        service = error.error_code.split('_')[0].lower()
        return {
            "error_type": "Music Service Error",
            "suggestions": [
                f"Verify {service} service is running and accessible",
                "Check your network connection",
                f"Review {service} credentials in .env file",
                "Check service status and maintenance schedules"
            ],
            "documentation": f"See docs/troubleshooting.md#{service}-service-error"
        }
    
    elif isinstance(error, FileSystemError):
        operation = error.error_code.split('_')[2].lower()
        return {
            "error_type": "File System Error",
            "suggestions": [
                "Verify required directories exist (logs/, playlists/, data/)",
                "Check file and directory permissions",
                "Ensure sufficient disk space",
                "Close any applications that might lock the files"
            ],
            "documentation": f"See docs/troubleshooting.md#file-system-{operation}-error"
        }
    
    # Default suggestions for unexpected errors
    return {
        "error_type": "Unexpected Error",
        "suggestions": [
            "Check the application logs for detailed error information",
            "Verify all required services are running",
            "Restart the application",
            "Contact support if the issue persists"
        ],
        "documentation": "See docs/troubleshooting.md#debugging-tips"
    }

def handle_error(e: Exception) -> tuple[Dict[str, Any], int]:
    """Convert exceptions to JSON responses with appropriate status codes."""
    if isinstance(e, AIDJError):
        error_response = {
            "error": {
                "code": e.error_code,
                "message": e.message,
                "troubleshooting": get_troubleshooting_suggestions(e)
            }
        }
        return error_response, e.status_code
    
    # Handle unexpected errors
    logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "troubleshooting": get_troubleshooting_suggestions(e)
        }
    }
    return error_response, 500

def api_error_handler(f):
    """Decorator to handle API endpoint errors consistently."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_response, status_code = handle_error(e)
            return jsonify(error_response), status_code
    return decorated_function

def validate_api_key(api_key: Optional[str], service: str) -> None:
    """Validate API key presence and format."""
    if not api_key:
        raise APIKeyError(f"{service} API key is missing", service)
    if not isinstance(api_key, str) or len(api_key.strip()) == 0:
        raise APIKeyError(f"Invalid {service} API key format", service)

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log error with context for debugging."""
    error_type = type(error).__name__
    error_message = str(error)
    error_traceback = traceback.format_exc()
    
    log_data = {
        "error_type": error_type,
        "error_message": error_message,
        "traceback": error_traceback
    }
    
    if context:
        log_data["context"] = context
    
    logger.error(f"Error occurred: {log_data}")

"""
Custom Exception Classes for Facebook Dashboard Backend

This module provides a unified exception hierarchy for consistent error handling
across the application. All custom exceptions inherit from AppException.
"""
from typing import Optional, Dict, Any


class AppException(Exception):
    """
    Base exception class for all application exceptions.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (e.g., 'AUTH_FAILED')
        status_code: HTTP status code to return
        details: Additional error details (optional)
    """
    def __init__(
        self, 
        message: str, 
        error_code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


# --- Authentication Errors ---

class AuthenticationError(AppException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="AUTH_FAILED",
            status_code=401,
            details=details
        )


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired."""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message)
        self.error_code = "TOKEN_EXPIRED"


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid."""
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message)
        self.error_code = "INVALID_TOKEN"


# --- Authorization Errors ---

class AuthorizationError(AppException):
    """Raised when user lacks permission."""
    def __init__(self, message: str = "Permission denied", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            status_code=403,
            details=details
        )


# --- Facebook API Errors ---

class FacebookAPIError(AppException):
    """Raised when Facebook API returns an error."""
    def __init__(
        self, 
        message: str = "Facebook API error", 
        fb_error_code: Optional[int] = None,
        fb_error_subcode: Optional[int] = None,
        details: Optional[Dict] = None
    ):
        super().__init__(
            message=message,
            error_code="FACEBOOK_API_ERROR",
            status_code=400,
            details={
                "fb_error_code": fb_error_code,
                "fb_error_subcode": fb_error_subcode,
                **(details or {})
            }
        )


class FacebookRateLimitError(FacebookAPIError):
    """Raised when Facebook API rate limit is hit."""
    def __init__(self, message: str = "Facebook API rate limit exceeded"):
        super().__init__(message=message)
        self.error_code = "FACEBOOK_RATE_LIMIT"
        self.status_code = 429


class FacebookTokenError(FacebookAPIError):
    """Raised when Facebook access token is invalid or expired."""
    def __init__(self, message: str = "Facebook access token is invalid or expired"):
        super().__init__(message=message)
        self.error_code = "FACEBOOK_TOKEN_ERROR"
        self.status_code = 401


# --- Resource Errors ---

class ResourceNotFoundError(AppException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str = "Resource", resource_id: Optional[str] = None):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class TeamNotFoundError(ResourceNotFoundError):
    """Raised when team is not found."""
    def __init__(self, team_id: Optional[str] = None):
        super().__init__(resource_type="Team", resource_id=team_id)


class UserNotFoundError(ResourceNotFoundError):
    """Raised when user is not found."""
    def __init__(self, user_id: Optional[str] = None):
        super().__init__(resource_type="User", resource_id=user_id)


# --- Validation Errors ---

class ValidationError(AppException):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation failed", field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field} if field else {}
        )


# --- Database Errors ---

class DatabaseError(AppException):
    """Raised when database operation fails."""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500
        )

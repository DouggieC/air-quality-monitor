"""
Custom exception hierarchy for the application.

Provides specific exception types for API, storage, and parsing errors
to enable targeted error handling in the data collection pipeline.
"""


class ApplicationError(Exception):
    """Base class for all application-specific errors."""
    pass


class APIError(ApplicationError):
    """Error communicating with external APIs (IQAir, OpenWeatherMap)."""
    pass


class StorageError(ApplicationError):
    """Error reading from or writing to storage backends."""
    pass


class ParseError(ApplicationError):
    """Error parsing API response data into domain models."""
    pass

"""
Service Modules Package for Facebook Dashboard Backend

This package organizes backend services into modular components:
- facebook_api: Pure Facebook Graph API calls
- metrics: Metric calculations and formatting
- cache: Caching service (already in cache.py)

Note: This package is named 'service_modules' to avoid conflict with existing services.py
"""

from .facebook_api import FacebookAPIClient
from .metrics import MetricsCalculator

__all__ = ['FacebookAPIClient', 'MetricsCalculator']

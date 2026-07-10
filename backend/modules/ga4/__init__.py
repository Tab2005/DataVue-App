"""
GA4 module package.

Avoid eager imports here so lightweight submodules (for example anomaly.py tests)
can be imported without requiring optional Google Analytics SDK dependencies.
"""

__all__ = [
    "client",
    "service",
    "repository",
    "anomaly",
    "insights_service",
    "insights_router",
]

"""
Meta Andromeda Module
Meta/Facebook creative scoring and operations console integration for DataVue.
"""

from .router import router
from .service import MetaAndromedaService
from .dependencies import get_current_meta_andromeda_user

__all__ = [
    "router",
    "MetaAndromedaService",
    "get_current_meta_andromeda_user",
]

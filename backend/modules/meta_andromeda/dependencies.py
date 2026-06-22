"""
Meta Andromeda Module - Dependencies
"""

from fastapi import Depends

from modules.auth.dependencies import get_current_user, require_module, require_permission


def get_current_meta_andromeda_user(user=Depends(get_current_user)):
    """Re-export current user dependency for module-local usage."""
    return user


require_meta_andromeda_module = require_module("meta_andromeda")
require_fb_ads_module = require_module("fb_ads")
require_fb_ads_analytics_view = require_permission("fb_ads:analytics:view")
# Meta Andromeda now uses module-only access control.
require_meta_andromeda_operate = require_meta_andromeda_module
require_meta_andromeda_feedback = require_meta_andromeda_module
require_meta_andromeda_release = require_meta_andromeda_module

__all__ = [
    "get_current_meta_andromeda_user",
    "require_meta_andromeda_module",
    "require_fb_ads_module",
    "require_fb_ads_analytics_view",
    "require_meta_andromeda_operate",
    "require_meta_andromeda_feedback",
    "require_meta_andromeda_release",
]

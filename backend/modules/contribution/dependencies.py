"""
Contribution Module - Dependencies

模組存取控制：contribution 採 module-only access（同 Meta Andromeda 現行模式），
不分細項權限。require_contribution_module 為本模組所有端點的共用依賴。
"""

from fastapi import Depends

from modules.auth.dependencies import get_current_user, require_module


def get_current_contribution_user(user=Depends(get_current_user)):
    """Re-export current user dependency for module-local usage."""
    return user


require_contribution_module = require_module("contribution")
# 本模組所有操作（讀取分組、發起分析、編輯分組、補抓資料）皆需模組存取權；
# 細項權限留待第 2 波依使用回饋再拆分（見 docs/21 第 3.5 節）。
require_contribution_operate = require_contribution_module

__all__ = [
    "get_current_contribution_user",
    "require_contribution_module",
    "require_contribution_operate",
]

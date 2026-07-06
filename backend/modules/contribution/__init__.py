"""Contribution Module — MMM 廣告活動貢獻衡量（docs/21）

回答「哪個廣告活動真正帶來增量轉換、下一塊錢該投給誰」。與 Meta Andromeda
（素材層）分工：本模組在活動層（macro）以 MMM 從花費的時間序列共變估計增量貢獻，
暴露 always-on／再行銷活動「收割功勞」的自報偏差。共用 Andromeda 的「模式」（骨架、
require_module 權限、背景任務 + 狀態輪詢、TokenManager 取 token），不共用引擎與資料表。

第 1 波任務 1.1：僅建立骨架與空端點（回 501），引擎 / 抓取 / 分組 / 編排於
任務 1.2–1.4 實作。
"""

from .router import router

__all__ = ["router"]

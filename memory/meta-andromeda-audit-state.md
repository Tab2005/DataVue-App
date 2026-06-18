---
name: meta-andromeda-audit-state
description: Meta Andromeda 模組審查現狀與未修復的高風險問題清單（截至 2026-06-18）
metadata:
  type: project
---

Meta Andromeda 模組（`backend/modules/meta_andromeda`）截至 2026-06-18 的審查結論：

doc 22（`docs/22_Meta_Andromeda_模組復審與優化建議報告.md`）是 HEAD 提交，之後無任何修復 commit。doc 22 列出的 P0/P1 問題**至今全部仍未修復**（已驗證程式碼）：
- `meta_andromeda_observed_creatives` 表仍無 Alembic migration（只有 ORM，3 個 migration 都沒建此表）
- drift report 仍在 read path 隨機建立並持久化 `ma_evt_mock_*` score event（`repository.py:619-640`）
- `ensure_seed_data()` 仍在所有 read API 被呼叫（`repository.py:418,436,443,511,561,722,1000,1027,1057`）
- 前端 Monitoring/Release 仍用 `meta_andromeda:operate`/`:release` feature permission（`MetaAndromedaMonitoring.jsx:32`、`MetaAndromedaRelease.jsx:21`），與後端 module-only 策略不一致
- worker claim / callback 無原子性與冪等性
- scoring runtime 不讀素材內容，只看文字欄位

doc 22 **沒提到、本次新發現**的問題：
- `MetaAndromedaScoreLab.jsx` 完全沒有權限 gate（連 usePermission 都沒 import），任何能進入頁面的使用者都能上傳+送評
- `add_meta_andromeda_score_job`（`scheduler.py:450`）不 gate `is_scheduler_enabled()`，scheduler 關閉時 MA job 仍會被排
- `OpenRouterScoringProvider` 不傳 multimodal/image 給模型，且 OpenRouter client 的 `timeout` 參數是 dead code（從未傳給 SDK）
- confidence 寫死 0.72/0.61；monitoring latency 寫死固定值
- README 稱「有 GOOGLE_AI_API_KEY 走 Gemini」，實際是 OpenRouter（文件漂移）

下次想了解模組狀態時先讀此記憶與 [[meta-andromeda-model-tuning]]。

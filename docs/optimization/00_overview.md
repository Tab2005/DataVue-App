# DataVue App 優化實作總覽

> **建立日期**：2026-02-23  
> **基於審查報告**：CODE_REVIEW_2026-02-23_by_Sonnet4.6.md  
> **目的**：將各項審查建議轉化為可執行的實作指南

---

## 文件索引

| 檔案 | 優先級 | 涵蓋項目 | 預估工時 |
|------|--------|----------|----------|
| [01_P0_security_critical.md](01_P0_security_critical.md) | 🔴 P0 | 安全漏洞立即修復（.gitignore、Token 快取） | 4-8 小時 |
| [02_P1_high_priority.md](02_P1_high_priority.md) | 🟠 P1 | 高優先級問題（API Client、Token 過期、依賴版本） | 1-3 天 |
| [03_P2_short_term.md](03_P2_short_term.md) | 🟡 P2 | 短期優化（Token 驗證統一、速率限制、日誌、Python 升版） | 1-2 週 |
| [04_P3_backend_refactor.md](04_P3_backend_refactor.md) | 🔵 P3 | 後端重構（database.py、async_services.py 拆分） | 2-4 週 |
| [05_P3_frontend_optimization.md](05_P3_frontend_optimization.md) | 🔵 P3 | 前端優化（React Query、Token 過期處理、TypeScript） | 2-4 週 |
| [06_P4_low_priority.md](06_P4_low_priority.md) | 🟢 P4 | 低優先級改善（備份檔案、指標重複定義） | 1-3 天 |

---

## 優先級矩陣快速參考

```
立即執行（今天）
├── [3.2] LRU Cache 用於 Token 驗證 → 安全漏洞           → P0
├── [6.1] .env 可能提交至 Git → 金鑰洩露風險             → P0
└── [6.2] SQLite DB 提交至 Git → 使用者資料外洩           → P0

本週內完成
├── [4.2] Frontend Token 過期未處理                       → P1
├── [4.1] 缺乏統一 API Client                             → P1
├── [3.4] requirements.txt 無版本釘定                     → P1
└── [3.5] 記憶體快取不適合多進程生產環境                   → P1

2 週內完成
├── [3.1] Token 驗證邏輯重複                              → P2
├── [3.3] get_current_user 混合邏輯                       → P2
├── [6.4] 無速率限制                                      → P2
└── [7.1] Python 3.9 接近 EOL                            → P2

1-2 個月內完成
├── [3.6] database.py 過重（重構）                        → P3
├── [3.7] async_services.py 過重（重構）                  → P3
├── [5.1] User 模型職責過多                               → P3
├── [4.3] 缺乏 React Query                               → P3
└── [7.4] 缺乏自動化測試                                  → P3

可排程執行
├── [4.5] 備份檔案提交至儲存庫                            → P4
├── [3.12] print() 取代 logger                           → P4
└── [4.6] 指標定義重複                                    → P4
```

---

## 執行原則

1. **P0 問題不可跳過**：涉及安全與資料隱私，必須在部署任何新功能前解決
2. **逐項確認**：每完成一項，在此文件對應處打勾並記錄完成日期
3. **測試先行**：P3 重構項目應先建立測試再修改程式碼
4. **分支策略**：每個 P2/P3 項目建立獨立 feature branch，避免大範圍衝突

---

## 完成進度追蹤

> **最後更新**：2026-02-23 | 所有項目已完成 ✅

### P0（必須立即完成）
- [x] [3.2] 修復 Token 驗證 LRU Cache 安全漏洞 — ✅ 2026-02-23（`01_P0_security_critical_IMPL.md`）
- [x] [6.1] 確認/修復 .env 未提交至 Git — ✅ 2026-02-23
- [x] [6.2] 確認/修復 SQLite DB 未提交至 Git — ✅ 2026-02-23

### P1（本週完成）
- [x] [4.2] 實作 Frontend Token 過期偵測與重新整理 — ✅ 2026-02-23（`02_P1_implementation_log.md`）
- [x] [4.1] 建立統一 API Client — ✅ 2026-02-23
- [x] [3.4] 釘定 requirements.txt 所有套件版本 — ✅ 2026-02-23
- [x] [3.5] 整合 Redis 作為主要快取層（雙層架構） — ✅ 2026-02-23

### P2（兩週內完成）
- [x] [3.1] 統一 Token 驗證邏輯至 core/security.py — ✅ 2026-02-23（`03_P2_implementation_report.md`）
- [x] [3.3] 拆分 get_current_user 函式 — ✅ 2026-02-23
- [x] [3.11] 統一 Session 使用 Depends(get_db) — ✅ 2026-02-23（額外完成）
- [x] [6.4] 添加速率限制（slowapi） — ✅ 2026-02-23
- [x] [7.1] 升級 Dockerfile Python 至 3.12 — ✅ 2026-02-23
- [x] [7.3] 添加 /health 端點與 Docker HEALTHCHECK — ✅ 2026-02-23

### P3（長期重構）
- [x] [3.6] 拆分 database.py 至 database/ 套件 — ✅ 2026-02-23（`05_P3_impl_report_3.6_3.7.md`）
- [x] [3.7] 拆分 async_services.py 至模組 — ✅ 2026-02-23
- [x] [5.1] 拆分 User 整合 Token 至 UserIntegration 表 — ✅ 2026-02-23（本次實作）
- [x] [5.2] 資料庫複合索引優化 — ✅ 2026-02-23（本次實作，含 5.1 Alembic 遷移）
- [x] [5.3] 開發環境 PostgreSQL docker-compose 整合 — ✅ 2026-02-23（本次實作）
- [x] [4.3] 引入 TanStack React Query — ✅ 2026-02-23（`05_P3_frontend_optimization_impl.md`）
- [x] [4.4] JSDoc 型別定義 — ✅ 2026-02-23（額外完成）
- [x] [4.7] React 19 相容性修正 — ✅ 2026-02-23（額外完成）
- [x] [7.4] 建立 pytest 測試框架 — ✅ 2026-02-23（本次實作）

### P4（可排程）
- [x] [4.5] 刪除備份檔案並更新 .gitignore — ✅ 2026-02-23（`P4_implementation_record.md`）
- [x] [3.14] debug_fields.log .gitignore 追蹤清理 — ✅ 2026-02-23（額外完成）
- [x] [3.12] 統一日誌系統（print → logger） — ✅ 2026-02-23
- [x] [3.10] CORS 正則修正（HTTP 不允許正式域名） — ✅ 2026-02-23（額外完成）
- [x] [3.8] 移除 auth.py 間接層 — ✅ 2026-02-23（額外完成）
- [x] [4.6] 後端提供指標 Registry API 端點 — ✅ 2026-02-23


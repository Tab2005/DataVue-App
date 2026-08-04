# Meta Andromeda Prompt 自適應校準計畫

> **文件編號：** 28  
> **建立日期：** 2026-06-24  
> **狀態：** 規劃中（未實作）

---

## 背景與問題

現有評分循環在打包校準資料集（`MetaAndromedaCalibrationDataset`）後即停止，沒有任何下游消費者使用 `status="queued_for_calibration"` 這個狀態。Scoring prompt 是硬編碼在 `runtime.py:241`，`model_registry.py` 的 `scoring_profile` 欄位只做 lineage 紀錄，從未被用來載入不同的 prompt。

本計畫將閉合這個缺口，讓每次校準資料集同步後自動分析偏差、生成修正版 prompt、建立新的 scoring profile，操作者再決定是否 promote。

---

## 架構概覽

```
sync_calibration_dataset()
  └─ 若 synced_count >= 10
       └─ trigger calibration_pipeline job (APScheduler one-off)
            ├─ analyze_dataset_bias()        → bias_summary
            ├─ generate_calibrated_profile() → 新 ScoringProfile 寫入 DB
            └─ 前端監控頁出現「新版 profile 待審核」+ Promote 按鈕
                  └─ 操作者點 Promote → 更新 model registry default scoring_profile
                       └─ runtime cache 失效 → 下一筆評分使用新 prompt
```

---

## Phase 1：DB-backed Scoring Profiles

### 新增 ORM Model

**檔案：** `backend/database/models/meta_andromeda.py`

```python
class MetaAndromedaScoringProfile(Base):
    __tablename__ = "meta_andromeda_scoring_profiles"
    id = Column(String, primary_key=True, default=lambda: f"sp_{uuid.uuid4().hex[:12]}")
    profile_name         = Column(String, nullable=False, unique=True, index=True)
    user_prompt_template = Column(Text, nullable=False)   # 含 {asset_type} 等佔位符
    system_prompt        = Column(Text, nullable=False)
    calibration_guidance = Column(Text, nullable=True)    # 校準後加入的偏差修正段落
    few_shot_examples    = Column(JSON, nullable=False, default=list)  # [{pred, obs, headline, summary}]
    bias_summary         = Column(JSON, nullable=True)    # 分析結果快照
    source               = Column(String(30), nullable=False, default="seed")  # seed | calibration_auto
    base_profile_name    = Column(String, nullable=True)  # 衍生自哪個 profile
    calibration_dataset_id = Column(String, ForeignKey("meta_andromeda_calibration_datasets.id"), nullable=True)
    is_promoted          = Column(Boolean, nullable=False, default=False)
    promoted_at          = Column(DateTime, nullable=True)
    created_at           = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
```

### 新增 Alembic Migration

**檔案：** `backend/alembic/versions/20260624_add_meta_andromeda_scoring_profiles.py`

遵照 `20260608_meta_andromeda_workflow_tables.py` 的 safe pattern（先 `_table_exists()` 再建立）。

Migration 的 `upgrade()` 中同時 **seed** 現有兩個 profile：
- `creative_scoring_v1` → 現有 hardcoded prompt（`source="seed"`, `is_promoted=False`）
- `creative_scoring_v2` → 同一 prompt（`source="seed"`, `is_promoted=True`）

---

## Phase 2：Runtime 動態載入 Prompt

**檔案：** `backend/modules/meta_andromeda/runtime.py`

1. 在 module level 加入 `_prompt_profile_cache: dict[str, dict] = {}` 和 `_profile_cache_lock = threading.Lock()`
2. 新增 `_load_scoring_profile(profile_name: str, db: Session) -> dict`：查 DB，找不到則 fallback 到 hardcoded 預設；結果 cache 於 module-level dict
3. 新增 `invalidate_prompt_cache(profile_name: str | None = None)` 供 promote 時呼叫
4. 修改 `OpenRouterScoringProvider.score()` 中 `prompt =` 和 `system_prompt =` 兩段：
   - 改從 `_load_scoring_profile(registry_entry.scoring_profile, db)` 取得 template
   - 用 `str.format_map()` 注入動態欄位（`asset_type`、`objective`、`placement_family`、`market`、`request_mode`、`headline`、`primary_text`、`cta`）
   - 若 profile 有 `calibration_guidance`，append 到 user prompt 末尾
   - 若 `few_shot_examples` 非空，append 格式化的 few-shot 段落

---

## Phase 3：Calibration Pipeline 模組

**新檔案：** `backend/modules/meta_andromeda/calibration_pipeline.py`

### `analyze_dataset_bias(db, dataset_id) -> dict`

從 `MetaAndromedaCalibrationItem` 讀取該 dataset 所有 items，計算：

| 欄位 | 說明 |
|---|---|
| `total_items` | 誤判總數 |
| `overall_error_rate` | average error |
| `confusion_matrix` | `{ actual_band: { predicted_band: count } }` |
| `dominant_bias` | `"over_predict"` \| `"under_predict"` \| `"mixed"` |
| `worst_examples` | error=2（最大誤差）的前 3 筆，含 headline、summary、prediction_band、observed_band |
| `min_samples_met` | `total_items >= 10` |

### `generate_calibrated_profile(db, dataset_id, base_profile_name) -> str`

1. 呼叫 `analyze_dataset_bias`
2. 依 `dominant_bias` 選擇對應的 calibration_guidance 文字（rule-based，不呼叫 LLM）：
   - **over_predict** → `"CALIBRATION NOTE: Recent data shows tendency to over-predict performance bands. Apply stricter thresholds for HIGH classification. Require multiple strong positive signals with no significant risk tags before assigning high band."`
   - **under_predict** → `"CALIBRATION NOTE: Recent data shows tendency to under-predict. Do not be overly conservative. If creatives show clear visual hierarchy, compelling CTA, and relevant messaging, lean towards mid or high band."`
   - **mixed** → `"CALIBRATION NOTE: Recent calibration shows inconsistent predictions. Pay special attention to risk_tags and diagnostic_breakdown consistency."`
3. 從 `worst_examples` 建立 `few_shot_examples` JSON（格式：預測錯誤案例 + 正確答案說明）
4. 建立新 `MetaAndromedaScoringProfile` 寫入 DB（`is_promoted=False`, `source="calibration_auto"`）
5. 回傳 `new_profile_name`（格式：`{base_profile_name}_cal_{dataset_id[:8]}`）

---

## Phase 4：整合觸發點

**檔案：** `backend/modules/meta_andromeda/service.py`

在 `sync_calibration_dataset()` 末尾，若 `synced_count >= 10`：

```python
add_meta_andromeda_calibration_job(dataset_id, base_profile_name)
```

**檔案：** `backend/core/scheduler.py`

```python
async def run_meta_andromeda_calibration_pipeline(dataset_id: str, base_profile_name: str):
    from modules.meta_andromeda.calibration_pipeline import generate_calibrated_profile
    db = SessionLocal()
    try:
        generate_calibrated_profile(db, dataset_id, base_profile_name)
    finally:
        db.close()

def add_meta_andromeda_calibration_job(dataset_id: str, base_profile_name: str):
    run_at = datetime.now(_LOCAL_TIMEZONE) + timedelta(seconds=5)
    scheduler.add_job(
        run_meta_andromeda_calibration_pipeline,
        trigger="date", run_date=run_at,
        args=[dataset_id, base_profile_name],
        id=f"ma_cal_{dataset_id}",
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
    )
```

---

## Phase 5：Promote API + 前端

### API Endpoints

**檔案：** `backend/modules/meta_andromeda/router.py`

| Method | Path | 說明 |
|---|---|---|
| `GET` | `/monitoring/scoring-profiles` | 列出所有 profiles，含 `is_promoted`、`source`、`bias_summary`、`created_at` |
| `POST` | `/monitoring/scoring-profiles/{profile_name}/promote` | 將指定 profile 設為 promoted；舊 promoted 設為 False；呼叫 `invalidate_prompt_cache()`；更新 model registry |

> **注意：** 兩個端點已在前一版本（前次 session）實作為 Scoring Profile 列表與 Promote 功能的基礎，但彼時 profile 為 in-memory；本計畫將改為 DB-backed。

### 前端更新

**檔案：** `frontend/src/pages/MetaAndromedaMonitoring.jsx`

在現有「Worker 主機」section 下方新增「Scoring Profiles」panel：
- 列表顯示所有 profiles：`profile_name`、`source` badge（`seed` / `auto`）、`is_promoted` 標記、`created_at`
- 若有未 promoted 的 `calibration_auto` profile：顯示黃色卡片「有新版校準 Profile 待審核」+ `bias_summary` 摘要 + Promote 按鈕
- Promote 後自動 reload summary

**檔案：** `frontend/src/services/metaAndromedaMonitoringService.js`
- `fetchScoringProfiles()` — 已實作
- `promoteScoringProfile(profileName)` — 已實作

---

## 修改檔案清單

| 類型 | 路徑 | 所屬 Phase |
|---|---|---|
| 修改（新增 model） | `backend/database/models/meta_andromeda.py` | Phase 1 |
| 新建 migration | `backend/alembic/versions/20260624_add_meta_andromeda_scoring_profiles.py` | Phase 1 |
| 新建 | `backend/modules/meta_andromeda/calibration_pipeline.py` | Phase 3 |
| 修改 | `backend/modules/meta_andromeda/runtime.py` | Phase 2 |
| 修改 | `backend/modules/meta_andromeda/service.py` | Phase 4 |
| 修改 | `backend/modules/meta_andromeda/router.py` | Phase 5 |
| 修改 | `backend/modules/meta_andromeda/schemas.py` | Phase 5 |
| 修改 | `backend/modules/meta_andromeda/repository.py` | Phase 5 |
| 修改 | `backend/core/scheduler.py` | Phase 4 |
| 修改 | `frontend/src/pages/MetaAndromedaMonitoring.jsx` | Phase 5 |
| 修改 | `frontend/src/services/metaAndromedaMonitoringService.js` | Phase 5 |

---

## 驗證方式

1. `alembic upgrade head` 確認 migration 無誤，`meta_andromeda_scoring_profiles` 表存在且有 seed 資料
2. 打一筆評分請求，確認 runtime 從 DB 載入 prompt（log 中出現 cache miss → DB load → cache hit）
3. 手動呼叫 `POST /meta-andromeda/calibration/sync`（需有 >= 10 筆誤判），確認 APScheduler 排入 `ma_cal_{dataset_id}` job
4. Job 執行後，`meta_andromeda_scoring_profiles` 表出現新 `calibration_auto` profile，`bias_summary` 有內容
5. 前端監控頁出現「待審核」卡片，點 Promote 後狀態切換，下一筆評分的 prompt 包含 `calibration_guidance`

---

## 暫緩事項（未來迭代）

- **A/B shadow scoring**：對同一批素材用新舊 profile 各跑一次、比較準確率後再 auto-promote
- **自訂日期區間**：`sync_calibration_dataset` 的 `window_kind="custom"` 的 `since`/`until` 目前未傳入（repository 現有 bug）
- **Profile rollback**：promote 後目前只能手動切回，無一鍵 rollback 機制

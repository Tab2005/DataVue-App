# 15 Meta Andromeda 儲存機制與持久化掛載實作計劃

## 目的

本文件基於 Meta Andromeda Phase 5.1 匯入優化實作，規劃後端 [FastAPI](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/main.py) 在生產環境（如 Zeabur）上的「廣告素材檔案儲存機制」與「持久化掛載 (Volume Mount)」技術落地方案。

由於 `Observation` 事實層需要永久保存廣告素材檔案（以防 FB CDN 連結失效），本計劃提供兩種儲存後端的具體設定指南，確保系統在雲端環境上能穩定、安全地存取實體圖片與影片。

---

## 儲存架構現況

目前在 [storage.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/modules/meta_andromeda/storage.py) 中，定義了 [MetaAndromedaStorageAdapter](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/modules/meta_andromeda/storage.py#L14-L138)，它支援兩種儲存後端（由 `META_ANDROMEDA_STORAGE_BACKEND` 控制）：

1. **`filesystem` (本地檔案儲存，預設)**：將素材檔案寫入 [META_ANDROMEDA_STORAGE_ROOT](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/core/config.py#L116-L123) 指定的本地路徑。
2. **`s3_compatible` (S3 相容物件儲存)**：使用 `boto3` 將素材上傳至共用物件儲存桶（如 AWS S3, Cloudflare R2, MinIO 等）。

---

## 落地實作計劃

### 方案 A：Zeabur 持久化磁碟掛載 (Filesystem)

適用於單一後端實例部署，且不希望額外付費購買雲端物件儲存的場景。

#### 1. Zeabur 控制台設定步驟
* **建立儲存區**：
  * 開啟 Zeabur 後端服務（FastAPI backend）的設定頁面。
  * 前往 **「儲存 (Volumes)」** 分頁，點擊 **「新增儲存區 (Add Volume)」**。
  * 設定掛載路徑 (Mount Path) 為：`/app/backend/storage`。
* **設定環境變數**：
  * 前往 **「變數 (Variables)」** 分頁。
  * 新增環境變數，將素材存取路徑與資料庫（若使用 SQLite）指向該掛載目錄下：
    ```bash
    META_ANDROMEDA_STORAGE_BACKEND=filesystem
    META_ANDROMEDA_STORAGE_ROOT=/app/backend/storage/meta_andromeda
    ```

#### 2. SQLite 資料庫移轉（非必要，但極度推薦）
若專案使用本地 SQLite 資料庫（`facebook_dashboard.db`），為了防止重啟/重新部署時資料庫遺失，應同步修改 `.env` 中資料庫的存放路徑，將其移入 Volume 中：
```bash
DATABASE_URL=sqlite:////app/backend/storage/facebook_dashboard.db
```

---

### 方案 B：S3 相容物件儲存 (S3 Compatible)

適用於多節點水平擴充 (Scale Out) 部署，或是希望靜態素材資源透過獨立 CDN 加速的生產場景。

#### 1. 雲端儲存桶準備
* 在 AWS S3、Cloudflare R2 或其他 S3 相容平台建立一個專屬儲存桶（例如 `datavue-assets`）。
* 設定該儲存桶的 CORS 政策，允許您的前端網域（如 `https://datavue-dev-saas.sitetegy.com`）跨域存取。

#### 2. Zeabur 環境變數設定
在 Zeabur 後端服務的 **「變數 (Variables)」** 分頁中，配置以下環境變數：
```bash
META_ANDROMEDA_STORAGE_BACKEND=s3_compatible
META_ANDROMEDA_STORAGE_S3_BUCKET=datavue-assets
META_ANDROMEDA_STORAGE_S3_REGION=ap-northeast-1
META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID=YOUR_S3_ACCESS_KEY
META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY=YOUR_S3_SECRET_ACCESS_KEY
# 若使用非 AWS S3 的服務（如 R2），需設定 Endpoint URL
META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
# 設定公開存取 Base URL 供前端讀取素材圖片
META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL=https://assets.sitetegy.com/meta-andromeda
```

---

## 容錯與降級機制

若網路中斷、CDN 網址失效、磁碟空間不足或 S3 權限配置錯誤：
* 後端在 [import_observed_facebook_ad](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/modules/meta_andromeda/service.py#L314-L397) 方法中的素材處理已實作 `try-except` 容錯防禦。
* 素材儲存失敗只會記錄警告日誌 `logger.warning`，**主流程不會中斷**。
* 廣告文案與績效 Observation 數據將照常成功匯入，確保業務連續性。

---

## 驗收清單 (Verification)

- [ ] 在本地或開發伺服器上配置 Volume 掛載。
- [ ] 執行單筆/批次匯入，確認後端無 `PermissionError` 或是物件儲存上傳失敗。
- [ ] 檢查儲存目錄（本地或 S3 BUCKET），確認是否有按日期結構格式（如 `uploads/YYYY/MM/DD/asset_xxxx/`）正確產生檔案。
- [ ] 確認前端 [Analytics.jsx](file:///C:/Users/BWM2/Documents/python/DataVue-App/frontend/src/pages/Analytics.jsx) 在完成匯入後，不會拋出跨域 CORS 阻擋。

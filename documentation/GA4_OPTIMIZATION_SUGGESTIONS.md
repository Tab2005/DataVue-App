# GA4 模組資料抓取優化建議

本文檔分析了 `backend/ga4_service.py` 中 `get_analytics` 函式的現行實作，並提出關鍵優化建議，以解決當前存在的嚴重資料不完整問題。

## 核心問題分析：資料嚴重不完整

經分析，GA4 模組的 `get_analytics` 函式在實作上存在重大缺陷，將導致報表數據的嚴重失真。

1.  **完全沒有分頁機制 (No Pagination):**
    目前的程式碼在呼叫 GA4 Data API 時，只發送了單次請求，並且未設定 `limit`（限制筆數）與 `offset`（位移）參數。根據 Google API 的官方文件，在未指定 `limit` 的情況下，API **預設最多只會回傳 1,000 筆資料**。

2.  **資料截斷風險:**
    這意味著，任何資料量超過 1,000 筆的 GA4 報表查詢，目前的系統**只會抓取到前 1,000 筆資料**，其餘的所有資料都會被直接遺漏，且系統不會提示任何錯誤。這會導致使用者看到的報表數據是不完整的，從而可能做出錯誤的業務判斷。

## 優化前後行為比較 (Behavior Comparison Before and After Optimization)

### 優化前（目前行為）

目前 GA4 的 `get_analytics` 函式行為是：

1.  無論請求多少資料，單次 API 請求**最多只會獲取 1,000 筆**。
2.  程式碼中沒有分頁處理邏輯，因此**所有超出 1,000 筆的資料都會被遺漏**。
3.  使用者看到的數據會是**不完整**的，且無法從介面判斷資料是否完整。

### 優化後（建議行為）

實作完整的分頁邏輯和提高批次大小後，GA4 的 `get_analytics` 函式行為將會是：

1.  系統會以 **100,000 筆**為一個批次持續發送 API 請求。
2.  透過 `offset` 參數，程式會**自動獲取所有分頁的資料**。
3.  只有當 API 回傳的資料筆數小於 100,000 筆時，才會停止抓取，確保**所有資料都已被完整獲取**。
4.  使用者將能看到**完整且準確**的 GA4 報表數據。

---

## 優化建議

為了確保資料的完整性與查詢效率，強烈建議對 `ga4_service.py` 進行以下修改。

### 1. 實作完整的分頁查詢邏輯

這是最高優先級的修改，以確保能獲取所有資料。應採用 `while` 迴圈搭配 `limit` 和 `offset` 參數來抓取所有分頁的資料。

**建議作法：**

```python
# 建議的迴圈邏輯
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
import json # 需要用於快取鍵的序列化

# ...

try:
    data_client = BetaAnalyticsDataClient(credentials=creds)
    all_rows = []
    offset = 0
    limit = 100000  # 使用 API 允許的最大值以提升效率

    while True:
        # 建立每次請求的 request object
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name=dim) for dim in dimensions],
            metrics=[Metric(name=met) for met in metrics],
            limit=limit,
            offset=offset
        )

        # 執行請求
        response = data_client.run_report(request)
        
        current_rows = response.rows
        if not current_rows:
            break # 如果沒有回傳資料，結束迴圈

        all_rows.extend(current_rows)

        # 如果回傳的筆數小於請求的 limit，代表這是最後一頁
        if len(current_rows) < limit:
            break

        offset += limit # 更新 offset 準備下一次請求

    # ... 後續處理 all_rows ...

except Exception as e:
    # ... 錯誤處理 ...

```

### 2. 整合快取機制 (Caching)

### 為什麼目前沒有快取機制？

這在軟體開發中是一個常見的現象，原因可能包括：

1.  **優先核心功能：** 在功能開發初期，重點往往是讓功能能夠正確運作，效能優化和快取通常會被排在後期。
2.  **開發資源與時程：** 可能受限於開發時間或資源，快取被視為是「好處，但非必要」的功能，留待未來實作。
3.  **不同模組的整合時機：** 雖然專案中存在 `backend/cache.py`，但它可能是在 GA4 模組開發之後才引入或完善的，導致 GA4 模組尚未整合進這個新的快取系統中。
4.  **初期數據量小：** 在資料量不大、請求頻率不高時，可能尚未顯現出快取的需求。

### 如何設置快取機制？

專案中的 `backend/cache.py` 已經提供了一個基於 `cachetools.TTLCache` 的記憶體快取系統，包含產生快取鍵、讀取和寫入快取的輔助函式。這使得整合快取變得非常簡便。

**實作步驟：**

1.  **引入快取函式：** 在 `ga4_service.py` 檔案中，從 `cache` 模組引入所需的函式。
    ```python
    from cache import generate_cache_key, get_cached, set_cached, analytics_cache
    import json # 用於序列化複雜參數作為快取鍵
    ```

2.  **產生快取鍵：** 在 `get_analytics` 函式一開始，根據所有查詢參數（`property_id`, `start_date`, `end_date`, `metrics`, `dimensions` 等）產生一個唯一的快取鍵。對於列表或字典型別的參數，建議使用 `json.dumps()` 進行序列化，以確保快取鍵的一致性。
    ```python
    cache_key = generate_cache_key(
        "ga4_analytics", # 可識別服務的前綴
        property_id,
        start_date,
        end_date,
        json.dumps(metrics, sort_keys=True), # 序列化 metrics 列表
        json.dumps(dimensions, sort_keys=True) # 序列化 dimensions 列表
    )
    ```

3.  **檢查快取：** 在向 Google API 發送請求之前，先嘗試從 `analytics_cache` 中讀取資料。
    ```python
    cached_data = get_cached(analytics_cache, cache_key)
    if cached_data is not None:
        print("[GA4] Returning data from cache.")
        return cached_data, None # 如果找到快取資料，直接回傳
    ```

4.  **寫入快取：** 在成功從 GA4 API 獲取所有分頁資料，並將其處理成最終的 `result` 格式後，再將這個結果存入快取中。
    ```python
    # ... (此處為您實作的分頁迴圈，將所有資料存入 final_result_object 中) ...

    print("[GA4] Storing data in cache.")
    set_cached(analytics_cache, cache_key, final_result_object) # 將完整的結果存入快取
    return final_result_object, None
    ```
    `analytics_cache` 預設的 TTL (Time To Live) 為 120 秒 (2 分鐘)，這表示資料會在快取中保留 2 分鐘，之後會自動失效。

## 總結

GA4 模組目前的實作存在嚴重的資料不完整風險，這是**亟待修復的 Bug**。實作**完整的分頁邏輯**是首要任務。完成分頁後，再搭配**快取機制**，才能確保此模組的穩定、高效與數據準確。
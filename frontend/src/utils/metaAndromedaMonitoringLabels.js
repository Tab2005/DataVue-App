const MONITORING_LABELS = {
    queued_total: ['Queued Total', '累計佇列數'],
    completed_total: ['Completed Total', '累計完成數'],
    failure_total: ['Failure Total', '累計失敗數'],
    'score-request': ['Prediction / ScoreEvent Queue', 'Prediction / ScoreEvent 佇列'],
    observed_total: ['Observed Imported (Cumulative)', '已匯入 Observation（累積）'],
    latest_observed_total: ['Observed in Latest Drift Window', '最近 Drift 區間 Observation'],
    observed_with_asset: ['Observed With Asset', '已有素材 Observation'],
    latest_matched_total: ['Matched to Completed Score', '成功配對 Completed Score'],
    latest_match_rate: ['Latest Match Rate', '最近配對率'],
    latest_calibration_candidate_total: ['Calibration Candidates', '可校準偏差樣本'],
    latest_calibration_synced_total: ['Calibration Synced', '已同步校準資料'],
    latest_calibration_status: ['Calibration Status', '校準資料狀態'],
    'queue_depth.current': ['Current Queue Depth', '當前佇列深度'],
    'queue_depth.peak': ['Peak Queue Depth', '佇列深度峰值'],
    'latency.avg(ms)': ['Avg Latency (ms)', '平均延遲 (ms)'],
    'latency.p95(ms)': ['P95 Latency (ms)', 'P95 延遲 (ms)'],
    'latency.max(ms)': ['Max Latency (ms)', '最大延遲 (ms)'],
    database_queue: ['Database Queue', '資料庫排程佇列'],
    redis_stream: ['Redis Stream', 'Redis 串流佇列'],
    apscheduler: ['APScheduler', '背景排程器'],
    processing_started: ['Processing Started', '已啟動處理'],
    completed: ['Completed', '處理完成'],
    failed: ['Failed', '處理失敗'],
    queued: ['Queued', '已入佇列'],
    dead_letter: ['Dead Letter', '異常任務 (已隔離)'],
    drifted: ['Drifted', '嚴重預估偏差'],
    warning: ['Warning', '警告'],
    stable: ['Stable', '穩定'],
    last_24h: ['Last 24 Hours', '最近 24 小時'],
    last_7d: ['Last 7 Days', '最近 7 天'],
    last_30d: ['Last 30 Days', '最近 30 天'],
    lifetime: ['Lifetime', '累積歷史成效'],
    custom: ['Custom Range', '自訂時間區間'],
    high: ['High', '高 (High)'],
    mid: ['Mid', '中 (Mid)'],
    low: ['Low', '低 (Low)'],
    score_request_received: ['Score Request Received', '收到評分請求'],
    dataset_calibration: ['Dataset Calibration', '資料集校準'],
    drift_diagnostics: ['Drift Diagnostics', '偏差診斷'],
    prediction_inference: ['Prediction Inference', '預測推論'],
    model_sync: ['Model Sync', '模型同步'],
    info: ['Info', '資訊'],
    error: ['Error', '錯誤'],
    critical: ['Critical', '嚴重'],
    shared_queue_host_adapter: ['Shared Queue Host Adapter', '共用佇列適配器'],
    not_started: ['Not Started', '尚未開始'],
    queued_for_calibration: ['Queued for Calibration', '已排入校準'],
    no_data_to_sync: ['No Data to Sync', '沒有可同步資料'],
};

export const getMonitoringText = (language) => (en, zh) => (language === 'en' ? en : zh);

export const getMonitoringTranslation = (key, language) => {
    if (!key) return '--';
    const label = MONITORING_LABELS[String(key).toLowerCase()];
    if (!label) return key;
    return language === 'en' ? label[0] : label[1];
};

export const formatMonitoringDateTime = (isoString) => {
    if (!isoString) return '--';
    try {
        let dateStr = isoString;
        if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
            dateStr = dateStr.includes('T') ? `${dateStr}Z` : dateStr;
        }
        const date = new Date(dateStr);
        if (Number.isNaN(date.getTime())) return isoString;

        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        const hh = String(date.getHours()).padStart(2, '0');
        const mm = String(date.getMinutes()).padStart(2, '0');
        const ss = String(date.getSeconds()).padStart(2, '0');

        return `${y}-${m}-${d} ${hh}:${mm}:${ss}`;
    } catch {
        return isoString;
    }
};
const matchesMonitoringQuery = (item, query, keys) => {
    if (!query) return true;
    return keys.some((key) => item[key]?.toLowerCase().includes(query));
};

export const filterMonitoringRecentEvents = (events = [], hostFilter, eventQuery) => {
    const query = eventQuery.trim().toLowerCase();
    return events.filter((event) => {
        const hostOk = hostFilter === 'all' || event.queue_host === hostFilter;
        return hostOk && matchesMonitoringQuery(event, query, [
            'event_type',
            'queue_host',
            'score_event_id',
            'runtime_job_id',
            'message',
        ]);
    });
};

export const filterMonitoringDeadLetters = (deadLetters = [], hostFilter, eventQuery) => {
    const query = eventQuery.trim().toLowerCase();
    return deadLetters.filter((item) => {
        const hostOk = hostFilter === 'all' || item.queue_host === hostFilter;
        return hostOk && matchesMonitoringQuery(item, query, [
            'failure_stage',
            'queue_host',
            'score_event_id',
            'runtime_job_id',
            'final_error_message',
        ]);
    });
};

export const getCleanupStaleConfirmMessage = (language) => language === 'zh'
    ? '確定要清除所有超過 30 分鐘仍卡在 queued / processing 的評分任務？\n\n此操作會將這些任務標記為 failed，不可回復。'
    : 'Clear all score events stuck in queued/processing for more than 30 minutes?\n\nThey will be marked as failed. This cannot be undone.';

export const getForcePromoteConfirmMessage = (language) => language === 'zh'
    ? '這個候選版本的回測結果未通過門檻（並未確定優於目前正式版）。仍要強制套用嗎？'
    : 'This candidate did not pass the backtest gate (not confirmed better than production). Force promote anyway?';

export const getPromoteProfileConfirmMessage = (profileName, language) => language === 'zh'
    ? `確定要將 "${profileName}" 設為生效中的 Scoring Profile？\n目前生效的 profile 會被取消。`
    : `Promote "${profileName}" as the active Scoring Profile?\nThe current active profile will be deactivated.`;

export const getHoldoutBacktestRequiredMessage = (language) => language === 'zh'
    ? '套用被擋下：尚未執行 holdout 回測。請先點「執行回測」按鈕。'
    : 'Promote blocked: holdout backtest has not run yet. Click "Run Backtest" first.';

export const getCalibrationSyncSuccessMessage = (result, language) => language === 'zh'
    ? `校準資料集建立成功！ID: ${result.dataset_id}，共 ${result.synced_count} 筆偏移素材。`
    : `Dataset created successfully! ID: ${result.dataset_id}, synced ${result.synced_count} ads.`;
export const buildMonitoringSearchParams = ({
    hostFilter,
    eventQuery,
    deadLetterOnly,
    selectedScoreEventId,
    driftWindowKind,
    driftSince,
    driftUntil,
}) => {
    const nextParams = new URLSearchParams();
    if (hostFilter && hostFilter !== 'all') nextParams.set('host', hostFilter);
    if (eventQuery.trim()) nextParams.set('q', eventQuery.trim());
    if (deadLetterOnly) nextParams.set('dead', '1');
    if (selectedScoreEventId) nextParams.set('event', selectedScoreEventId);
    if (driftWindowKind !== 'last_24h') nextParams.set('window', driftWindowKind);
    if (driftWindowKind === 'custom') {
        if (driftSince) nextParams.set('since', driftSince);
        if (driftUntil) nextParams.set('until', driftUntil);
    }
    return nextParams;
};

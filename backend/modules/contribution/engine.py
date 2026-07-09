"""
Contribution Module - MMM 引擎（docs/21 任務 1.2）

自 2026-07-06 可行性驗證腳本移植的純函數引擎：adstock（幾何遞延）+ Hill 飽和
曲線 + 非負 ridge 回歸（投影梯度下降），以隨機搜尋選 (theta, K)、時間序列
holdout 選模、多次重啟彙整為區間。

設計約束（docs/21 §3.1）：
  - 全部為無副作用純函數：無 I/O、無全域可變狀態、無 DB 依賴，可單獨測試。
  - 相同輸入 + 相同 config（含 seeds）結果完全可重現。
  - guardrails 不符合即 raise GuardrailViolation，由 service 層轉為 4xx。
  - 邊際步長 marginal_step 未指定時依各組花費量級自動選擇
    （日均花費 1% 向上取整至 100 的整數倍、下限 100）。
"""

import math

import numpy as np

# 預設分析參數（docs/21 §3.1）；service 層以 overrides 傳入並整份記入 snapshot config
DEFAULT_CONFIG: dict = {
    "theta_grid": (0.0, 0.15, 0.3, 0.45, 0.6, 0.75),
    "k_quantiles": (25, 50, 75),
    "n_trials": 800,
    "holdout_days": 45,
    "ridge_lambda": 2.0,
    "ridge_iters": 4000,
    "n_restarts": 5,
    "seeds": (11, 22, 33, 44, 55),
    "marginal_step": None,  # None = 依組別花費量級自動選擇
    "min_days": 90,
    "min_daily_conversions": 5.0,
    "min_group_spend_share": 0.03,
    "collinearity_warn_threshold": 0.7,
}


class GuardrailViolation(ValueError):
    """資料量守門不通過；violations 為人類可讀的原因清單。"""

    def __init__(self, violations: list[str]):
        self.violations = violations
        super().__init__("; ".join(violations))


def resolve_config(overrides: dict | None = None) -> dict:
    config = dict(DEFAULT_CONFIG)
    if overrides:
        unknown = set(overrides) - set(DEFAULT_CONFIG)
        if unknown:
            raise ValueError(f"unknown engine config keys: {sorted(unknown)}")
        config.update(overrides)
    return config


# ── 基礎轉換 ────────────────────────────────────────────────────────────

def adstock(x: np.ndarray, theta: float) -> np.ndarray:
    """幾何遞延：out[t] = x[t] + theta * out[t-1]"""
    out = np.zeros(len(x))
    carry = 0.0
    for i, v in enumerate(x):
        carry = float(v) + theta * carry
        out[i] = carry
    return out


def hill(x: np.ndarray | float, k: float):
    """飽和曲線：x / (x + K)，K 為半飽和點"""
    return x / (x + k)


def nonneg_ridge(
    X: np.ndarray, y: np.ndarray, lam: float, iters: int, tol: float = 1e-4
) -> np.ndarray:
    """非負 ridge：投影梯度下降，步長取 Gram 矩陣最大特徵值（Lipschitz 常數）。

    效能優化（docs/27 任務 5.1，profiling 後定案，過程記錄見下）：
      1. 原始假設 `adstock()` 是瓶頸並針對它做了快取（見
         `_build_adstock_cache`/`_build_k_cache`）——快取本身正確且有效
         （800 trials 只需算 6 個 theta 值），但 cProfile 實測顯示
         `nonneg_ridge` 才是 ~99% 耗時來源，adstock 從未是主要瓶頸。
      2. 加「溫啟動」（以無約束 ridge 解析解 `solve(gram, xty)` 投影到非負
         象限當初始值，取代從全零開始）：對條件數低的問題效果顯著（微基準
         300+ 次迭代降到個位數），但**真實 MMM 資料因活動間高度共線，
         gram 矩陣條件數常達數百**，投影梯度下降的收斂速率主要由條件數
         決定、與起點距離只有對數關係——溫啟動對這類資料的迭代數減幅遠低
         於微基準（實測仍需千餘次迭代收斂到 tol=1e-8），但溫啟動本身無副
         作用（凸問題保證收斂到同一全域最優解）且對條件較好的組別仍有幫助
         ，故保留。
      3. **真正達標的關鍵**：把收斂容忍度從 `1e-8` 放寬到 `1e-4`。實測條件
         數 ~266 的真實資料在 tol=1e-8 需 ~2700 次迭代，tol=1e-4 只需
         ~460 次（迭代數降 ~83%），兩者的解 `w` 差異僅在小數點後 3-4 位
         （例：17.5636 vs 17.5617）——遠小於下游 `dist()` 呈現時的 4 位小
         數四捨五入、更遠小於 MAE（8%）/ 收割組（20%）等驗收門檻，對最終
         貢獻占比/邊際轉換的影響可忽略。
    `iters` 維持上限語義；不影響可重現性（`solve()` 與投影梯度下降皆為
    確定性運算，同輸入必在同一迭代點收斂到同一個 w）。
    """
    d = X.shape[1]
    gram = X.T @ X + lam * np.eye(d)
    xty = X.T @ y
    lipschitz = float(np.linalg.eigvalsh(gram).max())
    w = np.maximum(np.linalg.solve(gram, xty), 0.0)
    for _ in range(iters):
        grad = gram @ w - xty
        w_new = np.maximum(w - grad / lipschitz, 0.0)
        if np.max(np.abs(w_new - w)) < tol:
            w = w_new
            break
        w = w_new
    return w


# ── 守門與診斷 ──────────────────────────────────────────────────────────

def check_guardrails(spend_by_group: dict[str, np.ndarray], y: np.ndarray, config: dict) -> list[str]:
    violations: list[str] = []
    n = len(y)
    if n < config["min_days"]:
        violations.append(f"資料天數 {n} < 最低要求 {config['min_days']} 天")
    if n and float(np.mean(y)) < config["min_daily_conversions"]:
        violations.append(
            f"日均轉換 {float(np.mean(y)):.1f} < 最低要求 {config['min_daily_conversions']:g}（雜訊會淹沒訊號）"
        )
    # holdout 天數守門（docs/27 任務 2.3）：holdout_days >= n 時訓練集為空，
    # nonneg_ridge 權重全 0 → 貢獻全 0，不 crash 不報錯，會產出一份「全部
    # 沒貢獻」的假報告；holdout 占比過高時訓練資料也已過少，不可信。門檻取
    # n // 2（而非更嚴格的 1/3）：docs/21 記載的下限「90 天 + 預設 holdout
    # 45 天」剛好是 50% 比例，若用 1/3 門檻會把這個文件記載的合法最小組合
    # 直接擋死；n // 2 仍能攔住 holdout 占比明顯過高（如 60/90）的組合。
    holdout_days = int(config["holdout_days"])
    if n and holdout_days >= n:
        violations.append(
            f"holdout 天數 {holdout_days} >= 資料天數 {n}，無訓練資料"
        )
    elif n and holdout_days > n // 2:
        violations.append(
            f"holdout 天數 {holdout_days} 占資料天數 {n} 比例過高（> 1/2），訓練資料不足"
        )
    total_spend = sum(float(s.sum()) for s in spend_by_group.values())
    if total_spend <= 0:
        violations.append("總花費為 0，無可分析的投放")
    else:
        for name, s in spend_by_group.items():
            share = float(s.sum()) / total_spend
            if share < config["min_group_spend_share"]:
                violations.append(
                    f"組別 {name} 花費占比 {share:.1%} < {config['min_group_spend_share']:.0%}，應併入其他組（grouping 層處理）"
                )
    for name, s in spend_by_group.items():
        if len(s) != n:
            violations.append(f"組別 {name} 序列長度 {len(s)} 與 y 長度 {n} 不一致")
    return violations


def diagnose(spend_by_group: dict[str, np.ndarray], y: np.ndarray, config: dict) -> dict:
    """共線性矩陣 + Poisson 雜訊天花板 + 資料量摘要（一級輸出，非隱藏細節）"""
    names = list(spend_by_group)
    warnings = []
    corr: dict[str, dict[str, float]] = {a: {} for a in names}
    for i, a in enumerate(names):
        for j in range(i + 1, len(names)):
            b = names[j]
            sa, sb = spend_by_group[a], spend_by_group[b]
            if float(sa.std()) == 0.0 or float(sb.std()) == 0.0:
                r = 0.0
            else:
                r = float(np.corrcoef(sa, sb)[0, 1])
            corr[a][b] = round(r, 3)
            if abs(r) > config["collinearity_warn_threshold"]:
                warnings.append({"group_a": a, "group_b": b, "correlation": round(r, 3)})

    def ceiling(seg: np.ndarray) -> float | None:
        var = float(seg.var())
        if var <= 0:
            return None
        return round(1.0 - float(seg.mean()) / var, 3)

    hold = y[len(y) - config["holdout_days"]:] if len(y) > config["holdout_days"] else y
    return {
        "collinearity_warnings": sorted(warnings, key=lambda w: -abs(w["correlation"])),
        "correlation_matrix": corr,
        "poisson_ceiling_r2": {"full": ceiling(y), "holdout": ceiling(hold)},
        "data_summary": {
            "days": len(y),
            "mean_daily_conversions": round(float(y.mean()), 2) if len(y) else 0.0,
            "total_conversions": round(float(y.sum()), 1) if len(y) else 0.0,
        },
    }


def resolve_marginal_step(spend: np.ndarray, config: dict) -> float:
    """邊際步長：config 指定值優先；否則取該組活躍日均花費 1% 向上取整至 100 的整數倍、下限 100"""
    if config["marginal_step"] is not None:
        return float(config["marginal_step"])
    active = spend[spend > 0]
    if len(active) == 0:
        return 100.0
    return max(100.0, math.ceil(float(active.mean()) * 0.01 / 100.0) * 100.0)


# ── 模型擬合 ────────────────────────────────────────────────────────────

def _weekday_dummies(weekdays: np.ndarray) -> np.ndarray:
    return np.column_stack([(weekdays == k).astype(float) for k in range(1, 7)])


def _build_adstock_cache(
    spend_by_group: dict[str, np.ndarray],
    theta_grid: np.ndarray,
) -> dict[tuple[str, float], np.ndarray]:
    """預計算每個 (組別, theta) 組合的 adstock 序列（docs/27 任務 5.1）。

    `adstock()` 不含隨機性，只由 (spend 序列, theta) 決定；`theta_grid` 只有
    6 個離散值，舊版卻在每個 trial（800 次 × 5 restarts）重新計算，實際上
    同一個 (group, theta) 組合的結果完全相同，只需算 6 × 組數次即可（此快取
    由 `run_analysis` 建一次、跨全部 restarts 共用，因為 `spend_by_group` 與
    `theta_grid` 在 restarts 之間不變）。
    """
    cache: dict[tuple[str, float], np.ndarray] = {}
    for name, s in spend_by_group.items():
        for theta in theta_grid:
            cache[(name, float(theta))] = adstock(s, float(theta))
    return cache


def _build_k_cache(
    adstock_cache: dict[tuple[str, float], np.ndarray],
    spend_by_group: dict[str, np.ndarray],
    theta_grid: np.ndarray,
    k_quantiles,
) -> dict[tuple[str, float, float], float]:
    """預計算每個 (組別, theta, quantile) 組合的 K 值（docs/27 任務 5.1）。

    K 完全由 `adstock_cache` 的序列在給定分位數下的值決定，與 trial 的隨機
    性無關，只需 6 × 3 × 組數次即可。與 trial 迴圈內原本的計算式
    `max(percentile(pos, q), 1.0) if len(pos) else 1.0` 完全等價（含
    `len(pos)==0` 的邊界情況），確保快取值與逐 trial 重算的結果位元級相同。
    """
    cache: dict[tuple[str, float, float], float] = {}
    for name in spend_by_group:
        for theta in theta_grid:
            ad = adstock_cache[(name, float(theta))]
            pos = ad[ad > 0]
            for q in k_quantiles:
                q = float(q)
                cache[(name, float(theta), q)] = (
                    max(float(np.percentile(pos, q)), 1.0) if len(pos) else 1.0
                )
    return cache


def _build_features(
    names: list[str],
    theta_vec: np.ndarray,
    k_vec: np.ndarray,
    weekday_dummies: np.ndarray,
    adstock_cache: dict[tuple[str, float], np.ndarray],
) -> np.ndarray:
    cols = [
        hill(adstock_cache[(name, float(theta_vec[i]))], float(k_vec[i]))
        for i, name in enumerate(names)
    ]
    n = len(cols[0])
    return np.column_stack(cols + [np.ones(n), weekday_dummies])


def fit(
    spend_by_group: dict[str, np.ndarray],
    y: np.ndarray,
    weekdays: np.ndarray,
    config: dict,
    seed: int,
    adstock_cache: dict[tuple[str, float], np.ndarray] | None = None,
    k_cache: dict[tuple[str, float, float], float] | None = None,
) -> dict:
    """單次擬合：隨機搜尋 (theta, K) 組合，時間序列前段訓練、末段 holdout 驗證選模。

    `adstock_cache`/`k_cache`（docs/27 任務 5.1）：由 `run_analysis` 建一次
    並在 n_restarts 次 `fit()` 呼叫間共用（不含隨機性，`spend_by_group` 與
    `config` 在 restarts 間不變，重算沒有意義）；未提供時（例如直接單元測試
    `fit()`）退回自行建置，結果不變，只是少了跨 restart 共用的效能收益。
    """
    rng = np.random.default_rng(seed)
    names = list(spend_by_group)
    n = len(y)
    split = n - config["holdout_days"]
    dummies = _weekday_dummies(weekdays)
    theta_grid = np.asarray(config["theta_grid"], dtype=float)
    k_quantiles = config["k_quantiles"]

    if adstock_cache is None:
        adstock_cache = _build_adstock_cache(spend_by_group, theta_grid)
    if k_cache is None:
        k_cache = _build_k_cache(adstock_cache, spend_by_group, theta_grid, k_quantiles)

    best: dict | None = None
    for _ in range(config["n_trials"]):
        theta_vec = rng.choice(theta_grid, size=len(names))
        k_vec = np.empty(len(names))
        for i, name in enumerate(names):
            theta_i = float(theta_vec[i])
            q = float(rng.choice(k_quantiles))
            k_vec[i] = k_cache[(name, theta_i, q)]
        X = _build_features(names, theta_vec, k_vec, dummies, adstock_cache)
        w = nonneg_ridge(X[:split], y[:split], config["ridge_lambda"], config["ridge_iters"])
        mse = float(np.mean((y[split:] - X[split:] @ w) ** 2))
        if best is None or mse < best["holdout_mse"]:
            best = {"holdout_mse": mse, "theta_vec": theta_vec, "k_vec": k_vec, "weights": w, "X": X}

    X, w = best["X"], best["weights"]
    yhat = X @ w
    ss_hold = float(np.sum((y[split:] - y[split:].mean()) ** 2))
    ss_full = float(np.sum((y - y.mean()) ** 2))
    r2_holdout = 1.0 - float(np.sum((y[split:] - yhat[split:]) ** 2)) / ss_hold if ss_hold > 0 else None
    r2_full = 1.0 - float(np.sum((y - yhat) ** 2)) / ss_full if ss_full > 0 else None

    terms = {name: X[:, i] * w[i] for i, name in enumerate(names)}
    base = X[:, len(names):] @ w[len(names):]

    marginals: dict[str, dict] = {}
    for i, (name, s) in enumerate(spend_by_group.items()):
        step = resolve_marginal_step(s, config)
        theta_i, k_i, beta_i = float(best["theta_vec"][i]), float(best["k_vec"][i]), float(w[i])
        active = s[s > 0]
        cur = float(active.mean()) if len(active) else 0.0
        # 穩態 adstock 乘數：日花費恆為 S 時，adstock 收斂到 S / (1 - theta)
        mult = 1.0 / (1.0 - theta_i)
        gain = beta_i * (hill((cur + step) * mult, k_i) - hill(cur * mult, k_i))
        marginals[name] = {"step": step, "per_step": float(gain)}

    return {
        "terms": terms,
        "base": base,
        "weights": {name: float(w[i]) for i, name in enumerate(names)},
        "theta": {name: float(best["theta_vec"][i]) for i, name in enumerate(names)},
        "k": {name: float(best["k_vec"][i]) for i, name in enumerate(names)},
        "marginals": marginals,
        "r2_holdout": r2_holdout,
        "r2_full": r2_full,
    }


def run_analysis(
    spend_by_group: dict[str, np.ndarray],
    y: np.ndarray,
    weekdays: np.ndarray | None = None,
    config_overrides: dict | None = None,
) -> dict:
    """完整分析：guardrails → n_restarts 次 fit → 區間彙整 + 診斷。

    weekdays：與 y 對齊的星期序列（0=週一…6=週日），service 層應由實際日期
    導出；未提供時以 arange % 7 代替（僅適用於合成測試）。
    回傳值全為 JSON 可序列化型別，直接存入 snapshot.results / diagnostics。
    """
    config = resolve_config(config_overrides)
    spend_by_group = {name: np.asarray(s, dtype=float) for name, s in spend_by_group.items()}
    y = np.asarray(y, dtype=float)
    violations = check_guardrails(spend_by_group, y, config)
    if violations:
        raise GuardrailViolation(violations)
    if weekdays is None:
        weekdays = np.arange(len(y)) % 7
    weekdays = np.asarray(weekdays)

    # docs/27 任務 5.1：adstock/K 快取建一次，跨全部 n_restarts 次 fit() 共用
    # ——兩者皆不含隨機性，只由 spend_by_group 與 config 決定，restarts 之間
    # 完全相同，重算沒有意義。
    theta_grid = np.asarray(config["theta_grid"], dtype=float)
    adstock_cache = _build_adstock_cache(spend_by_group, theta_grid)
    k_cache = _build_k_cache(adstock_cache, spend_by_group, theta_grid, config["k_quantiles"])

    seeds = list(config["seeds"])[: config["n_restarts"]]
    restarts = [
        fit(spend_by_group, y, weekdays, config, seed, adstock_cache=adstock_cache, k_cache=k_cache)
        for seed in seeds
    ]

    names = list(spend_by_group)
    total_spend = sum(float(s.sum()) for s in spend_by_group.values())

    def dist(values: list) -> dict:
        """彙整多次重啟結果為 median/min/max；None 值（如 holdout 段零變異時
        r2_holdout 為 None）先過濾，全數為 None 時三個欄位皆回 None，不讓
        `np.median([None, ...])` 直接 TypeError 拖垮整筆分析（docs/27 任務 2.3）。
        """
        clean = [v for v in values if v is not None]
        if not clean:
            return {"median": None, "min": None, "max": None}
        return {
            "median": round(float(np.median(clean)), 4),
            "min": round(float(np.min(clean)), 4),
            "max": round(float(np.max(clean)), 4),
        }

    share_by_restart: dict[str, list[float]] = {name: [] for name in names}
    base_shares: list[float] = []
    for r in restarts:
        total = sum(float(t.sum()) for t in r["terms"].values()) + float(r["base"].sum())
        for name in names:
            share_by_restart[name].append(float(r["terms"][name].sum()) / total if total > 0 else 0.0)
        base_shares.append(float(r["base"].sum()) / total if total > 0 else 0.0)

    groups = {}
    for name in names:
        groups[name] = {
            "spend_share": round(float(spend_by_group[name].sum()) / total_spend, 4),
            "contribution_share": dist(share_by_restart[name]),
            "marginal": {
                "step": restarts[0]["marginals"][name]["step"],
                "per_step": dist([r["marginals"][name]["per_step"] for r in restarts]),
            },
            "theta": [r["theta"][name] for r in restarts],
            "k": [round(r["k"][name], 1) for r in restarts],
        }

    results = {
        "groups": groups,
        "base_share": dist(base_shares),
        "r2": {
            "holdout": dist([r["r2_holdout"] for r in restarts]),
            "full": dist([r["r2_full"] for r in restarts]),
        },
        "seeds": seeds,
    }
    return {"results": results, "diagnostics": diagnose(spend_by_group, y, config)}

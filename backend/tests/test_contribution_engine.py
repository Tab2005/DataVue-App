"""
Contribution MMM 引擎任務 1.2 驗收測試（docs/21）

驗收標準：
  1. 合成資料（已知真實貢獻）迴歸測試：多資料集平均貢獻 MAE < 8%；
     收割組（真實 ~9%、自報 ~41%）的 MMM 估計 < 20%（平均）
  2. 重啟間貢獻中位數穩定（單一資料集內極差受控）
  3. guardrails 各拒絕條件觸發正確
  4. diagnose 共線性 / Poisson 天花板計算正確
  5. 引擎無 I/O、無全域狀態：同輸入同 config 結果完全可重現

合成資料產生器移植自 2026-07-06 可行性驗證腳本（mmm_synthetic_validation.py），
即「已知真實貢獻的合成資料就是引擎的迴歸測試」（docs/21 任務 1.2 實作步驟 2）。
"""

import numpy as np
import pytest

from modules.contribution import engine
from modules.contribution.engine import (
    GuardrailViolation,
    adstock,
    check_guardrails,
    diagnose,
    hill,
    nonneg_ridge,
    resolve_config,
    resolve_marginal_step,
    run_analysis,
)

# ── 合成資料產生器（已知真實貢獻） ──────────────────────────────────────

N_DAYS = 180
CHANNELS = ["P1_prospecting", "P2_lookalike", "RT_retargeting", "BR_branding"]

# 真實參數（引擎不知道，用來事後對答案）；RT 為「真實增量低、自報功勞高」的收割組
TRUE = {
    "P1_prospecting": dict(theta=0.30, k=2500.0, beta=55.0),
    "P2_lookalike": dict(theta=0.20, k=2000.0, beta=32.0),
    "RT_retargeting": dict(theta=0.10, k=800.0, beta=10.0),
    "BR_branding": dict(theta=0.60, k=3000.0, beta=18.0),
}
BASE_CONV = 12.0
WEEKEND_LIFT = 1.18
REPORT_BIAS = {"P1_prospecting": 0.55, "P2_lookalike": 0.65, "RT_retargeting": 3.8, "BR_branding": 0.35}

# 測試用降載參數：可行性驗證顯示 400 trials 已收斂，測試用 250 + 放寬斷言門檻
TEST_CONFIG = {
    "n_trials": 250,
    "ridge_iters": 2500,
    "n_restarts": 3,
    "seeds": (11, 22, 33),
}


def _gen_spend(rng):
    spend = {}
    levels = {"P1_prospecting": 3000, "P2_lookalike": 2200, "RT_retargeting": 1200, "BR_branding": 1500}
    for ch, lv in levels.items():
        walk = np.cumsum(rng.normal(0, 0.04, N_DAYS))
        series = lv * np.exp(walk - walk.mean())
        for _ in range(rng.integers(2, 4)):
            s = rng.integers(10, N_DAYS - 20)
            series[s:] *= rng.choice([0.6, 0.75, 1.4, 1.7])
        if rng.random() < 0.7:
            s = rng.integers(20, N_DAYS - 10)
            series[s : s + rng.integers(3, 8)] = 0.0
        spend[ch] = np.maximum(series, 0.0)
    return spend


def gen_dataset(seed):
    """回傳 (spend_by_group, y, true_shares, weekdays)；true_shares 為媒體組間占比（不含基線）"""
    rng = np.random.default_rng(seed)
    spend = _gen_spend(rng)
    weekdays = np.arange(N_DAYS) % 7
    season = np.where((weekdays == 5) | (weekdays == 6), WEEKEND_LIFT, 1.0)
    true_terms = {}
    total = np.full(N_DAYS, BASE_CONV)
    for ch, p in TRUE.items():
        term = p["beta"] * hill(adstock(spend[ch], p["theta"]), p["k"])
        true_terms[ch] = term
        total = total + term
    y = rng.poisson(np.maximum(total * season, 0.1)).astype(float)
    media_total = sum(t.sum() for t in true_terms.values())
    true_shares = {ch: float(t.sum() / media_total) for ch, t in true_terms.items()}
    return spend, y, true_shares, weekdays


def _media_shares(results: dict) -> dict[str, float]:
    """把引擎輸出的貢獻占比（含基線）重正規化為媒體組間占比，與 true_shares 同口徑"""
    med = {g: results["groups"][g]["contribution_share"]["median"] for g in results["groups"]}
    total = sum(med.values())
    return {g: (v / total if total > 0 else 0.0) for g, v in med.items()}


# ── 1. 合成資料迴歸測試（核心驗收） ────────────────────────────────────

@pytest.fixture(scope="module")
def synthetic_runs():
    runs = []
    for seed in [1, 2, 3]:
        spend, y, true_shares, weekdays = gen_dataset(seed)
        out = run_analysis(spend, y, weekdays=weekdays, config_overrides=TEST_CONFIG)
        runs.append((true_shares, out))
    return runs


def test_synthetic_contribution_mae(synthetic_runs):
    """多資料集平均貢獻 MAE < 8%（可行性驗證實測 5.4%，留 buffer）"""
    errors = []
    for true_shares, out in synthetic_runs:
        est = _media_shares(out["results"])
        errors.extend(abs(est[ch] - true_shares[ch]) for ch in CHANNELS)
    assert float(np.mean(errors)) < 0.08, f"MAE {np.mean(errors):.3f} 超過 8%"


def test_synthetic_harvest_group_corrected(synthetic_runs):
    """收割組 RT：自報 ~41%、真實 ~9%，MMM 估計（跨資料集平均）必須 < 20%"""
    ests, trues = [], []
    for true_shares, out in synthetic_runs:
        ests.append(_media_shares(out["results"])["RT_retargeting"])
        trues.append(true_shares["RT_retargeting"])
    reported = np.mean([t * REPORT_BIAS["RT_retargeting"] for t in trues])
    assert reported > 0.25, "測試前提：自報偏差應顯著（>25%）"
    assert float(np.mean(ests)) < 0.20, f"收割組估計 {np.mean(ests):.1%} 未被糾正"


def test_synthetic_restart_stability(synthetic_runs):
    """重啟間貢獻極差受控：單組 min-max 差 < 20pp、全體平均 < 10pp"""
    spreads = []
    for _, out in synthetic_runs:
        for g in out["results"]["groups"].values():
            spreads.append(g["contribution_share"]["max"] - g["contribution_share"]["min"])
    assert max(spreads) < 0.20, f"最大重啟極差 {max(spreads):.1%}"
    assert float(np.mean(spreads)) < 0.10, f"平均重啟極差 {np.mean(spreads):.1%}"


def test_reproducibility():
    """同輸入 + 同 config（含 seeds）→ 結果完全一致（無隱藏全域狀態）"""
    spend, y, _, weekdays = gen_dataset(7)
    cfg = dict(TEST_CONFIG, n_trials=60, n_restarts=2)
    a = run_analysis(spend, y, weekdays=weekdays, config_overrides=cfg)
    b = run_analysis(spend, y, weekdays=weekdays, config_overrides=cfg)
    assert a == b


# ── 2. guardrails ──────────────────────────────────────────────────────

def _tiny_dataset(days=180, mean_conv=20.0):
    rng = np.random.default_rng(0)
    spend = {"A": rng.uniform(500, 1500, days), "B": rng.uniform(500, 1500, days)}
    y = rng.poisson(mean_conv, days).astype(float)
    return spend, y


def test_guardrail_min_days():
    spend, y = _tiny_dataset(days=60)
    with pytest.raises(GuardrailViolation, match="天數"):
        run_analysis(spend, y)


def test_guardrail_min_daily_conversions():
    spend, y = _tiny_dataset(mean_conv=2.0)
    with pytest.raises(GuardrailViolation, match="日均轉換"):
        run_analysis(spend, y)


def test_guardrail_min_group_spend_share():
    spend, y = _tiny_dataset()
    spend["C_tiny"] = np.full(len(y), 1.0)  # 占比遠低於 3%
    with pytest.raises(GuardrailViolation, match="C_tiny"):
        run_analysis(spend, y)


def test_guardrail_length_mismatch():
    spend, y = _tiny_dataset()
    spend["A"] = spend["A"][:-5]
    violations = check_guardrails(
        {k: np.asarray(v) for k, v in spend.items()}, np.asarray(y), resolve_config()
    )
    assert any("長度" in v for v in violations)


# ── 2b. holdout 天數守門（docs/27 任務 2.3） ────────────────────────────

def test_guardrail_holdout_days_equal_to_total_days_rejected():
    """holdout_days == n：訓練集為空，必須拒絕，不可 silently 產出全 0 結果。"""
    spend, y = _tiny_dataset(days=90)
    with pytest.raises(GuardrailViolation, match="無訓練資料"):
        run_analysis(spend, y, config_overrides={"holdout_days": 90})


def test_guardrail_holdout_days_ratio_too_high_rejected():
    """holdout 占比 > 1/2：訓練資料不足，拒絕。"""
    spend, y = _tiny_dataset(days=90)
    with pytest.raises(GuardrailViolation, match="比例過高"):
        run_analysis(spend, y, config_overrides={"holdout_days": 46})


def test_guardrail_documented_minimum_90_days_with_default_holdout_passes():
    """docs/21 記載的下限「90 天 + 預設 holdout 45 天」（比例剛好 50%）必須
    仍可通過 guardrail——這是文件記載的合法最小組合，門檻不可誤傷。"""
    spend, y = _tiny_dataset(days=90)
    violations = check_guardrails(spend, y, resolve_config())
    assert not any("holdout" in v for v in violations)


def test_guardrail_default_180_days_with_default_holdout_passes():
    """預設建議組合「180 天 + 預設 holdout 45 天」（比例 25%）不受新規則影響。"""
    spend, y = _tiny_dataset(days=180)
    violations = check_guardrails(spend, y, resolve_config())
    assert not any("holdout" in v for v in violations)


# ── 3. diagnose ────────────────────────────────────────────────────────

def test_diagnose_collinearity_and_ceiling():
    rng = np.random.default_rng(1)
    base = rng.uniform(1000, 3000, 180)
    spend = {
        "A": base,
        "B": base * 1.5 + rng.normal(0, 10, 180),  # 與 A 幾乎完全共線
        "C": rng.uniform(1000, 3000, 180),          # 獨立
    }
    y = rng.poisson(20, 180).astype(float)
    d = diagnose(spend, y, resolve_config())
    pairs = {(w["group_a"], w["group_b"]) for w in d["collinearity_warnings"]}
    assert ("A", "B") in pairs
    assert all("C" not in p for p in pairs)
    # Poisson(20) → var ≈ mean → 天花板 ≈ 0（純雜訊、無可解釋變異）
    assert d["poisson_ceiling_r2"]["full"] < 0.3
    assert d["data_summary"]["days"] == 180


def test_diagnose_zero_variance_series():
    spend = {"A": np.zeros(180), "B": np.ones(180) * 100}
    y = np.random.default_rng(0).poisson(20, 180).astype(float)
    d = diagnose(spend, y, resolve_config())
    assert d["collinearity_warnings"] == []  # 零變異序列相關係數視為 0，不 crash


# ── 4. 邊際步長與基礎函數 ──────────────────────────────────────────────

def test_marginal_step_auto_by_spend_scale():
    cfg = resolve_config()
    assert resolve_marginal_step(np.full(10, 5000.0), cfg) == 100.0   # 1% = 50 → 下限 100
    assert resolve_marginal_step(np.full(10, 30000.0), cfg) == 300.0  # 1% = 300
    assert resolve_marginal_step(np.full(10, 31000.0), cfg) == 400.0  # 310 → 向上取整 400
    assert resolve_marginal_step(np.zeros(10), cfg) == 100.0          # 無活躍花費 → 下限
    cfg_fixed = resolve_config({"marginal_step": 1000})
    assert resolve_marginal_step(np.full(10, 30000.0), cfg_fixed) == 1000.0


def test_adstock_hill_basics():
    x = np.array([100.0, 0.0, 0.0])
    np.testing.assert_allclose(adstock(x, 0.5), [100.0, 50.0, 25.0])
    np.testing.assert_allclose(adstock(x, 0.0), x)
    assert hill(0.0, 100.0) == 0.0
    assert hill(100.0, 100.0) == 0.5
    assert 0.99 < hill(1e9, 100.0) < 1.0


def test_nonneg_ridge_recovers_nonneg_solution():
    rng = np.random.default_rng(3)
    X = rng.uniform(0, 1, (200, 3))
    w_true = np.array([2.0, 0.0, 5.0])
    y = X @ w_true + rng.normal(0, 0.01, 200)
    w = nonneg_ridge(X, y, lam=0.01, iters=5000)
    assert np.all(w >= 0)
    np.testing.assert_allclose(w, w_true, atol=0.15)


def test_resolve_config_rejects_unknown_keys():
    with pytest.raises(ValueError, match="unknown"):
        resolve_config({"typo_key": 1})


def test_results_are_json_serializable(synthetic_runs):
    import json

    _, out = synthetic_runs[0]
    json.dumps(out)  # 不可含 numpy 型別


def test_run_analysis_holdout_zero_variance_r2_is_none_not_crash():
    """holdout 段 y 為常數（零變異）時 r2_holdout 為 None；docs/27 任務 2.3
    修復前 `dist([None, None, ...])` 會直接 `np.median` TypeError 讓整筆分析
    失敗，修復後應正常完成、r2.holdout 三個欄位皆為 None。"""
    rng = np.random.default_rng(9)
    days = 180
    holdout_days = 45
    spend = {"A": rng.uniform(500, 1500, days), "B": rng.uniform(500, 1500, days)}
    y = rng.poisson(20, days).astype(float)
    y[-holdout_days:] = 15.0  # holdout 段常數 → ss_hold = 0 → r2_holdout = None
    weekdays = np.arange(days) % 7

    out = run_analysis(
        spend, y, weekdays=weekdays,
        config_overrides={"n_trials": 60, "n_restarts": 2, "holdout_days": holdout_days},
    )
    assert out["results"]["r2"]["holdout"] == {"median": None, "min": None, "max": None}
    # full R² 應正常計算（訓練段仍有變異）
    assert out["results"]["r2"]["full"]["median"] is not None

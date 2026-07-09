"""
Contribution 模組任務 1.4 grouping 規則測試（docs/21 §3.3）

驗收：auto_group() 在不同輸入下產生合理分組；validate_manual_groups 拒絕
非法手動輸入。
"""

from __future__ import annotations

import pytest

from modules.contribution import grouping


def _camp(cid: str, name: str, spend: float) -> dict:
    return {"campaign_id": cid, "campaign_name": name, "spend": spend}


# ── auto_group 基本行為 ──────────────────────────────────────────────
@pytest.mark.unit
def test_auto_group_empty_input_returns_other_bucket():
    assert grouping.auto_group([]) == [
        {"group_key": "G_other", "group_name": "其他", "campaign_ids": [], "source": "auto"}
    ]


@pytest.mark.unit
def test_auto_group_zero_spend_routes_all_to_other():
    out = grouping.auto_group([_camp("c1", "A", 0.0), _camp("c2", "B", 0.0)])
    keys = [g["group_key"] for g in out]
    assert keys == ["G_other"]
    assert sorted(out[0]["campaign_ids"]) == ["c1", "c2"]


@pytest.mark.unit
def test_auto_group_alwayson_keyword_becomes_G1():
    out = grouping.auto_group(
        [
            _camp("a", "OB 主力常態 A", 1000.0),
            _camp("b", "OB 主力常態 B", 800.0),
            _camp("c", "OB 影片 reels C", 500.0),
        ]
    )
    keys = [g["group_key"] for g in out]
    # 兩組主力常態聚合為 G1、影片為 G2
    assert "G1" in keys
    assert "G2" in keys
    g1 = next(g for g in out if g["group_key"] == "G1")
    assert sorted(g1["campaign_ids"]) == ["a", "b"]


@pytest.mark.unit
def test_auto_group_terminates_with_unmatched_low_share_campaign():
    """2026-07-08 全站反覆死亡真因的回歸測試。

    「名稱不含任何關鍵詞（Step 1 落入 G_other 桶）且占比 < 3%」的活動，
    舊版在 Step 2 迭代 G_other 桶時把它 append 回正在迭代的同一個 list，
    造成無限追加（RSS 每秒 +7MB 直到機器記憶體耗盡）。修正後必須正常
    終止、該活動留在 G_other 且不重複。
    """
    import threading

    camps = [
        _camp("big", "OB 常態主力", 1000.0),   # 命中 G1
        _camp("weird", "雙11特賣", 10.0),      # 無關鍵詞 + <3% → 舊版無限迴圈
    ]
    result: dict = {}

    def _run() -> None:
        result["out"] = grouping.auto_group(camps)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=10)
    assert "out" in result, "auto_group 未在 10 秒內返回（無限追加迴圈回歸）"

    out = result["out"]
    g_other = next(g for g in out if g["group_key"] == "G_other")
    # 該活動留在 G_other 且恰好一次（舊版會無限重複）
    assert g_other["campaign_ids"].count("weird") == 1
    # 全部組別無重複活動
    all_ids = [cid for g in out for cid in g["campaign_ids"]]
    assert len(all_ids) == len(set(all_ids))


@pytest.mark.unit
def test_auto_group_small_share_merges_into_G_other():
    out = grouping.auto_group(
        [
            _camp("big", "OB 主力 A", 1000.0),
            _camp("big2", "OB 主力 B", 800.0),
            _camp("tiny", "OB 測試 X", 10.0),  # < 3%
        ]
    )
    other = next((g for g in out if g["group_key"] == "G_other"), None)
    assert other is not None
    assert "tiny" in other["campaign_ids"]


@pytest.mark.unit
def test_auto_group_caps_groups_within_target_max():
    """組數 > 8 時低花費組別被併入 G_other。

    為觸發「> 8 組」場景，輸入 11 個名稱完全不同且不匹配任何關鍵詞的活動：
      - 共同前綴 4 字檢查：每個名稱前 4 字都不同 → 各自走 G_other
      - 結果：11 個 G_other 候選組（每組 1 個活動）
    然後 `len(final_list) > TARGET_GROUPS_MAX` 觸發組數收斂：低花費組別
    併入 G_other，最終 ≤ 8 組。
    """
    # 11 個英文活動名，前 4 字皆不同，不匹配任何關鍵詞
    names = [
        "AlphaOne Main", "BetaTwo Main", "GammaThree Main",
        "DeltaFour Main", "EpsilonFive Main", "ZetaSix Main",
        "EtaSeven Main", "ThetaEight Main", "IotaNine Main",
        "KappaTen Main", "LambdaEleven Main",
    ]
    camps = [_camp(f"p{i}", n, 100.0 + i * 5) for i, n in enumerate(names)]
    out = grouping.auto_group(camps)
    # 收斂後組數 ≤ 8
    assert len(out) <= grouping.TARGET_GROUPS_MAX
    # 11 個活動都必須在輸出中（沒有丟失；用 set 比較避開 p10 vs p2 字典序）
    all_ids = {c for g in out for c in g["campaign_ids"]}
    assert all_ids == {f"p{i}" for i in range(11)}
    # 至少有 1 個其他桶（被拆分或合併後）
    assert any("其他" in g["group_name"] for g in out)


@pytest.mark.unit
def test_auto_group_marks_source_as_auto():
    out = grouping.auto_group([_camp("a", "OB 主力 A", 1000.0)])
    assert all(g["source"] == "auto" for g in out)


# ── docs/27 任務 3.1：關鍵詞誤判修正 ─────────────────────────────────
@pytest.mark.unit
def test_auto_group_smart_shopping_not_misclassified_as_retargeting():
    """舊版 G5 含裸 `rt`，"Smart Shopping" 會誤含 "rt" 子字串被分進大包裝
    再行銷；移除裸 `rt` 後不應再誤判（保留 `retargeting`/`再行銷` 等強訊號）。"""
    out = grouping.auto_group(
        [
            _camp("a", "Smart Shopping Main", 1000.0),
            _camp("b", "Smart Shopping Sub", 800.0),
        ]
    )
    g5 = next((g for g in out if g["group_key"] == "G5"), None)
    assert g5 is None or ("a" not in g5["campaign_ids"] and "b" not in g5["campaign_ids"])


@pytest.mark.unit
def test_auto_group_contest_not_misclassified_as_test_traffic():
    """舊版 G7 的 `test` 無邊界，"Contest"/"Latest" 會誤含子字串被分進測試
    導流；改 `\\btest\\b` 後不應再誤判。"""
    out = grouping.auto_group(
        [
            _camp("a", "Photo Contest Campaign", 1000.0),
            _camp("b", "Photo Contest Followup", 800.0),
        ]
    )
    g7 = next((g for g in out if g["group_key"] == "G7"), None)
    assert g7 is None or ("a" not in g7["campaign_ids"] and "b" not in g7["campaign_ids"])


@pytest.mark.unit
def test_auto_group_bare_test_keyword_still_matches_g7():
    """word boundary 修正後，獨立出現的 "test" 仍應正確匹配 G7（不是矯枉過正）。"""
    out = grouping.auto_group(
        [
            _camp("a", "A/B test 導流", 1000.0),
            _camp("b", "A/B test 導流 2", 800.0),
        ]
    )
    g7 = next((g for g in out if g["group_key"] == "G7"), None)
    assert g7 is not None
    assert set(g7["campaign_ids"]) == {"a", "b"}


@pytest.mark.unit
def test_auto_group_activity_keyword_no_longer_triggers_g3():
    """`活動` 已從 G3 關鍵詞移除（訊號太弱，中文活動命名極常見）；含此字但
    無其他強訊號的活動不應被誤分進官網檔期。"""
    out = grouping.auto_group(
        [
            _camp("a", "母親節活動企劃", 1000.0),
            _camp("b", "母親節活動執行", 800.0),
        ]
    )
    g3 = next((g for g in out if g["group_key"] == "G3"), None)
    assert g3 is None or ("a" not in g3["campaign_ids"] and "b" not in g3["campaign_ids"])


# ── docs/27 任務 3.1：前綴聚類真正實作（取代 dead code） ──────────────
@pytest.mark.unit
def test_auto_group_real_prefix_clustering_groups_unmatched_campaigns():
    """3 個同前綴、無關鍵詞匹配、合計占比達標的活動應被聚為一個
    `G_prefix_*` 組——舊版 dead code 下這 3 個活動只會各自落入 G_other。"""
    out = grouping.auto_group(
        [
            _camp("a", "嚴選好物 Alpha", 1000.0),
            _camp("b", "嚴選好物 Beta", 900.0),
            _camp("c", "嚴選好物 Gamma", 800.0),
        ]
    )
    prefix_groups = [g for g in out if g["group_key"].startswith("G_prefix_")]
    assert len(prefix_groups) == 1
    assert set(prefix_groups[0]["campaign_ids"]) == {"a", "b", "c"}
    # 不應散落在 G_other
    g_other = next((g for g in out if g["group_key"] == "G_other"), None)
    if g_other is not None:
        assert not ({"a", "b", "c"} & set(g_other["campaign_ids"]))


@pytest.mark.unit
def test_auto_group_prefix_cluster_requires_at_least_two_members():
    """前綴桶內只有 1 個活動時不成組，直接併入 G_other（單一活動的「前綴」
    不構成分組意義）。"""
    out = grouping.auto_group(
        [
            _camp("big", "OB 主力常態 A", 1000.0),
            _camp("solo", "嚴選好物 Alpha", 500.0),  # 唯一帶此前綴的活動
        ]
    )
    prefix_groups = [g for g in out if g["group_key"].startswith("G_prefix_")]
    assert prefix_groups == []
    g_other = next((g for g in out if g["group_key"] == "G_other"), None)
    assert g_other is not None
    assert "solo" in g_other["campaign_ids"]


@pytest.mark.unit
def test_auto_group_prefix_cluster_requires_aggregate_share_above_threshold():
    """前綴桶合計花費占比 < min_spend_share 時不成組，即使桶內 ≥ 2 個活動。"""
    out = grouping.auto_group(
        [
            _camp("big", "OB 主力常態 A", 10000.0),
            _camp("p1", "嚴選好物 Alpha", 5.0),  # 兩者合計占比遠低於 3%
            _camp("p2", "嚴選好物 Beta", 5.0),
        ]
    )
    prefix_groups = [g for g in out if g["group_key"].startswith("G_prefix_")]
    assert prefix_groups == []
    g_other = next((g for g in out if g["group_key"] == "G_other"), None)
    assert g_other is not None
    assert {"p1", "p2"}.issubset(set(g_other["campaign_ids"]))


# ── validate_manual_groups ──────────────────────────────────────────
@pytest.mark.unit
def test_validate_manual_groups_accepts_full_coverage():
    errors, missing = grouping.validate_manual_groups(
        {"c1", "c2", "c3"},
        [
            {"group_key": "G1", "group_name": "X", "campaign_ids": ["c1", "c2"]},
            {"group_key": "G2", "group_name": "Y", "campaign_ids": ["c3"]},
        ],
    )
    assert errors == []
    assert missing == []


@pytest.mark.unit
def test_validate_manual_groups_rejects_missing_campaign():
    errors, missing = grouping.validate_manual_groups(
        {"c1", "c2"},
        [{"group_key": "G1", "group_name": "X", "campaign_ids": ["c1"]}],
    )
    assert any("未分配" in e for e in errors)
    assert missing == ["c2"]


@pytest.mark.unit
def test_validate_manual_groups_rejects_duplicate_key():
    errors, _ = grouping.validate_manual_groups(
        {"c1", "c2"},
        [
            {"group_key": "G1", "group_name": "X", "campaign_ids": ["c1"]},
            {"group_key": "G1", "group_name": "Y", "campaign_ids": ["c2"]},
        ],
    )
    assert any("重複" in e for e in errors)


@pytest.mark.unit
def test_validate_manual_groups_rejects_unauthorized_campaign():
    errors, _ = grouping.validate_manual_groups(
        {"c1"},
        [{"group_key": "G1", "group_name": "X", "campaign_ids": ["c1", "c999"]}],
    )
    assert any("c999" in e and "不屬於" in e for e in errors)


@pytest.mark.unit
def test_validate_manual_groups_rejects_duplicate_campaign_across_groups():
    errors, _ = grouping.validate_manual_groups(
        {"c1", "c2"},
        [
            {"group_key": "G1", "group_name": "X", "campaign_ids": ["c1"]},
            {"group_key": "G2", "group_name": "Y", "campaign_ids": ["c1", "c2"]},
        ],
    )
    assert any("多個組別" in e for e in errors)

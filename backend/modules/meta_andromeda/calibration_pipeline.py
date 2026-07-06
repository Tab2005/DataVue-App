"""
Meta Andromeda Calibration Pipeline
分析校準資料集的偏差模式，並自動生成修正版 Scoring Profile。
"""

import logging
import uuid
from datetime import datetime, timezone

from database.models.meta_andromeda import (
    MetaAndromedaCalibrationDataset,
    MetaAndromedaCalibrationItem,
    MetaAndromedaScoringProfile,
)
from .objective_routing import resolve_objective_group

logger = logging.getLogger(__name__)

MIN_ITEMS_FOR_CALIBRATION = 10
# 每個 objective_group few-shot 最多注入的錯例/對例數量
MAX_WRONG_EXAMPLES_PER_GROUP = 2
MAX_CORRECT_EXAMPLES_PER_GROUP = 1

_BIAS_GUIDANCE = {
    "over_predict": (
        "校準備註：近期成效資料顯示模型系統性地高估 ROAS 級距。"
        "對 HIGH 分類要套用更嚴格的門檻——須有多項強烈正面訊號且無明顯風險標記才給 HIGH。"
        "當視覺層次強但 CTA 或文案表現平庸時，預設給 MID 而非 HIGH。"
        "評分時寧可保守。"
    ),
    "under_predict": (
        "校準備註：近期成效資料顯示模型系統性地低估 ROAS 級距。"
        "不要過度保守。"
        "若素材具備清楚的視覺焦點、有說服力的 CTA，且訊息與目標市場調性一致，"
        "即使有小瑕疵也應偏向給 MID 或 HIGH。"
        "只有在出現明顯的結構性弱點時才給 LOW。"
    ),
    "mixed": (
        "校準備註：近期成效資料顯示預測模式不一致，沒有明顯的偏差方向。"
        "請仔細檢視 diagnostic_breakdown 各項分數——確保 visual_appeal、copywriting、"
        "cta_clarity、relevance 都是獨立且一致地評估。"
        "不要讓某一項特別強的表現掩蓋其他項目的弱點。"
    ),
}


def analyze_dataset_bias(db, dataset_id: str) -> dict:
    """Analyze a calibration dataset's confusion matrix and pick few-shot candidates.

    Unlike the original implementation, items now include BOTH mispredictions
    (error > 0) and correct pairs (error == 0) — sync_calibration_dataset syncs
    both so this can build a real confusion matrix (with a diagonal) instead of
    an error-only matrix, and so few-shot examples can mix wrong AND right
    cases rather than only ever showing the model its mistakes.
    """
    items = (
        db.query(MetaAndromedaCalibrationItem)
        .filter(MetaAndromedaCalibrationItem.dataset_id == dataset_id)
        .all()
    )

    total_items = len(items)
    if total_items == 0:
        return {
            "total_items": 0,
            "error_item_count": 0,
            "min_samples_met": False,
            "dominant_bias": "mixed",
            "confusion_matrix": {},
            "over_predict_count": 0,
            "under_predict_count": 0,
            "worst_examples": [],
            "few_shot_by_group": {},
        }

    band_order = {"low": 1, "mid": 2, "high": 3}
    over_predict = 0
    under_predict = 0
    error_item_count = 0
    confusion: dict[str, dict[str, int]] = {}
    candidates_by_group: dict[str, list[dict]] = {}

    for item in items:
        obs_band = item.observed_band
        pred_band = item.prediction_band
        confusion.setdefault(obs_band, {})
        confusion[obs_band][pred_band] = confusion[obs_band].get(pred_band, 0) + 1

        obs_val = band_order.get(obs_band, 2)
        pred_val = band_order.get(pred_band, 2)
        if item.error and item.error > 0:
            error_item_count += 1
            if pred_val > obs_val:
                over_predict += 1
            elif pred_val < obs_val:
                under_predict += 1

        score_event = item.score_event
        request_context = (score_event.request_context or {}) if score_event else {}
        image_url = (
            request_context.get("asset_public_url")
            or request_context.get("asset_source_url")
        )
        candidate = {
            "item_id": item.id,
            "prediction_band": pred_band,
            "observed_band": obs_band,
            "error": item.error,
            "is_correct": not item.error,
            "headline": request_context.get("headline", ""),
            "primary_text": request_context.get("primary_text", ""),
            "roas": (item.performance_snapshot or {}).get("roas"),
            "diagnostic_breakdown": (score_event.diagnostic_breakdown or {}) if score_event else {},
            "image_url": image_url,
            "objective_group": resolve_objective_group(item.objective),
        }
        candidates_by_group.setdefault(candidate["objective_group"], []).append(candidate)

    few_shot_by_group: dict[str, list[dict]] = {}
    worst_examples: list[dict] = []
    for group, candidates in candidates_by_group.items():
        wrong = sorted(
            (c for c in candidates if not c["is_correct"]),
            key=lambda c: c["error"],
            reverse=True,
        )
        correct = [c for c in candidates if c["is_correct"]]
        picked = wrong[:MAX_WRONG_EXAMPLES_PER_GROUP] + correct[:MAX_CORRECT_EXAMPLES_PER_GROUP]
        if picked:
            few_shot_by_group[group] = picked
        worst_examples.extend(wrong[:3])

    worst_examples.sort(key=lambda c: c["error"], reverse=True)
    worst_examples = worst_examples[:3]

    if over_predict > under_predict * 1.5:
        dominant_bias = "over_predict"
    elif under_predict > over_predict * 1.5:
        dominant_bias = "under_predict"
    else:
        dominant_bias = "mixed"

    return {
        "total_items": total_items,
        "error_item_count": error_item_count,
        "min_samples_met": error_item_count >= MIN_ITEMS_FOR_CALIBRATION,
        "dominant_bias": dominant_bias,
        "confusion_matrix": confusion,
        "over_predict_count": over_predict,
        "under_predict_count": under_predict,
        "worst_examples": worst_examples,
        "few_shot_by_group": few_shot_by_group,
    }


def format_few_shot_content(examples: list[dict]) -> tuple[str, list[dict]]:
    """Render few-shot examples as (prompt text block, multimodal image content blocks).

    Mixes correct and incorrect prior predictions (rather than only errors) and
    surfaces the model's own diagnostic_breakdown at scoring time so the lesson
    is "here is what you saw vs what actually happened", not just a band label
    mismatch. Image blocks are returned separately so the caller can splice them
    into the OpenRouter multimodal user_content list, since few-shot scoring
    relies primarily on the image.
    """
    if not examples:
        return "", []

    lines = [
        "\n\nCALIBRATION EXAMPLES (mix of correct and incorrect prior predictions; "
        "reference images are attached in the same order as these examples):"
    ]
    image_blocks: list[dict] = []
    for i, ex in enumerate(examples, 1):
        pred = ex.get("prediction_band", "?")
        obs = ex.get("observed_band", "?")
        headline = str(ex.get("headline") or "")[:80]
        roas = ex.get("roas")
        roas_str = f" (actual ROAS: {roas:.2f})" if isinstance(roas, (int, float)) else ""
        is_correct = ex.get("is_correct")
        outcome = "CORRECT prediction" if is_correct else "WRONG prediction"

        diag = ex.get("diagnostic_breakdown") or {}
        diag_str = "; ".join(f"{k}={v}" for k, v in list(diag.items())[:4]) if diag else "n/a"

        if is_correct:
            lesson = "This is a good reference — keep evaluating similar creatives the same way."
        else:
            lesson = (
                "Lesson: the diagnostic evidence above did not match actual performance — "
                "re-examine which visual or copy signal was misread for this pattern."
            )

        lines.append(
            f"  Example {i} [{outcome}]: predicted='{pred}', actual='{obs}'{roas_str}. "
            f"Headline: '{headline}'. Diagnostic at scoring time: {diag_str}. {lesson}"
        )

        image_url = ex.get("image_url")
        if isinstance(image_url, str) and image_url.startswith(("http://", "https://", "data:image/")):
            lines.append(f"  (Example {i} reference image attached below)")
            image_blocks.append({"type": "image_url", "image_url": {"url": image_url}})

    return "\n".join(lines), image_blocks


def _generate_llm_guidance(bias: dict, dataset_id: str, db=None) -> str | None:
    """Ask an LLM to turn the confusion matrix + worst examples into a specific
    calibration instruction, replacing the generic 3-template fallback. Returns
    None on any failure (no API key, network error, empty response, ...) so the
    caller falls back to _BIAS_GUIDANCE — this must never block calibration.
    """
    try:
        from services.ai.openrouter_client import OpenRouterClient
        from core.config import settings
        from .runtime import resolve_openrouter_api_key_for_asset

        api_key = settings.OPENROUTER_API_KEY
        if db is not None:
            # 用資料集裡任一筆項目的素材上傳者金鑰（跟正常評分流程一致），而不是只看
            # container 環境變數——見 resolve_openrouter_api_key_for_asset 的說明
            sample_item = (
                db.query(MetaAndromedaCalibrationItem)
                .filter(MetaAndromedaCalibrationItem.dataset_id == dataset_id)
                .first()
            )
            sample_asset_id = (
                sample_item.observed_creative.asset_id
                if sample_item and sample_item.observed_creative else None
            )
            api_key = resolve_openrouter_api_key_for_asset(db, sample_asset_id)

        client = OpenRouterClient(api_key=api_key)
        if client.client is None:
            return None

        confusion_lines = [
            f"  observed={obs_band}, predicted={pred_band}: {count} 筆"
            for obs_band, preds in bias["confusion_matrix"].items()
            for pred_band, count in preds.items()
        ]
        example_lines = [
            f"  - predicted={ex.get('prediction_band')}, observed={ex.get('observed_band')}, "
            f"headline={ex.get('headline', '')!r}, roas={ex.get('roas')}, "
            f"diagnostic={ex.get('diagnostic_breakdown')}"
            for ex in bias["worst_examples"][:5]
        ]

        prompt = (
            "You are analyzing a creative-scoring model's prediction errors to write a concise, "
            "specific calibration instruction for the model's next prompt version.\n\n"
            f"Dominant bias direction: {bias['dominant_bias']}\n"
            "Confusion matrix (observed vs predicted band counts):\n"
            + "\n".join(confusion_lines)
            + "\n\nWorst mispredicted examples:\n"
            + "\n".join(example_lines)
            + "\n\nWrite a single calibration-note paragraph (3-5 sentences, in Traditional Chinese "
            "/ 繁體中文, prefixed with '校準備註：') that tells the scoring model specifically what "
            "pattern to watch for and how to adjust — not generic advice like 'be more careful'. "
            "If you can infer a concrete creative pattern (e.g. text-heavy images, missing CTA, "
            "multi-person photos) from the examples, name it. "
            "Output ONLY the paragraph text, no preamble."
        )
        content = client.generate_content(
            prompt,
            model=None,
            system_prompt="You are a precise ML calibration analyst. Be concrete, not generic.",
            temperature=0.3,
            max_tokens=400,
            timeout=15,
        )
        content = (content or "").strip()
        return content or None
    except Exception as exc:
        logger.warning(
            "[CalibrationPipeline] LLM guidance generation failed for dataset %s: %s", dataset_id, exc
        )
        return None


def _set_dataset_status(db, dataset_id: str, status: str, extra_summary: dict | None = None) -> None:
    dataset = (
        db.query(MetaAndromedaCalibrationDataset)
        .filter(MetaAndromedaCalibrationDataset.id == dataset_id)
        .first()
    )
    if dataset is None:
        return
    dataset.status = status
    if extra_summary:
        summary = dict(dataset.summary or {})
        summary.update(extra_summary)
        dataset.summary = summary
    db.commit()


def _apply_split_labels(db, dataset_id: str, few_shot_item_ids: set[str]) -> None:
    """Mark every item in the dataset as split='few_shot' (leaked into the prompt,
    must not be used to evaluate the resulting profile) or split='holdout' (clean,
    reserved for the promote-gate backtest in repository.evaluate_profile_on_holdout)."""
    items = (
        db.query(MetaAndromedaCalibrationItem)
        .filter(MetaAndromedaCalibrationItem.dataset_id == dataset_id)
        .all()
    )
    for item in items:
        item.split = "few_shot" if item.id in few_shot_item_ids else "holdout"
    db.commit()


def generate_calibrated_profile(db, dataset_id: str, base_profile_name: str) -> str | None:
    bias = analyze_dataset_bias(db, dataset_id)

    if not bias["min_samples_met"]:
        logger.info(
            "[CalibrationPipeline] Dataset %s has only %d error items (< %d). Skipping profile generation.",
            dataset_id,
            bias["error_item_count"],
            MIN_ITEMS_FOR_CALIBRATION,
        )
        _set_dataset_status(db, dataset_id, "calibration_skipped:insufficient_samples")
        return None

    base_profile = (
        db.query(MetaAndromedaScoringProfile)
        .filter(MetaAndromedaScoringProfile.profile_name == base_profile_name)
        .first()
    )
    if base_profile is None:
        # 自我修復：正式環境曾發生 seed migration 因表已存在而被跳過、導致
        # meta_andromeda_scoring_profiles 整張表是空的（2026-07-03 生產事故，已用
        # hotfix migration 20260703_ma_seed_profile_hotfix 補回去）。這裡加一層防禦，
        # 未來若再因任何原因缺失 base profile，用 runtime.py 的硬編碼 fallback prompt
        # 自動補一筆同名 profile，而不是靜默失敗、卡住整條校準閉環。
        logger.warning(
            "[CalibrationPipeline] Base profile '%s' not found. Attempting to auto-heal from "
            "runtime fallback prompt instead of silently failing.",
            base_profile_name,
        )
        try:
            from .runtime import _FALLBACK_SYSTEM_PROMPT, _FALLBACK_USER_PROMPT_TEMPLATE

            base_profile = MetaAndromedaScoringProfile(
                id=f"sp_autoheal_{uuid.uuid4().hex[:12]}",
                profile_name=base_profile_name,
                user_prompt_template=_FALLBACK_USER_PROMPT_TEMPLATE,
                system_prompt=_FALLBACK_SYSTEM_PROMPT,
                source="auto_healed_fallback",
                is_promoted=False,
            )
            db.add(base_profile)
            db.commit()
            logger.warning(
                "[CalibrationPipeline] Auto-healed missing base profile '%s' from runtime fallback prompt.",
                base_profile_name,
            )
        except Exception as exc:
            logger.error(
                "[CalibrationPipeline] Auto-heal for base profile '%s' also failed: %s",
                base_profile_name, exc,
            )
            _set_dataset_status(
                db,
                dataset_id,
                "calibration_failed:base_profile_missing",
                extra_summary={"base_profile_name": base_profile_name},
            )
            return None

    new_profile_name = f"{base_profile_name}_cal_{dataset_id[:8]}"
    if db.query(MetaAndromedaScoringProfile).filter(
        MetaAndromedaScoringProfile.profile_name == new_profile_name
    ).first():
        logger.info("[CalibrationPipeline] Profile '%s' already exists. Skipping.", new_profile_name)
        _set_dataset_status(
            db,
            dataset_id,
            "calibrated",
            extra_summary={"generated_profile_name": new_profile_name},
        )
        return new_profile_name

    calibration_guidance = _generate_llm_guidance(bias, dataset_id, db) or _BIAS_GUIDANCE[bias["dominant_bias"]]

    few_shot_by_group = bias["few_shot_by_group"]
    # 保留頂層 few_shot_examples 供沒有 objective_profiles 覆蓋的舊路徑使用（向下相容）
    flat_few_shot_examples = bias["worst_examples"]
    objective_profiles = {
        group: {"few_shot_examples": examples}
        for group, examples in few_shot_by_group.items()
    }

    new_profile = MetaAndromedaScoringProfile(
        id=f"sp_{uuid.uuid4().hex[:12]}",
        profile_name=new_profile_name,
        user_prompt_template=base_profile.user_prompt_template,
        system_prompt=base_profile.system_prompt,
        calibration_guidance=calibration_guidance,
        few_shot_examples=flat_few_shot_examples,
        objective_profiles=objective_profiles or None,
        bias_summary=bias,
        source="calibration_auto",
        base_profile_name=base_profile_name,
        calibration_dataset_id=dataset_id,
        is_promoted=False,
    )
    db.add(new_profile)
    _set_dataset_status(
        db,
        dataset_id,
        "calibrated",
        extra_summary={"generated_profile_name": new_profile_name},
    )

    few_shot_item_ids = {
        ex["item_id"]
        for examples in few_shot_by_group.values()
        for ex in examples
        if ex.get("item_id")
    }
    _apply_split_labels(db, dataset_id, few_shot_item_ids)

    logger.info(
        "[CalibrationPipeline] Generated new profile '%s' from dataset %s (bias=%s, error_items=%d, total_items=%d).",
        new_profile_name,
        dataset_id,
        bias["dominant_bias"],
        bias["error_item_count"],
        bias["total_items"],
    )
    return new_profile_name


# ── Promote-gate holdout backtest (P1-6) ─────────────────────────────────────

MIN_HOLDOUT_SIZE = 5
# accuracy 不容忍任何劣化；ranking 相關性給一點雜訊容忍空間（holdout 樣本通常不大）
BACKTEST_SPEARMAN_TOLERANCE = 0.02


async def _default_holdout_scorer(item: MetaAndromedaCalibrationItem, profile_name: str) -> dict | None:
    """Re-score one holdout CalibrationItem's asset with `profile_name`, bypassing
    whatever profile is currently is_promoted (ignore_promoted=True). Returns the
    runtime score result dict, or None if the item can't be scored."""
    from .runtime import OpenRouterScoringProvider, resolve_openrouter_api_key_for_asset
    from .model_registry import model_registry
    from core.config import settings
    from database import SessionLocal

    obs = item.observed_creative
    score_event = item.score_event
    if obs is None or not obs.asset_uri:
        return None
    request_context = (score_event.request_context or {}) if score_event else {}

    # 用素材上傳者的個人金鑰（跟正常評分流程一致），而不是只看 container 環境變數
    # ——否則在金鑰其實存在 DB 而非環境變數的部署下，這裡會每一筆都失敗且不拋例外可查
    key_db = SessionLocal()
    try:
        api_key = resolve_openrouter_api_key_for_asset(key_db, obs.asset_id)
    finally:
        key_db.close()

    score_payload = {
        "asset_uri": obs.asset_uri,
        "asset_type": obs.media_type if obs.media_type in {"image", "video"} else "image",
        "objective": item.objective,
        "placement_family": item.placement_family,
        "market": item.market,
        "request_mode": "auto",
        "request_context": {
            "headline": request_context.get("headline"),
            "primary_text": request_context.get("primary_text"),
            "cta": request_context.get("cta"),
            "asset_public_url": request_context.get("asset_public_url"),
            "asset_source_url": request_context.get("asset_source_url") or obs.asset_uri,
            # 標記為回測請求：符合 self-consistency 的「高價值請求」資格（見 runtime.py
            # _resolve_self_consistency_sample_count），若啟用會取樣 N 次取中位數
            "is_backtest": True,
        },
    }
    # 回測用「backtest」情境選模型：若有指定專門的較強/較貴模型（release_channel=
    # backtest_reference）就優先用它，讓 ρ/accuracy 比較不被互動用的便宜模型天花板卡住
    registry_entry = model_registry.get_entry(purpose="backtest")
    provider = OpenRouterScoringProvider(api_key=api_key, force_profile_name=profile_name)
    try:
        return await provider.score(score_payload, registry_entry)
    except Exception as exc:
        logger.warning("[CalibrationPipeline] Holdout re-score failed for item %s: %s", item.id, exc)
        return None


async def evaluate_profile_on_holdout(db, profile_name: str, scorer=None) -> dict:
    """Promote-gate backtest: re-score the holdout split of the calibration dataset
    that produced `profile_name` using the candidate profile itself, and compare
    band accuracy / ranking correlation against the baseline already captured when
    those items were synced (their prediction_band/baseline_overall_score, produced
    by whatever profile was live at sync time).

    `scorer` is injectable for testing (async callable(item, profile_name) -> dict|None);
    defaults to _default_holdout_scorer which makes real AI provider calls.
    """
    from .repository import _spearman_r  # local import to avoid a module-level cycle

    scorer = scorer or _default_holdout_scorer

    profile = (
        db.query(MetaAndromedaScoringProfile)
        .filter(MetaAndromedaScoringProfile.profile_name == profile_name)
        .first()
    )
    if profile is None:
        return {"status": "skipped", "reason": "profile_not_found"}
    if not profile.calibration_dataset_id:
        return {"status": "skipped", "reason": "no_calibration_dataset"}

    holdout_items = (
        db.query(MetaAndromedaCalibrationItem)
        .filter(
            MetaAndromedaCalibrationItem.dataset_id == profile.calibration_dataset_id,
            MetaAndromedaCalibrationItem.split == "holdout",
        )
        .all()
    )
    if len(holdout_items) < MIN_HOLDOUT_SIZE:
        return {
            "status": "skipped",
            "reason": "insufficient_holdout",
            "holdout_size": len(holdout_items),
            "min_holdout_size": MIN_HOLDOUT_SIZE,
        }

    band_score = {"low": 1, "mid": 2, "high": 3}
    baseline_correct = 0
    candidate_correct = 0
    baseline_scores: list[float] = []
    candidate_scores: list[float] = []
    perf_values: list[float] = []
    evaluated = 0

    for item in holdout_items:
        result = await scorer(item, profile_name)
        if result is None:
            continue
        new_band = result.get("roas_band")
        new_score = result.get("overall_score")
        if new_band is None or new_score is None:
            continue

        evaluated += 1
        if item.prediction_band == item.observed_band:
            baseline_correct += 1
        if new_band == item.observed_band:
            candidate_correct += 1

        perf_value = (item.performance_snapshot or {}).get("roas")
        if perf_value is not None and item.baseline_overall_score is not None:
            perf_values.append(float(perf_value))
            baseline_scores.append(float(item.baseline_overall_score))
            candidate_scores.append(float(new_score))

    if evaluated == 0:
        return {"status": "skipped", "reason": "no_items_scored", "holdout_size": len(holdout_items)}

    baseline_accuracy = baseline_correct / evaluated
    candidate_accuracy = candidate_correct / evaluated
    baseline_spearman = _spearman_r(baseline_scores, perf_values) if len(baseline_scores) >= 3 else 0.0
    candidate_spearman = _spearman_r(candidate_scores, perf_values) if len(candidate_scores) >= 3 else 0.0

    accuracy_gate = candidate_accuracy >= baseline_accuracy
    spearman_gate = candidate_spearman >= (baseline_spearman - BACKTEST_SPEARMAN_TOLERANCE)
    passed_gate = accuracy_gate and spearman_gate

    result = {
        "status": "evaluated",
        "holdout_size": len(holdout_items),
        "evaluated_count": evaluated,
        "baseline_accuracy": round(baseline_accuracy, 4),
        "candidate_accuracy": round(candidate_accuracy, 4),
        "baseline_spearman": round(baseline_spearman, 4),
        "candidate_spearman": round(candidate_spearman, 4),
        "accuracy_delta": round(candidate_accuracy - baseline_accuracy, 4),
        "spearman_delta": round(candidate_spearman - baseline_spearman, 4),
        "accuracy_gate_passed": accuracy_gate,
        "spearman_gate_passed": spearman_gate,
        "passed_gate": passed_gate,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    bias_summary = dict(profile.bias_summary or {})
    bias_summary["holdout_backtest"] = result
    profile.bias_summary = bias_summary
    db.add(profile)
    db.commit()

    logger.info(
        "[CalibrationPipeline] Holdout backtest for '%s': accuracy %.3f -> %.3f, spearman %.3f -> %.3f, passed=%s",
        profile_name, baseline_accuracy, candidate_accuracy, baseline_spearman, candidate_spearman, passed_gate,
    )
    return result

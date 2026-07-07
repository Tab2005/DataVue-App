"""
Meta Andromeda Module - shared objective -> objective_group routing.

Single source of truth used by both the scoring runtime (prompt selection /
roas_band eligibility) and the repository (observed-band labeling / drift
matching). Prior to this module, runtime.py used an exact-match dict while
repository.py used substring matching, so the same FB objective (notably
OUTCOME_LEADS) could be routed to different groups on the prediction side
vs. the observation side.
"""

import logging

logger = logging.getLogger(__name__)

CONVERSION = "conversion"
LEAD = "lead"
TRAFFIC = "traffic"
AWARENESS = "awareness"
ENGAGEMENT = "engagement"
VIDEO = "video"
APP = "app"
UNKNOWN = "unknown"

KNOWN_OBJECTIVE_GROUPS = {CONVERSION, LEAD, TRAFFIC, AWARENESS, ENGAGEMENT, VIDEO, APP}

# Groups whose prompt explicitly forbids ROAS prediction and whose observed
# label should come from CTR/CPC rather than ROAS/CPA.
NON_ROAS_GROUPS = {TRAFFIC, AWARENESS, ENGAGEMENT, VIDEO}

_OBJECTIVE_GROUP_MAP: dict[str, str] = {
    # conversion
    "purchase": CONVERSION,
    "add_to_cart": CONVERSION,
    "complete_registration": CONVERSION,
    "outcome_sales": CONVERSION,
    # lead
    "lead": LEAD,
    "lead_gen": LEAD,
    "form_submit": LEAD,
    "outcome_leads": LEAD,
    # traffic
    "traffic": TRAFFIC,
    "link_clicks": TRAFFIC,
    "landing_page_views": TRAFFIC,
    "outcome_traffic": TRAFFIC,
    # awareness
    "brand_awareness": AWARENESS,
    "reach": AWARENESS,
    "awareness": AWARENESS,
    "outcome_awareness": AWARENESS,
    "page_likes": AWARENESS,
    # engagement
    "engagement": ENGAGEMENT,
    "post_engagement": ENGAGEMENT,
    "outcome_engagement": ENGAGEMENT,
    # video
    "video_views": VIDEO,
    "video": VIDEO,
    # app
    "outcome_app_promotion": APP,
    "app_installs": APP,
    "mobile_app_installs": APP,
}


def resolve_objective_group(objective: str | None) -> str:
    """Resolve a raw FB/Score-Lab objective string into a fixed objective_group.

    Empty/missing objective defaults to conversion (matches historical
    behavior of manual Score Lab uploads with no objective selected).
    An objective that IS provided but not recognized is routed to
    "unknown" (logged) rather than silently defaulting to conversion.
    """
    if not objective:
        return CONVERSION
    key = objective.lower().strip()
    group = _OBJECTIVE_GROUP_MAP.get(key)
    if group is None:
        logger.warning("[MetaAndromeda] Unknown objective '%s' - routed to 'unknown' group.", objective)
        return UNKNOWN
    return group


def is_roas_band_eligible(objective_group: str) -> bool:
    """Whether the given objective_group should predict/observe a ROAS-style band.

    conversion/lead/app/unknown fall back to ROAS/CPA-style evaluation;
    traffic/awareness/engagement/video explicitly opt out (roas_band=null).
    """
    return objective_group not in NON_ROAS_GROUPS


def is_predicted_band_eligible(objective_group: str) -> bool:
    """Whether the prompt for this objective_group asks the model to produce a
    comparable predicted band (any kind: ROAS, CTR potential, VTR potential, …).

    docs/23: traffic/awareness/video/engagement 原本被排除在 roas_band 之外
    （heuristic 與 observed_label 仍用 CTR/CPC 走 NON_ROAS 路由），但 prompt 已
    更新成「產出對應目標的潛力 band」，所以「是否有預測 band」這件事對所有已知
    group 都是 True。本函式供文件標記、未來統計分析與「這個 group 是不是應該在
    detail 頁顯示預測欄位」等語意判斷使用；不要拿來取代 is_roas_band_eligible()
    ——那條路由仍控制「觀測端用 ROAS 還是用 CTR/CPC」以及「heuristic fallback
    要不要產 band」這兩條獨立邏輯。
    """
    return objective_group in KNOWN_OBJECTIVE_GROUPS

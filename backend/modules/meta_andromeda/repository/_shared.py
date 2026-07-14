"""Shared imports and constants for Meta Andromeda repository modules."""

import logging
import os
from collections import Counter
from copy import deepcopy
from datetime import date, datetime, timezone
import math
import statistics
from sqlalchemy.orm import Session

from core.config import settings
from database.models.meta_andromeda import (
    MetaAndromedaAsset,
    MetaAndromedaCalibrationDataset,
    MetaAndromedaCalibrationItem,
    MetaAndromedaDeadLetter,
    MetaAndromedaDriftReport,
    MetaAndromedaFeedbackEvent,
    MetaAndromedaBacktestRun,
    MetaAndromedaModelRegistryEntry,
    MetaAndromedaObservedCreative,
    MetaAndromedaReleaseEvent,
    MetaAndromedaReleaseRecord,
    MetaAndromedaScoreEvent,
    MetaAndromedaScoringProfile,
    MetaAndromedaWorkerEvent,
)
from ..model_registry import model_registry
from ..objective_routing import NON_ROAS_GROUPS, resolve_objective_group
from ..labeling import (
    LABEL_POLICY_VERSION,
    compute_label_thresholds,
    label_observed_band,
    match_observed_to_prediction,
    persist_label_policy,
)

logger = logging.getLogger(__name__)

TERMINAL_SCORE_STATUSES = {"completed", "failed"}

RELEASE_FORCE_NOTE_PREFIX = "[FORCED_RELEASE_GATE_BYPASS]"
DEFAULT_RELEASE_MIN_PAIRWISE_ACCURACY = 0.55

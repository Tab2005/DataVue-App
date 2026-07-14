"""Facade for the Meta Andromeda DB-backed repository.

This package preserves the original ``modules.meta_andromeda.repository`` import
path while the implementation lives in focused mixins.
"""

from ._stats import _spearman_r
from .release_metrics import (
    ReleaseGateError,
    compute_backtest_run_metrics,
    compute_release_metrics,
    list_release_metric_pairs,
)
from .review_queue import ReviewQueueMixin
from .monitoring import MonitoringMixin
from .drift import DriftMixin
from .score_events import ScoreEventMixin
from .observations import ObservationMixin
from .release import PromotionGateError, ReleaseCandidateExistsError, ReleaseMixin
from .feedback_calibration import FeedbackCalibrationMixin
from .profiles_registry import ProfileRegistryMixin


class MetaAndromedaRepository(
    ReviewQueueMixin,
    MonitoringMixin,
    DriftMixin,
    ScoreEventMixin,
    ObservationMixin,
    ReleaseMixin,
    FeedbackCalibrationMixin,
    ProfileRegistryMixin,
):
    pass


repository = MetaAndromedaRepository()

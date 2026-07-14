"""Meta Andromeda service facade."""

from ._shared import *  # noqa: F403
from . import admin_ops as _admin_ops
from . import assets as _assets
from . import observation_import as _observation_import
from . import scoring as _scoring
from . import worker_callbacks as _worker_callbacks
from .admin_ops import AdminOpsServiceMixin
from .assets import AssetServiceMixin
from .observation_import import ObservationImportServiceMixin
from .scoring import ScoringServiceMixin
from .worker_callbacks import WorkerCallbackServiceMixin


class MetaAndromedaService(
    AdminOpsServiceMixin,
    AssetServiceMixin,
    ObservationImportServiceMixin,
    ScoringServiceMixin,
    WorkerCallbackServiceMixin,
):
    """Service layer for the current DataVue integration slice."""


for _module in (_admin_ops, _assets, _observation_import, _scoring, _worker_callbacks):
    _module.MetaAndromedaService = MetaAndromedaService


__all__ = ["MetaAndromedaService", "MetaAndromedaValidationError"]

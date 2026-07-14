"""APScheduler facade preserving the original core.scheduler import path."""

import sys
import types

from . import contribution_jobs as _contribution_jobs
from . import engine as _engine
from . import ga4_jobs as _ga4_jobs
from . import meta_andromeda_jobs as _meta_andromeda_jobs
from . import report_jobs as _report_jobs
from ._shared import *  # noqa: F403

_SCHEDULER_MODULES = (
    _engine,
    _report_jobs,
    _meta_andromeda_jobs,
    _contribution_jobs,
    _ga4_jobs,
)

for _module in _SCHEDULER_MODULES:
    for _name, _value in list(_module.__dict__.items()):
        if not _name.startswith("__"):
            globals()[_name] = _value

for _module in _SCHEDULER_MODULES:
    for _name, _value in list(globals().items()):
        if not _name.startswith("__"):
            setattr(_module, _name, _value)


class _SchedulerFacadeModule(types.ModuleType):
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if not name.startswith("__"):
            for module in _SCHEDULER_MODULES:
                setattr(module, name, value)


sys.modules[__name__].__class__ = _SchedulerFacadeModule

__all__ = [name for name in globals() if not name.startswith("__") and name != "_SCHEDULER_MODULES"]

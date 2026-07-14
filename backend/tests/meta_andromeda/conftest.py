"""
Meta Andromeda module integration tests
"""

import asyncio
import hashlib
import hmac
import json
import os
import time

import httpx
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import modules.meta_andromeda.service as meta_andromeda_service_module
import modules.meta_andromeda.queue_host as meta_andromeda_queue_host_module
import modules.meta_andromeda.storage as meta_andromeda_storage_module
import modules.meta_andromeda.router as meta_andromeda_router_module
import modules.meta_andromeda.internal_asset_gateway as meta_andromeda_internal_gateway_module
import core.scheduler as scheduler_module
from modules.auth import dependencies as auth_dependencies
import redis_cache as redis_cache_module
from database import Module, Permission, Role, RolePermission, Team, TeamMember, UserModuleAccess, UserRole
from modules.meta_andromeda.repository import repository
from modules.meta_andromeda.runtime import MetaAndromedaRuntimeAdapter, runtime_adapter
from modules.meta_andromeda.service import MetaAndromedaService
from main import app
from database import get_db
from modules.meta_andromeda.dependencies import (
    get_current_meta_andromeda_user,
    require_fb_ads_analytics_view,
    require_fb_ads_module,
    require_meta_andromeda_module,
    require_meta_andromeda_operate,
    require_meta_andromeda_release,
)

from modules.meta_andromeda.internal_router import router as meta_andromeda_internal_router

@pytest.fixture
def meta_andromeda_access(client, db, sample_admin_user):
    repository.ensure_seed_data(db)
    app.dependency_overrides[get_current_meta_andromeda_user] = lambda: sample_admin_user
    app.dependency_overrides[require_meta_andromeda_module] = lambda: True
    app.dependency_overrides[require_meta_andromeda_operate] = lambda: True
    app.dependency_overrides[require_meta_andromeda_release] = lambda: True
    app.dependency_overrides[require_fb_ads_module] = lambda: True
    app.dependency_overrides[require_fb_ads_analytics_view] = lambda: True
    yield client
    app.dependency_overrides.pop(get_current_meta_andromeda_user, None)
    app.dependency_overrides.pop(require_meta_andromeda_module, None)
    app.dependency_overrides.pop(require_meta_andromeda_operate, None)
    app.dependency_overrides.pop(require_meta_andromeda_release, None)
    app.dependency_overrides.pop(require_fb_ads_module, None)
    app.dependency_overrides.pop(require_fb_ads_analytics_view, None)

@pytest.fixture
def meta_andromeda_permission_client(client, db, sample_user):
    repository.ensure_seed_data(db)
    app.dependency_overrides[get_current_meta_andromeda_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db
    yield client, sample_user
    app.dependency_overrides.pop(get_current_meta_andromeda_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_db, None)

def _setup_meta_andromeda_team_access(
    db,
    user,
    *,
    membership_role: UserRole,
    role_key: str,
    grant_module_access: bool = True,
):
    team = Team(name=f"Meta Team {role_key}", owner_id=user.id)
    db.add(team)
    db.flush()

    module = Module(key="meta_andromeda", name="Meta Andromeda", enabled=True)
    db.add(module)
    db.flush()

    db.add(TeamMember(team_id=team.id, user_id=user.id, role=membership_role))
    if grant_module_access:
        db.add(
            UserModuleAccess(
                user_id=user.id,
                team_id=team.id,
                module_id=module.id,
                enabled=True,
            )
        )

    db.commit()
    return team

def _ensure_module(db, *, module_key: str, module_name: str) -> Module:
    module = db.query(Module).filter(Module.key == module_key).first()
    if module is None:
        module = Module(key=module_key, name=module_name, enabled=True)
        db.add(module)
        db.flush()
    return module

def _grant_team_module_access(db, *, user_id: str, team_id: str, module_key: str, module_name: str) -> None:
    module = _ensure_module(db, module_key=module_key, module_name=module_name)
    access = db.query(UserModuleAccess).filter(
        UserModuleAccess.user_id == user_id,
        UserModuleAccess.team_id == team_id,
        UserModuleAccess.module_id == module.id,
    ).first()
    if access is None:
        db.add(
            UserModuleAccess(
                user_id=user_id,
                team_id=team_id,
                module_id=module.id,
                enabled=True,
            )
        )

def _grant_team_role_permission(
    db,
    *,
    role_key: str,
    permission_key: str,
    permission_name: str,
    module_key: str,
    module_name: str,
) -> None:
    role = db.query(Role).filter(Role.key == role_key).first()
    if role is None:
        role = Role(key=role_key, name=role_key, scope="team")
        db.add(role)
        db.flush()

    module = _ensure_module(db, module_key=module_key, module_name=module_name)
    permission = db.query(Permission).filter(Permission.key == permission_key).first()
    if permission is None:
        permission = Permission(
            module_id=module.id,
            key=permission_key,
            name=permission_name,
            category="feature",
        )
        db.add(permission)
        db.flush()

    role_permission = db.query(RolePermission).filter(
        RolePermission.role_id == role.id,
        RolePermission.permission_id == permission.id,
    ).first()
    if role_permission is None:
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))

def _clear_meta_andromeda_operational_data(db) -> None:
    from database.models.meta_andromeda import (
        MetaAndromedaBacktestRun,
        MetaAndromedaDeadLetter,
        MetaAndromedaDriftReport,
        MetaAndromedaFeedbackEvent,
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent,
        MetaAndromedaWorkerEvent,
    )

    db.query(MetaAndromedaDeadLetter).delete()
    db.query(MetaAndromedaWorkerEvent).delete()
    db.query(MetaAndromedaFeedbackEvent).delete()
    db.query(MetaAndromedaDriftReport).delete()
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.query(MetaAndromedaBacktestRun).delete()
    db.commit()

def _mark_release_candidate_metrics(db, model_version: str, *, accuracy: float, metrics_source: str = "computed") -> None:
    from database.models.meta_andromeda import MetaAndromedaReleaseRecord

    record = (
        db.query(MetaAndromedaReleaseRecord)
        .filter(
            MetaAndromedaReleaseRecord.record_kind == "candidate",
            MetaAndromedaReleaseRecord.model_version == model_version,
        )
        .first()
    )
    assert record is not None
    record.metrics_source = metrics_source
    record.metrics_sample_count = 10 if metrics_source == "computed" else None
    record.pairwise_ranking_accuracy = accuracy
    record.mean_band_error = 0.2
    db.add(record)
    db.commit()


def _install_internal_worker_httpx_proxy(monkeypatch, db):
    worker_test_app = FastAPI()
    worker_test_app.include_router(meta_andromeda_internal_router)

    def override_get_db():
        yield db

    worker_test_app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=worker_test_app)

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self._client = httpx.AsyncClient(transport=transport, base_url="http://worker.test")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            await self._client.aclose()

        async def get(self, url, params=None, headers=None):
            return await self._client.get("/internal/meta-andromeda/assets/raw", params=params, headers=headers)

        async def post(self, url, data=None, files=None, headers=None):
            return await self._client.post("/internal/meta-andromeda/assets", data=data, files=files, headers=headers)

    monkeypatch.setattr(meta_andromeda_internal_gateway_module.httpx, "AsyncClient", FakeAsyncClient)


from database.models.meta_andromeda import (
    MetaAndromedaBacktestRun,
    MetaAndromedaCalibrationItem,
    MetaAndromedaDriftReport,
    MetaAndromedaObservedCreative,
    MetaAndromedaReleaseRecord,
    MetaAndromedaScoreEvent,
    MetaAndromedaScoringProfile,
)

_ORIGINAL_TEST_ORDER = {
    'test_meta_andromeda_create_backtest_run_queues_isolated_run': 0,
    'test_meta_andromeda_create_backtest_run_rejects_invalid_model': 1,
    'test_meta_andromeda_review_queue_excludes_backtest_scores': 2,
    'test_meta_andromeda_ping_returns_payload': 3,
    'test_meta_andromeda_runtime_health_reports_missing_internal_asset_worker_config_on_web_filesystem': 4,
    'test_meta_andromeda_upload_persists_file_to_storage_root': 5,
    'test_meta_andromeda_upload_supports_s3_compatible_storage': 6,
    'test_meta_andromeda_preview_proxies_filesystem_asset_from_internal_worker': 7,
    'test_meta_andromeda_preview_returns_404_when_internal_worker_returns_404': 8,
    'test_meta_andromeda_internal_asset_route_rejects_missing_auth': 9,
    'test_meta_andromeda_internal_upload_route_rejects_missing_auth': 10,
    'test_meta_andromeda_upload_rejects_empty_file': 11,
    'test_meta_andromeda_upload_rejects_mime_extension_mismatch': 12,
    'test_meta_andromeda_overview_returns_current_integration_state': 13,
    'test_meta_andromeda_monitoring_exposes_worker_host_observability': 14,
    'test_meta_andromeda_monitoring_timeline_returns_event_detail': 15,
    'test_meta_andromeda_drift_trigger_creates_report_and_alert': 16,
    'test_meta_andromeda_drift_accuracy_and_mae_calculation': 17,
    'test_meta_andromeda_drift_matching_by_checksum': 18,
    'test_meta_andromeda_monitoring_summary_does_not_reseed_read_path': 19,
    'test_meta_andromeda_drift_trigger_does_not_persist_mock_scores': 20,
    'test_meta_andromeda_runtime_health_returns_shared_runtime_summary': 21,
    'test_meta_andromeda_score_submit_supports_database_queue_host': 22,
    'test_meta_andromeda_score_submit_supports_external_webhook_queue_host': 23,
    'test_meta_andromeda_external_worker_callback_completes_score': 24,
    'test_meta_andromeda_external_worker_callback_retryable_failure_requeues': 25,
    'test_meta_andromeda_score_submit_supports_redis_stream_queue_host': 26,
    'test_meta_andromeda_redis_stream_consumer_acks_messages': 27,
    'test_meta_andromeda_redis_stream_reclaim_reschedules_stale_pending_messages': 28,
    'test_scheduler_role_flags_resolve_correctly': 29,
    'test_meta_andromeda_release_metrics_refresh_job_registered_daily': 30,
    'test_meta_andromeda_release_metrics_refresh_handles_insufficient_data': 31,
    'test_get_active_host_web_role_never_dispatches_locally': 32,
    'test_meta_andromeda_observation_import_stream_dispatch_and_consume': 33,
    'test_meta_andromeda_import_endpoint_dispatches_to_worker_in_web_role': 34,
    'test_meta_andromeda_review_queue_supports_filters': 35,
    'test_meta_andromeda_review_queue_detail_returns_selected_item': 36,
    'test_meta_andromeda_review_queue_falls_back_to_observed_media_url_for_preview': 37,
    'test_meta_andromeda_feedback_timeline_returns_read_only_entries': 38,
    'test_meta_andromeda_feedback_submit_updates_timeline': 39,
    'test_meta_andromeda_score_submit_queues_then_completes': 40,
    'test_meta_andromeda_score_retries_then_completes': 41,
    'test_meta_andromeda_score_timeout_marks_failed': 42,
    'test_meta_andromeda_asset_prep_does_not_block_event_loop': 43,
    'test_meta_andromeda_release_overview_returns_candidates_and_notes': 44,
    'test_meta_andromeda_release_metric_pairs_mismatch_sort': 45,
    'test_meta_andromeda_release_metric_pairs_score_vs_perf_sort': 46,
    'test_meta_andromeda_release_metric_pairs_empty': 47,
    'test_meta_andromeda_release_approve_updates_history': 48,
    'test_meta_andromeda_release_approve_blocks_uncomputed_candidate': 49,
    'test_meta_andromeda_release_approve_blocks_low_accuracy_candidate': 50,
    'test_meta_andromeda_release_approve_force_requires_note': 51,
    'test_meta_andromeda_release_approve_force_bypasses_gate_and_marks_history': 52,
    'test_meta_andromeda_release_rollback_ignores_accuracy_gate': 53,
    'test_meta_andromeda_create_release_candidate_appears_in_overview': 54,
    'test_meta_andromeda_create_release_candidate_inherits_production_scoring_profile': 55,
    'test_meta_andromeda_create_release_candidate_rejects_duplicate_model_version': 56,
    'test_meta_andromeda_created_candidate_can_be_approved_to_production': 57,
    'test_effective_scoring_status_reports_no_override_when_env_matches_db': 58,
    'test_effective_scoring_status_flags_override_from_env_model': 59,
    'test_validate_candidate_model_reports_ok_for_valid_model': 60,
    'test_validate_candidate_model_reports_not_found': 61,
    'test_validate_candidate_model_flags_missing_image_support_and_narrow_context': 62,
    'test_meta_andromeda_observation_import_accepts_supported_window_contract': 63,
    'test_meta_andromeda_observation_import_rejects_unsupported_window_kind': 64,
    'test_meta_andromeda_facebook_importer_normalizes_ad_row': 65,
    'test_meta_andromeda_observation_import_uses_facebook_importer': 66,
    'test_meta_andromeda_observation_import_persists_asset_and_observed_record': 67,
    'test_meta_andromeda_observation_import_auto_creates_score_event': 68,
    'test_meta_andromeda_observation_import_denies_without_fb_ads_module_access': 69,
    'test_meta_andromeda_observation_import_denies_without_fb_ads_analytics_permission': 70,
    'test_meta_andromeda_observation_import_allows_with_fb_ads_module_and_permission': 71,
    'test_meta_andromeda_observation_import_rejects_disallowed_media_host': 72,
    'test_meta_andromeda_team_user_without_module_access_is_denied_read_only_endpoint': 73,
    'test_meta_andromeda_team_viewer_can_read_overview_with_team_module_access': 74,
    'test_meta_andromeda_team_member_can_submit_feedback_in_team_workspace': 75,
    'test_meta_andromeda_team_member_can_trigger_drift_report_and_approve_release': 76,
    'test_sync_calibration_dataset_endpoint': 77,
    'test_meta_andromeda_monitoring_summary_uses_real_latency_metrics': 78,
    'test_meta_andromeda_heuristic_runtime_uses_lower_score_and_dynamic_confidence': 79,
    'test_meta_andromeda_scheduler_disabled_skips_score_job_registration': 80,
    'test_meta_andromeda_mark_score_processing_claim_is_single_shot': 81,
    'test_meta_andromeda_external_worker_completed_callback_is_idempotent': 82,
    'test_meta_andromeda_external_worker_stale_failed_callback_does_not_override_completed': 83,
    'test_meta_andromeda_openrouter_invalid_schema_falls_back_to_heuristic': 84,
    'test_meta_andromeda_storage_image_is_encoded_and_sent_as_data_uri': 85,
    'test_meta_andromeda_image_auto_compression': 86,
    'test_objective_routing_is_predicted_band_eligible_covers_all_known_groups': 87,
    'test_default_objective_profiles_make_non_roas_groups_band_eligible': 88,
    'test_validate_provider_result_preserves_band_for_non_roas_groups': 89,
    'test_score_to_list_item_includes_objective_group': 90,
    'test_non_roas_objectives_resolve_to_correct_group_and_metric_focus': 91,
    'test_non_roas_group_end_to_end_ai_band_flows_through_to_detail': 92,
    'test_non_roas_group_enters_calibration_dataset_when_band_predicted': 93,
    'test_non_roas_group_enters_drift_report_accuracy_when_band_predicted': 94,
    'test_heuristic_fallback_still_skips_band_for_non_roas_groups': 95,
}


def pytest_collection_modifyitems(items):
    def order_key(item):
        base_name = item.name.split("[")[0]
        return _ORIGINAL_TEST_ORDER.get(base_name, len(_ORIGINAL_TEST_ORDER))

    items.sort(key=order_key)


__all__ = [name for name in globals() if not name.startswith("__")]

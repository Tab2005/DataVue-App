"""ObservationImportServiceMixin for Meta Andromeda service."""

from ._shared import *  # noqa: F403


class ObservationImportServiceMixin:

    @staticmethod
    async def _fetch_observed_facebook_ad_candidate(
        *,
        payload: dict,
        user_id: str,
        team_id: str | None = None,
    ):
        return await fetch_observed_creative_candidate(
            account_id=payload["account_id"],
            ad_id=payload["ad_id"],
            user_id=user_id,
            observation_window_kind=payload["observation_window_kind"],
            market=payload["market"],
            placement_family=payload["placement_family"],
            primary_text=payload.get("primary_text"),
            headline=payload.get("headline"),
            cta=payload.get("cta"),
            team_id=team_id,
            since=payload.get("since"),
            until=payload.get("until"),
        )


    @staticmethod
    def build_observed_creative_id(ad_id: str, observation_window_kind: str) -> str:
        today = datetime.now(UTC).date()
        return f"ma_obs_{today.strftime('%Y%m%d')}_{ad_id[-6:]}_{observation_window_kind}"


    @staticmethod
    def _set_observation_import_status(observed_creative_id: str, **updates) -> dict:
        return set_import_status(observed_creative_id, **updates)


    @staticmethod
    def queue_observed_facebook_ad_import(payload: dict) -> dict:
        observed_creative_id = MetaAndromedaService.build_observed_creative_id(
            payload["ad_id"],
            payload["observation_window_kind"],
        )
        MetaAndromedaService._set_observation_import_status(
            observed_creative_id,
            observation_status="queued",
            observation_message="Observation import queued",
            asset_uri=None,
            score_event_id=None,
            score_status="pending_observation",
            runtime_job_id=None,
        )
        return {
            "observed_creative_id": observed_creative_id,
            "status": "accepted",
            "asset_uri": None,
            "score_event_id": None,
            "score_status": "pending_observation",
            "runtime_job_id": None,
            "source": {
                "platform": "facebook_ads",
                "account_id": payload["account_id"],
                "ad_id": payload["ad_id"],
            },
            "observation_window": {
                "kind": payload["observation_window_kind"],
                "start": payload.get("since") or "",
                "end": payload.get("until") or "",
            },
            "performance_snapshot": {},
        }


    @staticmethod
    async def _download_observed_asset_snapshot(
        *,
        media_url: str,
        ad_id: str,
        media_type: str,
    ) -> dict:
        parsed = urlparse(media_url)
        if parsed.scheme != "https":
            raise MetaAndromedaValidationError("observed_media_url_must_use_https", status_code=400)
        if not MetaAndromedaService._is_allowed_media_host(parsed.hostname):
            raise MetaAndromedaValidationError("observed_media_url_host_not_allowed", status_code=400)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(media_url)
            response.raise_for_status()

        content_type = response.headers.get("content-type", "").split(";")[0].strip() or None
        if len(response.content) > settings.META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES:
            raise MetaAndromedaValidationError("observed_media_too_large", status_code=413)
        if media_type == "image" and content_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise MetaAndromedaValidationError("observed_media_mime_not_allowed", status_code=415)
        if media_type == "video" and content_type not in {"video/mp4", "video/quicktime"}:
            raise MetaAndromedaValidationError("observed_media_mime_not_allowed", status_code=415)
        path_name = Path(parsed.path).name
        if path_name:
            source_filename = path_name
        else:
            extension = guess_extension(content_type or "") if content_type else None
            if not extension:
                extension = ".png" if media_type == "image" else ".mp4" if media_type == "video" else ".bin"
            source_filename = f"{ad_id}{extension}"

        asset_type = media_type if media_type in {"image", "video"} else "image"
        return {
            "file_bytes": response.content,
            "source_filename": source_filename,
            "content_type": content_type,
            "asset_type": asset_type,
        }


    @staticmethod
    def _resolve_observed_uploader_id_sync(db, user_id: str) -> str:
        """同步版本：查詢 User 資料表，將外部 google_id 轉換為內部 User.id（純 DB I/O，見 docs/24 Wave 1）。"""
        db_user = db.query(User).filter(User.google_id == user_id).first()
        return db_user.id if db_user else user_id


    @staticmethod
    def _store_observed_asset_sync(db, snapshot: dict, user_db_id: str) -> dict:
        """同步版本：把下載好的素材位元組寫入儲存後端並登記資產紀錄（檔案/S3 寫入 + DB，見 docs/24 Wave 1）。"""
        asset_record = storage_adapter.store_asset(
            file_bytes=snapshot["file_bytes"],
            asset_type=snapshot["asset_type"],
            source_filename=snapshot["source_filename"],
            uploaded_by=user_db_id,
            content_type=snapshot["content_type"],
        )
        return repository.create_uploaded_asset(db, asset_record=asset_record)


    @staticmethod
    def _create_observed_creative_record_sync(db, observed_record: dict) -> dict:
        """同步版本：寫入觀測素材紀錄（純 DB I/O，見 docs/24 Wave 1）。"""
        return repository.create_observed_creative(db, observed_record=observed_record)


    @staticmethod
    async def import_observed_facebook_ad(
        db,
        payload: dict,
        *,
        user_id: str,
        team_id: str | None = None,
    ) -> dict:
        candidate = await MetaAndromedaService._fetch_observed_facebook_ad_candidate(
            payload=payload,
            user_id=user_id,
            team_id=team_id,
        )
        candidate = ObservedCreativeCandidate.model_validate(candidate)

        observed_creative_id = MetaAndromedaService.build_observed_creative_id(
            candidate.ad_id,
            candidate.observation_window_kind,
        )
        stored_asset = None

        if candidate.media_url and candidate.media_type in {"image", "video"}:
            try:
                snapshot = await MetaAndromedaService._download_observed_asset_snapshot(
                    media_url=candidate.media_url,
                    ad_id=candidate.ad_id,
                    media_type=candidate.media_type,
                )
                # 查詢 User 資料表，將外部 google_id 轉換為內部 User.id (UUID)，防止外鍵約束衝突。
                # 必須放在素材下載「之後」：session 第一次查詢就會 checkout 連線並持有到
                # commit/close，若先查 DB 再下載，整段下載期間（最長 30 秒）都佔住連線池，
                # 批次匯入時會耗盡 QueuePool（2026-07-13 匯入失敗事故）。
                user_db_id = await asyncio.to_thread(
                    MetaAndromedaService._resolve_observed_uploader_id_sync, db, user_id
                )
                stored_asset = await asyncio.to_thread(
                    MetaAndromedaService._store_observed_asset_sync, db, snapshot, user_db_id
                )
            except MetaAndromedaValidationError:
                raise
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"[Observation Import] Failed to download or store asset from {candidate.media_url} for ad_id {candidate.ad_id}: {e}",
                    exc_info=True
                )

        observed_record = await asyncio.to_thread(
            MetaAndromedaService._create_observed_creative_record_sync,
            db,
            {
                "id": observed_creative_id,
                "asset_id": stored_asset["asset_id"] if stored_asset else None,
                "asset_uri": stored_asset["asset_uri"] if stored_asset else None,
                "source_platform": candidate.source_platform,
                "source_account_id": candidate.source_account_id,
                "campaign_id": candidate.campaign_id,
                "adset_id": candidate.adset_id,
                "ad_id": candidate.ad_id,
                "ad_name": candidate.ad_name,
                "objective": candidate.objective,
                "placement_family": candidate.placement_family,
                "market": candidate.market,
                "primary_text": candidate.primary_text,
                "headline": candidate.headline,
                "cta": candidate.cta,
                "media_url": candidate.media_url,
                "media_type": candidate.media_type,
                "performance_snapshot": candidate.performance_snapshot,
                "observation_window_kind": candidate.observation_window_kind,
                "observation_window_start": candidate.observation_window_start,
                "observation_window_end": candidate.observation_window_end,
                "source_fetched_at": candidate.source_fetched_at,
                "lineage": {
                    "source_platform": candidate.source_platform,
                    "source_account_id": candidate.source_account_id,
                    "campaign_id": candidate.campaign_id,
                    "adset_id": candidate.adset_id,
                    "ad_id": candidate.ad_id,
                    "objective_group": resolve_objective_group(candidate.objective),
                },
            },
        )

        score_event_id = None
        score_status = "skipped_no_asset"
        runtime_job_id = None
        auto_score_payload = None

        if observed_record.get("asset_uri") and observed_record.get("asset_id") and observed_record.get("media_type") in {"image", "video"}:
            score_status = "queued_background"
            auto_score_payload = {
                "asset_uri": observed_record["asset_uri"],
                "asset_type": observed_record["media_type"],
                "asset_id": observed_record["asset_id"],
                "request_mode": "auto",
                "objective": observed_record.get("objective") or "purchase",
                "placement_family": observed_record.get("placement_family") or "all",
                "market": observed_record.get("market") or "TW",
                "primary_text": observed_record.get("primary_text"),
                "headline": observed_record.get("headline"),
                "cta": observed_record.get("cta"),
                "observed_creative_id": observed_record["observed_creative_id"],
            }

        return {
            "observed_creative_id": observed_record["observed_creative_id"],
            "status": "accepted",
            "asset_uri": observed_record["asset_uri"],
            "score_event_id": score_event_id,
            "score_status": score_status,
            "runtime_job_id": runtime_job_id,
            "source": {
                "platform": candidate.source_platform,
                "account_id": candidate.source_account_id,
                "ad_id": candidate.ad_id,
            },
            "observation_window": {
                "kind": candidate.observation_window_kind,
                "start": candidate.observation_window_start,
                "end": candidate.observation_window_end,
            },
            "performance_snapshot": candidate.performance_snapshot,
            "_auto_score_payload": auto_score_payload,
        }


    @staticmethod
    def _prepare_score_event_for_observation_sync(auto_score_payload: dict):
        """同步版本：判斷並準備觀測匯入後的自動評分事件（純 DB/Redis I/O，見 docs/24 Wave 1）。

        回傳 ("linked", result)：重用既有已完成評分，DB 寫入與狀態更新已全部完成，
        呼叫端直接回傳 result 即可。
        回傳 ("need_dispatch", info)：呼叫端需留在有運作中 event loop 的執行緒上呼叫
        MetaAndromedaService.enqueue_score_event() 完成實際派工——該呼叫在
        local_async fallback 時會用到 asyncio.create_task()，不能丟進 to_thread。
        回傳 ("error", None)：建立評分事件失敗，狀態已標記為 failed，呼叫端直接回傳 None。
        """
        from database.models.meta_andromeda import MetaAndromedaScoreEvent as _ScoreEvent
        from sqlalchemy.orm.attributes import flag_modified

        db = SessionLocal()
        observed_creative_id = auto_score_payload.get("observed_creative_id") or "unknown_observation"
        asset_uri = auto_score_payload.get("asset_uri")
        try:
            # 同一素材可能在多個觀測窗口（last_7d/last_30d/lifetime）各匯入一次；只要該素材已有
            # 「AI 模式、completed」的最新評分就重用，不必每個窗口都重新呼叫 AI 評一次分。
            # request_context.observed_creative_id 保留原本第一個連結的觀測（相容現有單值查詢），
            # 完整的多對一關聯改記在 lineage.linked_observation_ids（新增、不影響既有查詢）。
            existing = None
            if asset_uri:
                existing = (
                    db.query(_ScoreEvent)
                    .filter(
                        _ScoreEvent.asset_uri == asset_uri,
                        _ScoreEvent.status == "completed",
                    )
                    .order_by(_ScoreEvent.completed_at.desc())
                    .all()
                )
                existing = next(
                    (evt for evt in existing if (evt.lineage or {}).get("scoring_mode") == "ai"),
                    None,
                )

            if existing:
                rc = dict(existing.request_context or {})
                rc.setdefault("observed_creative_id", observed_creative_id)

                lineage = dict(existing.lineage or {})
                linked_ids = list(lineage.get("linked_observation_ids") or [])
                if observed_creative_id not in linked_ids:
                    linked_ids.append(observed_creative_id)
                lineage["linked_observation_ids"] = linked_ids
                existing.lineage = lineage
                existing.request_context = rc
                flag_modified(existing, "request_context")
                flag_modified(existing, "lineage")
                db.commit()
                MetaAndromedaService._set_observation_import_status(
                    observed_creative_id,
                    score_event_id=existing.id,
                    score_status="completed",
                    runtime_job_id=existing.runtime_job_id,
                )
                logger.info(
                    "[Observation Import] Linked existing score event %s → observed_creative_id %s (skipped re-score, now linked to %d observations)",
                    existing.id,
                    observed_creative_id,
                    len(linked_ids),
                )
                return "linked", {"score_event_id": existing.id, "status": "completed"}

            # 無既有預評，正常建立並排入評分
            payload = {
                key: value
                for key, value in auto_score_payload.items()
                if key != "observed_creative_id"
            }
            payload.setdefault("request_context", {})
            payload["request_context"]["observed_creative_id"] = observed_creative_id
            payload["request_context"]["origin"] = "analytics"
            created_score = MetaAndromedaService.create_score_event(db, payload)
            score_event_id = created_score["score_event_id"]
            runtime_job_id = get_meta_andromeda_score_job_id(score_event_id)
            MetaAndromedaService.assign_score_runtime_job(db, score_event_id, runtime_job_id)
            return "need_dispatch", {
                "observed_creative_id": observed_creative_id,
                "score_event_id": score_event_id,
                "runtime_job_id": runtime_job_id,
            }
        except Exception as exc:
            logger.warning(
                "[Observation Import] Background auto score-event creation failed for observed_creative_id %s: %s",
                observed_creative_id,
                exc,
                exc_info=True,
            )
            MetaAndromedaService._set_observation_import_status(
                observed_creative_id,
                score_status="failed",
                observation_message=str(exc),
            )
            return "error", None
        finally:
            db.close()


    @staticmethod
    async def create_and_enqueue_score_event_for_observation(auto_score_payload: dict | None) -> dict | None:
        if not auto_score_payload:
            return None

        kind, payload = await asyncio.to_thread(
            MetaAndromedaService._prepare_score_event_for_observation_sync, auto_score_payload
        )
        if kind != "need_dispatch":
            return payload

        observed_creative_id = payload["observed_creative_id"]
        score_event_id = payload["score_event_id"]
        runtime_job_id = payload["runtime_job_id"]

        db = SessionLocal()
        try:
            queued_score = MetaAndromedaService.enqueue_score_event(
                db,
                score_event_id=score_event_id,
                runtime_job_id=runtime_job_id,
            )
        finally:
            db.close()

        logger.info(
            "[Observation Import] Background auto score-event queued for observed_creative_id %s: %s",
            observed_creative_id,
            score_event_id,
        )
        await asyncio.to_thread(
            MetaAndromedaService._set_observation_import_status,
            observed_creative_id,
            score_event_id=score_event_id,
            score_status=queued_score.get("status") or "queued",
            runtime_job_id=queued_score.get("runtime_job_id") or runtime_job_id,
        )
        return queued_score


    @staticmethod
    def dispatch_observed_facebook_ad_import(payload: dict, *, user_id: str, team_id: str | None) -> bool:
        """docs/24 Wave 2：web 角色下把觀測匯入 job 經 Redis stream 派給獨立
        worker process，讓匯入負載完全離開 web process（Wave 1 的 to_thread
        化已確保就算留在本地也不會卡住 event loop，但資源仍會佔用 web）。

        回傳 True 代表已成功派工給 worker，呼叫端（router）不需要再自己執行；
        回傳 False 代表未派工（非 web 角色，或 web 角色但 Redis 不可用），
        呼叫端應退回在本 process 用 BackgroundTasks 執行。
        """
        if settings.SERVICE_ROLE != "web":
            return False

        dispatch = queue_host_adapter.enqueue_observation_import_event(
            payload, user_id=user_id, team_id=team_id
        )
        return bool(dispatch.get("accepted"))


    @staticmethod
    async def run_observed_facebook_ad_import_job(payload: dict, *, user_id: str, team_id: str | None = None) -> None:
        observed_creative_id = MetaAndromedaService.build_observed_creative_id(
            payload["ad_id"],
            payload["observation_window_kind"],
        )
        await asyncio.to_thread(
            MetaAndromedaService._set_observation_import_status,
            observed_creative_id,
            observation_status="queued",
            observation_message="Observation import queued, waiting for concurrency slot",
            score_status="pending_observation",
        )

        async with _observation_import_semaphore.acquire():
            await asyncio.to_thread(
                MetaAndromedaService._set_observation_import_status,
                observed_creative_id,
                observation_status="processing",
                observation_message="Observation import processing",
                score_status="pending_observation",
            )
            db = SessionLocal()
            try:
                response = await MetaAndromedaService.import_observed_facebook_ad(
                    db,
                    payload,
                    user_id=user_id,
                    team_id=team_id,
                )
                auto_score_payload = response.pop("_auto_score_payload", None)
                await asyncio.to_thread(
                    MetaAndromedaService._set_observation_import_status,
                    observed_creative_id,
                    observation_status="completed",
                    observation_message="Observation imported",
                    asset_uri=response.get("asset_uri"),
                    score_status=response.get("score_status"),
                    runtime_job_id=response.get("runtime_job_id"),
                    score_event_id=response.get("score_event_id"),
                )
                if auto_score_payload:
                    await MetaAndromedaService.create_and_enqueue_score_event_for_observation(auto_score_payload)
                elif response.get("score_status") == "skipped_no_asset":
                    await asyncio.to_thread(
                        MetaAndromedaService._set_observation_import_status,
                        observed_creative_id,
                        score_status="skipped_no_asset",
                    )
            except Exception as exc:
                logger.warning(
                    "[Observation Import] Background observation import failed for %s: %s",
                    observed_creative_id,
                    exc,
                    exc_info=True,
                )
                await asyncio.to_thread(
                    MetaAndromedaService._set_observation_import_status,
                    observed_creative_id,
                    observation_status="failed",
                    observation_message=str(exc),
                    score_status="blocked_by_observation_failure",
                )
            finally:
                db.close()


    @staticmethod
    def get_observed_facebook_ad_import_status(db, observed_creative_id: str) -> dict:
        observed = repository.get_observed_creative(db, observed_creative_id)
        memory_status = get_import_status(observed_creative_id)
        if observed is None:
            if memory_status:
                return {
                    "observed_creative_id": observed_creative_id,
                    "observation_status": memory_status.get("observation_status", "queued"),
                    "observation_message": memory_status.get("observation_message"),
                    "asset_uri": memory_status.get("asset_uri"),
                    "score_event_id": memory_status.get("score_event_id"),
                    "score_status": memory_status.get("score_status"),
                    "runtime_job_id": memory_status.get("runtime_job_id"),
                    "updated_at": memory_status.get("updated_at"),
                }
            return {
                "observed_creative_id": observed_creative_id,
                "observation_status": "not_found",
                "observation_message": "Observation import not found",
                "asset_uri": None,
                "score_event_id": None,
                "score_status": None,
                "runtime_job_id": None,
                "updated_at": None,
            }

        latest_score = repository.get_latest_score_event_for_observation(db, observed_creative_id)
        memory_score_status = memory_status.get("score_status")
        if latest_score:
            score_status = latest_score.get("status")
            score_event_id = latest_score.get("score_event_id")
            runtime_job_id = latest_score.get("runtime_job_id")
        else:
            score_status = memory_score_status or ("pending_score_event" if observed.get("asset_uri") else "skipped_no_asset")
            score_event_id = memory_status.get("score_event_id")
            runtime_job_id = memory_status.get("runtime_job_id")

        return {
            "observed_creative_id": observed_creative_id,
            "observation_status": "completed",
            "observation_message": memory_status.get("observation_message") or "Observation imported",
            "asset_uri": observed.get("asset_uri"),
            "score_event_id": score_event_id,
            "score_status": score_status,
            "runtime_job_id": runtime_job_id,
            "updated_at": memory_status.get("updated_at") or observed.get("created_at"),
        }

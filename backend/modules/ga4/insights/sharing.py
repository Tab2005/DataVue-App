"""Snapshot share-link helpers for GA4 insights (docs/39)."""

from __future__ import annotations

from ._shared import *


def create_share_link(db, *, snapshot_id: str):
    return repository.get_or_create_share_token(db, snapshot_id=snapshot_id)


def get_snapshot_by_share_token(db, token: str):
    return repository.get_snapshot_by_share_token(db, token)

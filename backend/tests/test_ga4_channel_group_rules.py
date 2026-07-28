"""GA4 渠道值自訂分組規則驗證（docs/44 步驟 1-2）。"""

import pytest


@pytest.mark.unit
def test_repository_list_channel_group_rules_ordered_by_priority(db, sample_user):
    from modules.ga4.repository import repository

    repository.create_channel_group_rule(
        db, property_id="123456", channel_dimension="source_medium",
        group_label="Facebook Ads", match_type="contains", pattern="facebook / cpc",
        priority=5, created_by=sample_user.id,
    )
    repository.create_channel_group_rule(
        db, property_id="123456", channel_dimension="source_medium",
        group_label="Facebook Ads", match_type="prefix", pattern="facebook / post-ads",
        priority=1, created_by=sample_user.id,
    )
    db.commit()

    rules = repository.list_channel_group_rules(db, property_id="123456")
    assert [r.pattern for r in rules] == ["facebook / post-ads", "facebook / cpc"]


@pytest.mark.unit
def test_repository_list_channel_group_rules_filters_by_dimension(db, sample_user):
    from modules.ga4.repository import repository

    repository.create_channel_group_rule(
        db, property_id="123456", channel_dimension="source_medium",
        group_label="Facebook Ads", match_type="contains", pattern="facebook",
        priority=0, created_by=sample_user.id,
    )
    repository.create_channel_group_rule(
        db, property_id="123456", channel_dimension="source",
        group_label="Facebook (all)", match_type="exact", pattern="facebook",
        priority=0, created_by=sample_user.id,
    )
    db.commit()

    source_medium_rules = repository.list_channel_group_rules(db, property_id="123456", channel_dimension="source_medium")
    assert len(source_medium_rules) == 1
    assert source_medium_rules[0].channel_dimension == "source_medium"


@pytest.mark.unit
def test_service_upsert_channel_group_rule_create_then_update(db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    created = GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="contains", pattern="facebook / cpc", priority=1,
    )
    db.commit()

    updated = GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=created.id, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads (paid)",
        match_type="prefix", pattern="facebook / post", priority=2,
    )
    db.commit()

    assert updated.id == created.id
    assert updated.group_label == "Facebook Ads (paid)"
    assert updated.match_type == "prefix"
    assert updated.priority == 2

    missing = GA4InsightsService.upsert_channel_group_rule(
        db, rule_id="does-not-exist", user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="x", match_type="prefix", pattern="x", priority=0,
    )
    assert missing is None


@pytest.mark.unit
def test_upsert_channel_group_rule_rejects_unknown_dimension(db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    with pytest.raises(ValueError):
        GA4InsightsService.upsert_channel_group_rule(
            db, rule_id=None, user_id=sample_user.id, property_id="123456",
            channel_dimension="not_a_real_dimension", group_label="x",
            match_type="prefix", pattern="x", priority=0,
        )


@pytest.mark.unit
def test_upsert_channel_group_rule_rejects_unknown_match_type(db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    with pytest.raises(ValueError):
        GA4InsightsService.upsert_channel_group_rule(
            db, rule_id=None, user_id=sample_user.id, property_id="123456",
            channel_dimension="source_medium", group_label="x",
            match_type="regex", pattern="x", priority=0,
        )


@pytest.mark.unit
def test_delete_channel_group_rule(db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    created = GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="contains", pattern="facebook", priority=0,
    )
    db.commit()

    assert GA4InsightsService.delete_channel_group_rule(db, rule_id=created.id) is True
    db.commit()
    assert GA4InsightsService.delete_channel_group_rule(db, rule_id=created.id) is False


@pytest.mark.unit
def test_list_channel_groups_deduplicates_by_label_and_counts_rules(db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="contains", pattern="facebook / cpc", priority=0,
    )
    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="contains", pattern="facebook / post-ads", priority=1,
    )
    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Google Ads",
        match_type="contains", pattern="google / cpc", priority=0,
    )
    db.commit()

    groups = GA4InsightsService.list_channel_groups(db, property_id="123456", channel_dimension="source_medium")
    assert groups == [
        {"group_label": "Facebook Ads", "rule_count": 2},
        {"group_label": "Google Ads", "rule_count": 1},
    ]


@pytest.mark.unit
def test_get_channel_group_match_conditions(db, sample_user):
    """同一分組底下多條規則全部都要生效（OR），不是只取第一條比對成功的。"""
    from modules.ga4.insights_service import GA4InsightsService

    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="contains", pattern="facebook / cpc", priority=0,
    )
    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="prefix", pattern="facebook / post", priority=1,
    )
    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Google Ads",
        match_type="contains", pattern="google / cpc", priority=0,
    )
    db.commit()

    conditions = GA4InsightsService.get_channel_group_match_conditions(
        db, property_id="123456", channel_dimension="source_medium", group_label="Facebook Ads",
    )
    assert set(conditions) == {("contains", "facebook / cpc"), ("prefix", "facebook / post")}

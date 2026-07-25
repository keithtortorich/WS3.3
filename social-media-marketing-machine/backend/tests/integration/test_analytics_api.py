"""Integration tests for the analytics API: immutable snapshot ingestion,
the campaign summary, and the weekly KPI rollup — against the real FastAPI
app wired to an in-memory SQLite DB (get_db / auth overridden)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from app.models.analytics import Analytics
from app.models.campaign import Campaign
from app.models.client import Client
from app.models.organization import Organization
from app.models.post import Post

# 2026-01-05 is a Monday; 2026-01-11 the Sunday that closes the same ISO week.
WEEK_A = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
WEEK_A_SUNDAY = datetime(2026, 1, 11, 23, 0, tzinfo=timezone.utc)
WEEK_B = datetime(2026, 1, 12, 9, 0, tzinfo=timezone.utc)


async def _seed_org(db_session, org_id: uuid.UUID) -> uuid.UUID:
    """Create org + client + campaign, returning the campaign id."""
    org = Organization(id=org_id, name=f"Org {org_id.hex[:6]}", slug=f"org-{org_id.hex[:8]}")
    db_session.add(org)
    await db_session.flush()

    client_row = Client(organization_id=org_id, name="Client")
    db_session.add(client_row)
    await db_session.flush()

    campaign = Campaign(organization_id=org_id, client_id=client_row.id, name="Campaign")
    db_session.add(campaign)
    await db_session.commit()
    return campaign.id


async def _seed_post(db_session, org_id: uuid.UUID, campaign_id: uuid.UUID) -> uuid.UUID:
    post = Post(
        organization_id=org_id,
        campaign_id=campaign_id,
        platform="instagram",
        caption="hello",
    )
    db_session.add(post)
    await db_session.commit()
    return post.id


async def _seed_snapshot(
    db_session,
    org_id: uuid.UUID,
    post_id: uuid.UUID,
    captured_at: datetime,
    *,
    impressions: int,
    likes: int,
    comments: int,
    shares: int,
    clicks: int,
) -> None:
    db_session.add(
        Analytics(
            organization_id=org_id,
            post_id=post_id,
            captured_at=captured_at,
            impressions=impressions,
            likes=likes,
            comments_count=comments,
            shares=shares,
            clicks=clicks,
        )
    )
    await db_session.commit()


async def _analytics_row_count(db_session) -> int:
    return (await db_session.execute(select(func.count()).select_from(Analytics))).scalar_one()


# ----------------------------------------------------------------------
# Snapshot ingestion
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_snapshot_and_read_it_back(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_org(db_session, TEST_ORG_ID)
    post_id = await _seed_post(db_session, TEST_ORG_ID, campaign_id)

    payload = {
        "post_id": str(post_id),
        "captured_at": WEEK_A.isoformat(),
        "impressions": 1000,
        "likes": 100,
        "comments_count": 10,
        "shares": 5,
        "clicks": 20,
    }
    create_response = await client.post("/api/v1/analytics", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["post_id"] == str(post_id)
    assert created["impressions"] == 1000

    list_response = await client.get(f"/api/v1/analytics?post_id={post_id}")
    assert list_response.status_code == 200
    page = list_response.json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == created["id"]
    assert page["items"][0]["likes"] == 100


@pytest.mark.asyncio
async def test_duplicate_snapshot_is_rejected_and_creates_no_row(client, db_session):
    """Snapshots are immutable: same (post, captured_at) => 409, one row."""
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_org(db_session, TEST_ORG_ID)
    post_id = await _seed_post(db_session, TEST_ORG_ID, campaign_id)

    payload = {
        "post_id": str(post_id),
        "captured_at": WEEK_A.isoformat(),
        "impressions": 1000,
        "likes": 100,
    }
    first = await client.post("/api/v1/analytics", json=payload)
    assert first.status_code == 201, first.text

    # Same natural key, different metrics — must not overwrite history.
    duplicate = dict(payload, impressions=9999, likes=1)
    second = await client.post("/api/v1/analytics", json=duplicate)
    assert second.status_code == 409, second.text
    assert second.json()["error"] == "ConflictError"

    assert await _analytics_row_count(db_session) == 1
    stored = (await db_session.execute(select(Analytics))).scalar_one()
    assert stored.impressions == 1000  # original preserved, not overwritten
    assert stored.likes == 100


@pytest.mark.asyncio
async def test_same_post_different_capture_time_is_a_new_snapshot(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_org(db_session, TEST_ORG_ID)
    post_id = await _seed_post(db_session, TEST_ORG_ID, campaign_id)

    for captured_at in (WEEK_A, WEEK_B):
        response = await client.post(
            "/api/v1/analytics",
            json={
                "post_id": str(post_id),
                "captured_at": captured_at.isoformat(),
                "impressions": 10,
            },
        )
        assert response.status_code == 201, response.text

    assert await _analytics_row_count(db_session) == 2


# ----------------------------------------------------------------------
# Weekly rollup
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_weekly_rollup_arithmetic_across_posts_and_weeks(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_org(db_session, TEST_ORG_ID)
    post_a = await _seed_post(db_session, TEST_ORG_ID, campaign_id)
    post_b = await _seed_post(db_session, TEST_ORG_ID, campaign_id)

    # Week of 2026-01-05: two posts, two snapshots.
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_a, WEEK_A,
        impressions=1000, likes=100, comments=10, shares=5, clicks=20,
    )
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_b, WEEK_A_SUNDAY,
        impressions=500, likes=50, comments=5, shares=0, clicks=10,
    )
    # Week of 2026-01-12: one post, one snapshot.
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_a, WEEK_B,
        impressions=200, likes=20, comments=2, shares=1, clicks=3,
    )

    response = await client.get(f"/api/v1/analytics/campaigns/{campaign_id}/weekly")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["campaign_id"] == str(campaign_id)
    weeks = body["weeks"]
    assert [w["week_start"] for w in weeks] == ["2026-01-05", "2026-01-12"]

    first = weeks[0]
    assert first["post_count"] == 2
    assert first["impressions"] == 1500
    assert first["likes"] == 150
    assert first["comments"] == 15
    assert first["shares"] == 5
    assert first["clicks"] == 30
    # (150 + 15 + 5) / 1500
    assert first["engagement_rate"] == pytest.approx(170 / 1500)

    second = weeks[1]
    assert second["post_count"] == 1
    assert second["impressions"] == 200
    assert second["likes"] == 20
    assert second["comments"] == 2
    assert second["shares"] == 1
    assert second["clicks"] == 3
    assert second["engagement_rate"] == pytest.approx(23 / 200)


@pytest.mark.asyncio
async def test_weekly_rollup_respects_date_range(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_org(db_session, TEST_ORG_ID)
    post_id = await _seed_post(db_session, TEST_ORG_ID, campaign_id)
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_id, WEEK_A,
        impressions=1000, likes=100, comments=10, shares=5, clicks=20,
    )
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_id, WEEK_B,
        impressions=200, likes=20, comments=2, shares=1, clicks=3,
    )

    # end_date is inclusive: 2026-01-11 keeps week A, drops week B.
    response = await client.get(
        f"/api/v1/analytics/campaigns/{campaign_id}/weekly"
        "?start_date=2026-01-05&end_date=2026-01-11"
    )
    assert response.status_code == 200, response.text
    weeks = response.json()["weeks"]
    assert len(weeks) == 1
    assert weeks[0]["week_start"] == "2026-01-05"
    assert weeks[0]["impressions"] == 1000


@pytest.mark.asyncio
async def test_weekly_rollup_empty_range_returns_empty_list_not_error(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_org(db_session, TEST_ORG_ID)
    post_id = await _seed_post(db_session, TEST_ORG_ID, campaign_id)
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_id, WEEK_A,
        impressions=1000, likes=100, comments=10, shares=5, clicks=20,
    )

    response = await client.get(
        f"/api/v1/analytics/campaigns/{campaign_id}/weekly"
        "?start_date=2030-01-01&end_date=2030-01-31"
    )
    assert response.status_code == 200, response.text
    assert response.json()["weeks"] == []


@pytest.mark.asyncio
async def test_weekly_rollup_zero_impressions_yields_null_engagement_rate(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_org(db_session, TEST_ORG_ID)
    post_id = await _seed_post(db_session, TEST_ORG_ID, campaign_id)
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_id, WEEK_A,
        impressions=0, likes=0, comments=0, shares=0, clicks=0,
    )

    response = await client.get(f"/api/v1/analytics/campaigns/{campaign_id}/weekly")
    assert response.status_code == 200, response.text
    weeks = response.json()["weeks"]
    assert len(weeks) == 1
    assert weeks[0]["engagement_rate"] is None


@pytest.mark.asyncio
async def test_weekly_rollup_unknown_campaign_returns_404(client, db_session):
    from tests.conftest import TEST_ORG_ID

    await _seed_org(db_session, TEST_ORG_ID)
    response = await client.get(f"/api/v1/analytics/campaigns/{uuid.uuid4()}/weekly")
    assert response.status_code == 404
    assert response.json()["error"] == "NotFoundError"


# ----------------------------------------------------------------------
# Campaign summary
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_campaign_summary_totals(client, db_session):
    from tests.conftest import TEST_ORG_ID

    campaign_id = await _seed_org(db_session, TEST_ORG_ID)
    post_a = await _seed_post(db_session, TEST_ORG_ID, campaign_id)
    post_b = await _seed_post(db_session, TEST_ORG_ID, campaign_id)
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_a, WEEK_A,
        impressions=1000, likes=100, comments=10, shares=5, clicks=20,
    )
    await _seed_snapshot(
        db_session, TEST_ORG_ID, post_b, WEEK_B,
        impressions=200, likes=20, comments=2, shares=1, clicks=3,
    )

    response = await client.get(f"/api/v1/analytics/campaigns/{campaign_id}/summary")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_posts"] == 2
    assert body["total_impressions"] == 1200
    assert body["total_likes"] == 120
    assert body["total_comments"] == 12
    assert body["total_shares"] == 6
    assert body["total_clicks"] == 23


# ----------------------------------------------------------------------
# Cross-tenant isolation
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rollup_and_summary_never_include_another_orgs_rows(client, db_session):
    """Org B rows attached to org A's campaign/post must never be counted.

    This deliberately constructs the *leak* shape a forgotten filter would
    expose: an org-B Post pointing at org A's campaign, and an org-B
    Analytics row pointing at org A's Post.
    """
    from tests.conftest import TEST_ORG_ID

    org_a_campaign = await _seed_org(db_session, TEST_ORG_ID)
    org_a_post = await _seed_post(db_session, TEST_ORG_ID, org_a_campaign)
    await _seed_snapshot(
        db_session, TEST_ORG_ID, org_a_post, WEEK_A,
        impressions=1000, likes=100, comments=10, shares=5, clicks=20,
    )

    org_b_id = uuid.uuid4()
    await _seed_org(db_session, org_b_id)
    # Org B post hanging off org A's campaign.
    org_b_post = await _seed_post(db_session, org_b_id, org_a_campaign)
    await _seed_snapshot(
        db_session, org_b_id, org_b_post, WEEK_A,
        impressions=777_000, likes=777, comments=77, shares=7, clicks=7,
    )
    # Org B analytics row hanging off org A's post.
    await _seed_snapshot(
        db_session, org_b_id, org_a_post, WEEK_B,
        impressions=999_000, likes=999, comments=99, shares=9, clicks=9,
    )

    rollup = await client.get(f"/api/v1/analytics/campaigns/{org_a_campaign}/weekly")
    assert rollup.status_code == 200, rollup.text
    weeks = rollup.json()["weeks"]
    assert len(weeks) == 1
    assert weeks[0]["week_start"] == "2026-01-05"
    assert weeks[0]["post_count"] == 1
    assert weeks[0]["impressions"] == 1000
    assert weeks[0]["likes"] == 100

    summary = await client.get(f"/api/v1/analytics/campaigns/{org_a_campaign}/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["total_posts"] == 1
    assert body["total_impressions"] == 1000

    listing = await client.get("/api/v1/analytics")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

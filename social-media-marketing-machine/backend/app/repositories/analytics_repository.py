"""Analytics repository: immutable snapshot ingestion + KPI aggregation.

Two things live here that are deliberately NOT in the router:

1. **Duplicate-snapshot policy.** Analytics rows are immutable time-series
   points. The natural key is ``(organization_id, post_id, captured_at)``.
   Re-ingesting the same natural key is *rejected* (409) rather than
   upserted — see :meth:`AnalyticsRepository.create_snapshot`.

2. **Aggregation.** All KPI queries are ORM ``select()`` statements that
   aggregate in the database (``func.sum`` / ``func.count``), never by
   loading rows into Python. Every one of them filters on
   ``organization_id`` on *each* joined tenant-scoped table, not just the
   entry point — see ``app/repositories/base.py`` for the rationale.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, NamedTuple, Optional, Sequence

from sqlalchemy import Float, cast, func, select
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.core.sql_functions import week_start
from app.models.analytics import Analytics
from app.models.campaign import Campaign
from app.models.post import Post
from app.repositories.base import OrgScopedRepository


class CampaignSummaryRow(NamedTuple):
    """Aggregate totals across every analytics snapshot of a campaign."""

    total_posts: int
    total_impressions: int
    total_likes: int
    total_comments: int
    total_shares: int
    total_clicks: int
    average_engagement_rate: Optional[float]


class WeeklyKPIRow(NamedTuple):
    """One (campaign, week) bucket of the weekly KPI rollup."""

    week_start: date
    post_count: int
    impressions: int
    likes: int
    comments: int
    shares: int
    clicks: int
    engagement_rate: Optional[float]


def _as_date(value: Any) -> date:
    """Normalize a week-bucket value to ``datetime.date``.

    PostgreSQL returns a real ``date``. SQLite's ``DATE()`` returns a
    ``'YYYY-MM-DD'`` string, which SQLAlchemy's SQLite DATE result
    processor normally converts — this is a belt-and-braces fallback so a
    dialect quirk can never leak a raw string into a Pydantic response.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


class AnalyticsRepository(OrgScopedRepository[Analytics]):
    model = Analytics

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    async def get_by_natural_key(
        self, organization_id: uuid.UUID, post_id: uuid.UUID, captured_at: datetime
    ) -> Optional[Analytics]:
        """Look up an existing snapshot by its natural key."""
        stmt = select(Analytics).where(
            Analytics.organization_id == organization_id,
            Analytics.post_id == post_id,
            Analytics.captured_at == captured_at,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_snapshot(self, snapshot: Analytics) -> Analytics:
        """Insert an immutable snapshot, rejecting a duplicate natural key.

        REJECT rather than UPSERT, deliberately: an analytics row is a
        historical observation, and silently overwriting one would destroy
        history that a trend chart depends on — the exact thing the model's
        own docstring says snapshots exist to preserve. A re-delivered
        poller payload is a no-op the caller should know about (409), not a
        rewrite of the past.

        Two layers, because the pre-check alone is a read-then-write race:
        two concurrent pollers can both find nothing and both insert. The
        ``uq_analytics_org_post_captured`` constraint (migration
        ``e00c25c0041f``) is the authority; the pre-check exists only so the
        common case returns a useful 409 without burning a failed INSERT.
        """
        existing = await self.get_by_natural_key(
            snapshot.organization_id, snapshot.post_id, snapshot.captured_at
        )
        if existing is not None:
            raise self._duplicate_error(snapshot, existing_id=existing.id)

        # The race window between the check above and this insert is closed by
        # the unique constraint, not by the check.
        try:
            async with self.session.begin_nested():
                return await self.create(snapshot)
        except IntegrityError as exc:
            if not self._is_natural_key_violation(exc):
                raise
            raise self._duplicate_error(snapshot) from exc

    @staticmethod
    def _is_natural_key_violation(exc: IntegrityError) -> bool:
        """True only for the analytics natural-key constraint.

        Matched by name so an unrelated integrity error (a bad FK, say) still
        surfaces as itself rather than being mislabeled a duplicate snapshot.
        """
        return "uq_analytics_org_post_captured" in str(exc.orig)

    @staticmethod
    def _duplicate_error(
        snapshot: Analytics, existing_id: uuid.UUID | None = None
    ) -> ConflictError:
        details = {
            "post_id": str(snapshot.post_id),
            "captured_at": snapshot.captured_at.isoformat(),
        }
        if existing_id is not None:
            details["existing_id"] = str(existing_id)
        return ConflictError(
            "An analytics snapshot already exists for this post at this "
            "capture time; snapshots are immutable and are not overwritten.",
            details=details,
        )

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    async def campaign_summary(
        self, organization_id: uuid.UUID, campaign_id: uuid.UUID
    ) -> CampaignSummaryRow:
        """All-time totals for one campaign, aggregated in the database."""
        stmt = (
            select(
                func.count(func.distinct(Post.id)),
                func.coalesce(func.sum(Analytics.impressions), 0),
                func.coalesce(func.sum(Analytics.likes), 0),
                func.coalesce(func.sum(Analytics.comments_count), 0),
                func.coalesce(func.sum(Analytics.shares), 0),
                func.coalesce(func.sum(Analytics.clicks), 0),
                func.avg(Analytics.engagement_rate),
            )
            .select_from(Post)
            .outerjoin(
                Analytics,
                (Analytics.post_id == Post.id)
                & (Analytics.organization_id == organization_id),
            )
            .where(
                Post.campaign_id == campaign_id,
                Post.organization_id == organization_id,
            )
        )
        row = (await self.session.execute(stmt)).one()
        return CampaignSummaryRow(
            total_posts=row[0] or 0,
            total_impressions=int(row[1] or 0),
            total_likes=int(row[2] or 0),
            total_comments=int(row[3] or 0),
            total_shares=int(row[4] or 0),
            total_clicks=int(row[5] or 0),
            average_engagement_rate=float(row[6]) if row[6] is not None else None,
        )

    async def weekly_rollup(
        self,
        organization_id: uuid.UUID,
        campaign_id: uuid.UUID,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Sequence[WeeklyKPIRow]:
        """Per-week KPI rollup for a campaign (``smm_gtm_bridge.sql`` 4b).

        ``start``/``end`` bound ``captured_at`` half-openly
        (``start <= captured_at < end``) so adjacent ranges never
        double-count a boundary snapshot.

        ``engagement_rate`` is *derived* from the aggregated counters
        (``(likes + comments + shares) / impressions``) rather than
        averaging the per-snapshot ``engagement_rate`` column: averaging
        pre-computed ratios across posts of wildly different reach is
        arithmetically meaningless. NULL when the bucket has no
        impressions. The division is cast to FLOAT because SQLite would
        otherwise do integer division on two integer SUMs.
        """
        bucket = week_start(Analytics.captured_at).label("week_start")

        impressions = func.coalesce(func.sum(Analytics.impressions), 0)
        likes = func.coalesce(func.sum(Analytics.likes), 0)
        comments = func.coalesce(func.sum(Analytics.comments_count), 0)
        shares = func.coalesce(func.sum(Analytics.shares), 0)
        clicks = func.coalesce(func.sum(Analytics.clicks), 0)

        filters = [
            Campaign.id == campaign_id,
            Campaign.organization_id == organization_id,
            Post.organization_id == organization_id,
            Analytics.organization_id == organization_id,
        ]
        if start is not None:
            filters.append(Analytics.captured_at >= start)
        if end is not None:
            filters.append(Analytics.captured_at < end)

        stmt = (
            select(
                bucket,
                func.count(func.distinct(Post.id)),
                impressions,
                likes,
                comments,
                shares,
                clicks,
                cast(likes + comments + shares, Float) / func.nullif(impressions, 0),
            )
            .select_from(Campaign)
            .join(Post, Post.campaign_id == Campaign.id)
            .join(Analytics, Analytics.post_id == Post.id)
            .where(*filters)
            .group_by(bucket)
            .order_by(bucket)
        )

        rows = (await self.session.execute(stmt)).all()
        return [
            WeeklyKPIRow(
                week_start=_as_date(r[0]),
                post_count=int(r[1] or 0),
                impressions=int(r[2] or 0),
                likes=int(r[3] or 0),
                comments=int(r[4] or 0),
                shares=int(r[5] or 0),
                clicks=int(r[6] or 0),
                engagement_rate=float(r[7]) if r[7] is not None else None,
            )
            for r in rows
        ]

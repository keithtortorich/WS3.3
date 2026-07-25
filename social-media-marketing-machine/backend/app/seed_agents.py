"""Seed script: load extracted marketing agents into the database for an org.

Usage:
    python -m app.seed_agents --org-id <uuid>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.agent_template import AgentTemplate

SEED_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / ".hermes"
    / "desktop-attachments"
    / "agents_extracted.json"
)


def _category_from_use_case(name: str, use_case: str) -> str | None:
    text = f"{name} {use_case}".lower()
    if any(token in text for token in ["lead", "score"]):
        return "lead_growth"
    if any(
        token in text
        for token in ["content", "calendar", "blog", "seo", "keyword", "audit", "performance"]
    ):
        return "content_marketing"
    if any(token in text for token in ["social", "listening", "influencer"]):
        return "social_media"
    if any(
        token in text
        for token in ["competitive", "pricing", "strategy", "trend"]
    ):
        return "strategy"
    if any(
        token in text
        for token in ["email", "campaign", "conversion", "attribution", "journey"]
    ):
        return "campaign_optimization"
    if any(
        token in text
        for token in ["brand", "voice", "pitch", "landing", "feedback"]
    ):
        return "messaging"
    return "default"


_KNOWN_SLUGS = [
    "competitive-intelligence-agent",
    "icp-reverse-engineer-agent",
    "pitch-deck-generator-agent",
    "content-calendar-creator-agent",
    "email-campaign-optimizer-agent",
    "seo-keyword-research-agent",
    "social-media-audit-agent",
    "lead-scoring-model-agent",
    "campaign-performance-analyzer-agent",
    "brand-voice-development-agent",
    "customer-journey-mapping-agent",
    "conversion-rate-optimization-agent",
    "influencer-research-agent",
    "market-trend-analysis-agent",
    "landing-page-copy-agent",
    "email-list-segmentation-agent",
    "competitive-pricing-research-agent",
    "content-performance-auditor-agent",
    "marketing-attribution-analyst-agent",
    "social-listening-intelligence-agent",
    "customer-feedback-analyzer-agent",
]


def _slug_for_name(name: str) -> str:
    normalized = name.strip().lower()
    for slug in _KNOWN_SLUGS:
        if normalized == slug.replace("-", " "):
            return slug
    return normalized.replace("/", "-").replace(" ", "-").replace("’", "").replace("'", "")


async def seed_agents(organization_id: uuid.UUID) -> None:
    if not SEED_PATH.exists():
        raise SystemExit(f"Missing seed file at {SEED_PATH}")

    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    async with AsyncSessionLocal() as session:
        for agent in payload.get("agents", []):
            slug = _slug_for_name(agent["agent_name"])
            existing = (
                await session.execute(
                    select(AgentTemplate).where(
                        AgentTemplate.organization_id == organization_id,
                        AgentTemplate.slug == slug,
                    )
                )
            ).scalar_one_or_none()

            if existing:
                print(
                    f"Skipping '{slug}' — already exists (v{existing.version})."
                )
                continue

            template = AgentTemplate(
                organization_id=organization_id,
                slug=slug,
                name=agent["agent_name"].strip(),
                description=agent["use_case"].strip(),
                template_body=agent["prompt"].strip(),
                variables=[],
                category=_category_from_use_case(
                    agent["agent_name"], agent["use_case"]
                ),
                version=1,
                is_active=True,
            )
            session.add(template)
            print(f"Seeding '{slug}' (v1).")
            session.expunge_all()
        await session.commit()
    print("Seeding complete.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed marketing agents for an organization."
    )
    parser.add_argument("--org-id", required=True, help="Target organization UUID")
    args = parser.parse_args()
    asyncio.run(seed_agents(uuid.UUID(args.org_id)))


if __name__ == "__main__":
    main()

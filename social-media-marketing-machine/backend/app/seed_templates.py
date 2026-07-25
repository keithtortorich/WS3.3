"""Seed script: loads the starter Jinja2 templates in app/templates/*.jinja2
into the PromptTemplate table for a given organization.

Usage:
    python -m app.seed_templates --org-id <uuid>

If no --org-id is given, the script prints usage and exits — prompt
templates are org-scoped (multi-tenant), so seeding requires a target
organization to already exist.
"""
from __future__ import annotations

import argparse
import asyncio
import uuid
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.prompt_template import PromptTemplate

TEMPLATES_DIR = Path(__file__).parent / "templates"

# (slug, display name, description, expected variable names)
STARTER_TEMPLATES = [
    (
        "social_post_caption",
        "Social Post Caption",
        "Generates a full, platform-appropriate social media caption for a brand/campaign.",
        ["brand", "voice", "audience", "platform", "goal", "offer", "cta", "keywords", "campaign", "post_type"],
    ),
    (
        "headline_hook",
        "Headline / Hook Generator",
        "Generates 5 scroll-stopping headline/hook options for a post or ad.",
        ["brand", "voice", "audience", "platform", "goal", "offer", "keywords", "campaign"],
    ),
    (
        "hashtag_generator",
        "Hashtag Generator",
        "Generates a tiered (broad/niche/branded) hashtag set appropriate to the platform.",
        ["brand", "platform", "audience", "campaign", "post_type", "keywords"],
    ),
]


async def seed_templates(organization_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        for slug, name, description, variables in STARTER_TEMPLATES:
            template_path = TEMPLATES_DIR / f"{slug}.jinja2"
            body = template_path.read_text(encoding="utf-8")

            existing = (
                await session.execute(
                    select(PromptTemplate).where(
                        PromptTemplate.organization_id == organization_id,
                        PromptTemplate.slug == slug,
                        PromptTemplate.is_active.is_(True),
                    )
                )
            ).scalar_one_or_none()

            if existing:
                print(f"Skipping '{slug}' — an active version already exists (v{existing.version}).")
                continue

            template = PromptTemplate(
                organization_id=organization_id,
                slug=slug,
                name=name,
                description=description,
                template_body=body,
                variables=variables,
                version=1,
                is_active=True,
            )
            session.add(template)
            print(f"Seeded template '{slug}' (v1).")

        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed starter PromptTemplates for an organization.")
    parser.add_argument("--org-id", required=True, help="UUID of the organization to seed templates for.")
    args = parser.parse_args()
    asyncio.run(seed_templates(uuid.UUID(args.org_id)))


if __name__ == "__main__":
    main()

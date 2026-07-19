from __future__ import annotations

from app.models.campaign import Campaign
from app.repositories.base import OrgScopedRepository


class CampaignRepository(OrgScopedRepository[Campaign]):
    model = Campaign

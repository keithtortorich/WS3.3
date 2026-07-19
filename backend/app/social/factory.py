"""Factory that instantiates a SocialPlatformAdapter by Platform enum."""
from __future__ import annotations

from app.models.enums import PlatformName
from app.social.base import SocialPlatformAdapter
from app.social.platforms.facebook import FacebookAdapter
from app.social.platforms.google_business import GoogleBusinessAdapter
from app.social.platforms.instagram import InstagramAdapter
from app.social.platforms.linkedin import LinkedInAdapter
from app.social.platforms.pinterest import PinterestAdapter
from app.social.platforms.threads import ThreadsAdapter
from app.social.platforms.tiktok import TikTokAdapter
from app.social.platforms.x import XAdapter
from app.social.platforms.youtube import YouTubeAdapter

_ADAPTER_REGISTRY = {
    PlatformName.LINKEDIN: LinkedInAdapter,
    PlatformName.FACEBOOK: FacebookAdapter,
    PlatformName.INSTAGRAM: InstagramAdapter,
    PlatformName.X: XAdapter,
    PlatformName.THREADS: ThreadsAdapter,
    PlatformName.TIKTOK: TikTokAdapter,
    PlatformName.PINTEREST: PinterestAdapter,
    PlatformName.YOUTUBE: YouTubeAdapter,
    PlatformName.GOOGLE_BUSINESS: GoogleBusinessAdapter,
}


def get_social_adapter(platform: PlatformName) -> SocialPlatformAdapter:
    """Instantiate the adapter for the given platform. Only LinkedIn is
    fully implemented; the rest raise NotImplementedError per-method."""
    adapter_cls = _ADAPTER_REGISTRY.get(platform)
    if adapter_cls is None:
        raise ValueError(f"Unknown platform '{platform}'.")
    return adapter_cls()

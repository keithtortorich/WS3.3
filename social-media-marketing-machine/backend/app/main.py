"""FastAPI application factory.

Using an explicit ``create_app()`` factory (rather than a bare module-level
``app = FastAPI()``) keeps app construction testable — tests can build a
fresh app instance with overridden dependencies without import-order side
effects.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler, unhandled_exception_handler
from app.routers import (
    agent_templates,
    analytics,
    approvals,
    auth,
    brands,
    calendar,
    campaigns,
    clients,
    execution_nodes,
    integrations,
    media,
    notifications,
    posts,
    publish,
)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Social Media Marketing Machine API",
        description=(
            "Multi-tenant SaaS platform API for marketing agencies to manage "
            "clients, brands, campaigns, and AI-assisted social media content "
            "through creation, approval, scheduling, and publishing."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(auth.router)
    app.include_router(clients.router)
    app.include_router(brands.router)
    app.include_router(campaigns.router)
    app.include_router(posts.router)
    app.include_router(media.router)
    app.include_router(analytics.router)
    app.include_router(calendar.router)
    app.include_router(publish.router)
    app.include_router(approvals.router)
    app.include_router(notifications.router)
    app.include_router(agent_templates.router)
    app.include_router(execution_nodes.router)
    app.include_router(integrations.router)

    @app.get("/healthz", tags=["health"])
    async def health_check() -> dict:
        """Liveness probe used by docker-compose healthchecks."""
        return {"status": "ok", "env": settings.APP_ENV}

    return app


app = create_app()

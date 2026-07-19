"""Lightweight in-process publish/subscribe event bus.

This is intentionally NOT a distributed message queue — it's a simple
synchronous (with async handler support) dispatcher that lets different
parts of the monolith react to domain events (see domain_events.py)
without importing each other directly. For cross-process work (e.g. retry
logic that must survive a process restart), handlers hand off to Celery
tasks (see app/workers/tasks/publish_tasks.py) rather than doing the work
inline on the bus thread.

Why not just call functions directly? Decoupling: e.g. when a
``PublishFailed`` event fires, both a Celery retry task AND a Notification
-creation handler can subscribe independently, without the code that
detected the failure needing to know about either.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Type, TypeVar, Union

from app.events.domain_events import DomainEvent

logger = logging.getLogger(__name__)

EventT = TypeVar("EventT", bound=DomainEvent)
Handler = Callable[[EventT], Union[None, Awaitable[None]]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: Type[EventT], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[EventT], handler: Handler) -> None:
        if handler in self._handlers.get(event_type, []):
            self._handlers[event_type].remove(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Dispatch an event to all subscribed handlers.

        Handler exceptions are logged and swallowed (not re-raised) so one
        broken subscriber can't take down the publisher's request/task —
        this mirrors how most production event buses behave.
        """
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            try:
                result = handler(event)
                if inspect.isawaitable(result):
                    await result
            except Exception:  # noqa: BLE001 - intentionally broad, see docstring
                logger.exception(
                    "Event handler %r raised while handling %s", handler, type(event).__name__
                )

    def publish_sync(self, event: DomainEvent) -> None:
        """Synchronous convenience wrapper for non-async call sites (e.g.
        inside a Celery task, which runs outside an event loop)."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.publish(event))
        else:
            # Already inside a loop (e.g. called from async code accidentally
            # using the sync wrapper) — schedule it instead of blocking.
            asyncio.ensure_future(self.publish(event))


# Process-wide singleton. A monolith-scale event bus doesn't need per-request
# instances; handlers register once at import time.
event_bus = EventBus()

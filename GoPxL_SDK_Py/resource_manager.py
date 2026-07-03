"""GoResourceManager - URI-keyed GoResource cache."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from .resource import GoResource

if TYPE_CHECKING:
    from .rest_client import GoRestClient


class GoResourceManager:
    def __init__(self, client: GoRestClient) -> None:
        self._client = client
        self._resources: dict[str, GoResource] = {}
        self._lock = threading.Lock()
        self._auto_subscribe = False
        self._auto_validation = False
        self._subscription_optimized_invalidation = True
        self._client.set_non_idempotent_request_handler(self._on_non_idempotent_request)

    def client(self) -> GoRestClient:
        return self._client

    def get_or_create(self, uri: str) -> GoResource:
        key = uri if uri.startswith("/") else f"/{uri}"
        should_subscribe = False
        should_validate = False
        with self._lock:
            resource = self._resources.get(key)
            if resource is None:
                resource = GoResource(self._client, key, manager=self)
                self._resources[key] = resource
                should_subscribe = self._auto_subscribe
                should_validate = self._auto_validation
        if should_validate:
            resource.enable_validation(True)
        if should_subscribe:
            resource.subscribe()
        return resource

    def set_auto_subscribe(self, enabled: bool) -> None:
        self._auto_subscribe = enabled

    def auto_subscribe(self) -> bool:
        return self._auto_subscribe

    def set_auto_validation(self, enabled: bool) -> None:
        self._auto_validation = enabled

    def auto_validation(self) -> bool:
        return self._auto_validation

    def enable_validation_all(self) -> None:
        with self._lock:
            resources = list(self._resources.values())
        for resource in resources:
            resource.enable_validation(True)

    def disable_validation_all(self) -> None:
        with self._lock:
            resources = list(self._resources.values())
        for resource in resources:
            resource.enable_validation(False)

    def subscribe_all(self) -> None:
        with self._lock:
            resources = [r for r in self._resources.values() if not r.is_subscribed()]
        for resource in resources:
            resource.subscribe()

    def unsubscribe_all(self) -> None:
        with self._lock:
            resources = [r for r in self._resources.values() if r.is_subscribed()]
        for resource in resources:
            resource.unsubscribe()

    def invalidate_all(self) -> None:
        with self._lock:
            resources = list(self._resources.values())
        for resource in resources:
            resource.mark_remote_changes()

    def reset_connection_state(self) -> None:
        with self._lock:
            resources = list(self._resources.values())
            for resource in resources:
                resource.reset_subscription_state()
        self._client.clear_all_listeners()

    def set_subscription_optimized_invalidation(self, enabled: bool) -> None:
        self._subscription_optimized_invalidation = enabled

    def subscription_optimized_invalidation(self) -> bool:
        return self._subscription_optimized_invalidation

    def remove(self, uri: str) -> None:
        key = uri if uri.startswith("/") else f"/{uri}"
        with self._lock:
            resource = self._resources.pop(key, None)
        if resource is not None and resource.is_subscribed():
            resource.unsubscribe()

    def cleanup(self) -> None:
        removed: list[GoResource] = []
        with self._lock:
            for key in list(self._resources):
                resource = self._resources[key]
                if resource.is_deleted():
                    removed.append(self._resources.pop(key))
        for resource in removed:
            if resource.is_subscribed():
                resource.unsubscribe()

    def mark_and_remove_if_present(self, uri: str) -> None:
        key = uri if uri.startswith("/") else f"/{uri}"
        removed: GoResource | None = None
        with self._lock:
            resource = self._resources.get(key)
            if resource is not None:
                resource.mark_deleted()
                removed = self._resources.pop(key)
        if removed is not None and removed.is_subscribed():
            removed.unsubscribe()

    def clear(self) -> None:
        with self._lock:
            self._resources.clear()

    def _on_non_idempotent_request(self) -> None:
        with self._lock:
            resources = list(self._resources.values())
        for resource in resources:
            if self._subscription_optimized_invalidation and resource.is_subscribed():
                continue
            resource.mark_remote_changes()

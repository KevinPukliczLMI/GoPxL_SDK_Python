"""GoResource - high-level REST resource helper (mirrors GoPxLSdk::GoResource)."""

from __future__ import annotations

import copy
import threading
from typing import TYPE_CHECKING, Any, Callable

from .enums import GoNotificationType, GoStatus
from .exceptions import GoRequestError, GoResourceError, GoResourceValidationError
from .json_pointer import JsonPointerError, get_at, merge_patch, normalize_path, set_at
from .schema_validator import GoSchemaValidator

if TYPE_CHECKING:
    from .resource_manager import GoResourceManager
    from .rest_client import GoRestClient
    from .response import GoNotificationResponse

_LINKS_SELF_HREF = "/_links/self/href"


class GoRelationType:
    Item = "item"
    Scanner = "go:scanner"
    SubTask = "go:subTask"
    Content = "go:content"
    Command = "go:command"
    Action = "go:action"


class GoUpdateScope:
    def __init__(self, resource: GoResource) -> None:
        self._resource = resource
        self._resource.begin_update()

    def cancel(self) -> None:
        self._resource.cancel_update()

    def __enter__(self) -> GoUpdateScope:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self._resource.discard_pending()
            if self._resource.is_update_deferred():
                self._resource._deferred_depth -= 1  # noqa: SLF001
                if self._resource._deferred_depth == 0:  # noqa: SLF001
                    self._resource._cancelled = False  # noqa: SLF001
            return
        self._resource.end_update()


class GoResource:
    DEFAULT_TIMEOUT_MS = 5000
    DEFAULT_EXPAND_LEVEL = 0
    DEFAULT_RELATION_TYPE = GoRelationType.Item

    def __init__(
        self,
        client: GoRestClient,
        uri: str,
        manager: GoResourceManager | None = None,
    ) -> None:
        self._client = client
        self._uri = uri if uri.startswith("/") else f"/{uri}"
        self._manager = manager
        self._timeout_ms = self.DEFAULT_TIMEOUT_MS
        self._expand_level = self.DEFAULT_EXPAND_LEVEL
        self._auto_fetch_schema = False
        self._auto_invalidation = True
        self._cached_data: dict[str, Any] | None = None
        self._cached_schema: dict[str, Any] | None = None
        self._data_cache_valid = False
        self._schema_cache_valid = False
        self._validation_enabled = False
        self._pending_patch: dict[str, Any] = {}
        self._deferred_depth = 0
        self._cancelled = False
        self._has_remote_changes = False
        self._deleted = False
        self._subscribed = False
        self._listener_id = 0
        self._change_handler: Callable[[GoNotificationResponse], None] | None = None
        self._state_lock = threading.Lock()

    def uri(self) -> str:
        return self._uri

    def set_timeout(self, timeout_ms: int) -> None:
        self._timeout_ms = timeout_ms

    def timeout(self) -> int:
        return self._timeout_ms

    def set_expand_level(self, level: int) -> None:
        self._expand_level = level

    def expand_level(self) -> int:
        return self._expand_level

    def set_auto_fetch_schema(self, enabled: bool) -> None:
        self._auto_fetch_schema = enabled

    def auto_fetch_schema(self) -> bool:
        return self._auto_fetch_schema

    def set_auto_invalidation(self, enabled: bool) -> None:
        self._auto_invalidation = enabled

    def auto_invalidation(self) -> bool:
        return self._auto_invalidation

    def is_managed(self) -> bool:
        return self._manager is not None

    def is_deleted(self) -> bool:
        return self._deleted

    def has_remote_changes(self) -> bool:
        return self._has_remote_changes

    def _check_deleted(self) -> None:
        if self._deleted:
            raise GoResourceError(f"GoResource [{self._uri}] is deleted")

    def mark_deleted(self) -> None:
        self._deleted = True
        self._data_cache_valid = False
        self._schema_cache_valid = False
        self._cached_data = None
        self._cached_schema = None

    def mark_remote_changes(self) -> None:
        self._has_remote_changes = True

    def invalidate(self) -> None:
        self._data_cache_valid = False
        self._schema_cache_valid = False
        self._cached_data = None
        self._cached_schema = None
        self._has_remote_changes = True

    def invalidate_cache(self) -> None:
        self._data_cache_valid = False
        self._schema_cache_valid = False
        self._cached_data = None
        self._cached_schema = None

    def cache_payload(self, payload: dict[str, Any]) -> None:
        self._cached_data = dict(payload)
        self._data_cache_valid = True
        schema = payload.get("_schema")
        if isinstance(schema, dict):
            self._cached_schema = dict(schema)
            self._schema_cache_valid = True

    def cache(self) -> None:
        self._check_deleted()
        self.read(args={"includeSchema": self._auto_fetch_schema, "expandLevel": self._expand_level})

    def _ensure_data(self) -> dict[str, Any]:
        self._check_deleted()
        if self._has_remote_changes:
            self._data_cache_valid = False
            self._has_remote_changes = False
        if not self._data_cache_valid:
            self.cache()
        return self._cached_data or {}

    def data(self, force_refresh: bool = False) -> dict[str, Any]:
        if force_refresh:
            self.invalidate_cache()
        return copy.deepcopy(self._ensure_data())

    def read(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        self._check_deleted()
        read_args = {"expandLevel": self._expand_level}
        if args:
            read_args.update(args)
        try:
            response = self._client.read(self._uri, args=read_args).get_response(self._timeout_ms)
        except GoRequestError as exc:
            self._handle_not_found(exc)
            raise
        payload = dict(response.payload or {})
        self.cache_payload(payload)
        self._has_remote_changes = False
        return copy.deepcopy(payload)

    def update(self, patch: dict[str, Any] | None = None, args: dict[str, Any] | None = None) -> dict[str, Any]:
        self._check_deleted()
        body = patch if patch is not None else self._pending_patch
        try:
            if args:
                response = self._client.update(self._uri, body, args).get_response(self._timeout_ms)
            else:
                response = self._client.update(self._uri, body).get_response(self._timeout_ms)
        except GoRequestError as exc:
            self._handle_not_found(exc)
            raise
        if isinstance(response.payload, dict) and response.payload:
            self.cache_payload(dict(response.payload))
        elif self._auto_invalidation:
            self.invalidate_cache()
        self._pending_patch = {}
        self._has_remote_changes = False
        return copy.deepcopy(self._cached_data or {})

    def get_bool(self, path: str) -> bool:
        return bool(self._get_prop(path))

    def get_int(self, path: str) -> int:
        return int(self._get_prop(path))

    def get_int64(self, path: str) -> int:
        return int(self._get_prop(path))

    def get_float(self, path: str) -> float:
        return float(self._get_prop(path))

    def get_double(self, path: str) -> float:
        return float(self._get_prop(path))

    def get_string(self, path: str) -> str:
        return str(self._get_prop(path))

    def get_object(self, path: str) -> dict[str, Any]:
        value = self._get_prop(path)
        if not isinstance(value, dict):
            raise GoResourceError(f"GoResource [{self._uri}] get_object({path!r}): not an object")
        return copy.deepcopy(value)

    def get_prop(self, path: str) -> Any:
        return copy.deepcopy(self._get_prop(path))

    def _get_prop(self, path: str) -> Any:
        try:
            return get_at(self._ensure_data(), normalize_path(path))
        except JsonPointerError as exc:
            raise GoResourceError(f"GoResource [{self._uri}] get_prop({path!r}): {exc}") from exc

    def set_bool(self, path: str, value: bool) -> None:
        self._set_prop(path, value)

    def set_int(self, path: str, value: int) -> None:
        self._set_prop(path, value)

    def set_int64(self, path: str, value: int) -> None:
        self._set_prop(path, value)

    def set_float(self, path: str, value: float) -> None:
        self._set_prop(path, value)

    def set_double(self, path: str, value: float) -> None:
        self._set_prop(path, value)

    def set_string(self, path: str, value: str) -> None:
        self._set_prop(path, value)

    def set_prop(self, path: str, value: Any) -> None:
        self._set_prop(path, value)

    def set_json(self, patch: dict[str, Any]) -> None:
        self._apply_set(patch)

    def set_value(self, key: str, value: Any) -> None:
        self.set_prop(f"/{key.lstrip('/')}", value)

    def get_value(self, key: str, default: Any = None) -> Any:
        try:
            return self.get_prop(f"/{key.lstrip('/')}")
        except GoResourceError:
            return default

    def _set_prop(self, path: str, value: Any) -> None:
        normalized = normalize_path(path)
        patch: dict[str, Any] = {}
        set_at(patch, normalized, value)
        self._validate_if_enabled(normalized, value)
        self._apply_set(patch)

    def _apply_set(self, patch_payload: dict[str, Any]) -> None:
        self._check_deleted()
        merge_patch(self._pending_patch, patch_payload)
        if self._deferred_depth == 0:
            self.flush()

    def begin_update(self) -> None:
        self._deferred_depth += 1

    def end_update(self) -> dict[str, Any]:
        if self._deferred_depth <= 0:
            raise GoResourceError(f"GoResource [{self._uri}] end_update() called without matching begin_update()")
        self._deferred_depth -= 1
        if self._deferred_depth == 0:
            if self._cancelled:
                self._pending_patch = {}
                self._cancelled = False
            elif self._pending_patch:
                return self.update()
        return self.data()

    def scoped_update(self) -> GoUpdateScope:
        return GoUpdateScope(self)

    def cancel_update(self) -> None:
        if self._deferred_depth > 0:
            self._cancelled = True

    def is_update_cancelled(self) -> bool:
        return self._cancelled

    def is_update_deferred(self) -> bool:
        return self._deferred_depth > 0

    def flush(self) -> None:
        self._check_deleted()
        if not self._pending_patch:
            return
        patch = self._pending_patch
        self._pending_patch = {}
        self.update(patch)

    def discard_pending(self) -> None:
        self._pending_patch = {}

    def enable_validation(self, enable: bool = True) -> None:
        self._validation_enabled = enable

    def is_validation_enabled(self) -> bool:
        return self._validation_enabled

    def _ensure_schema(self) -> dict[str, Any]:
        if not self._schema_cache_valid:
            self.schema()
        return self._cached_schema or {}

    def schema(self) -> dict[str, Any]:
        self._check_deleted()
        if self._schema_cache_valid and self._cached_schema is not None:
            return copy.deepcopy(self._cached_schema)
        self.read(args={"includeSchema": True, "expandLevel": self._expand_level})
        return copy.deepcopy(self._cached_schema or {})

    def schema_for(self, path: str) -> dict[str, Any]:
        return GoSchemaValidator.schema_for_path(self._ensure_schema(), normalize_path(path))

    def validate(self, path: str, value: Any, errors: list[str] | None = None) -> bool:
        try:
            schema_node = GoSchemaValidator.schema_for_path(self._ensure_schema(), normalize_path(path))
        except GoResourceError:
            return True
        validation_errors: list[str] = [] if errors is None else errors
        return GoSchemaValidator.validate(value, schema_node, validation_errors)

    def _validate_if_enabled(self, path: str, value: Any) -> None:
        if not self._validation_enabled:
            return
        try:
            schema_node = GoSchemaValidator.schema_for_path(self._ensure_schema(), normalize_path(path))
        except GoResourceError:
            return
        validation_errors: list[str] = []
        if not GoSchemaValidator.validate(value, schema_node, validation_errors):
            raise GoResourceValidationError(
                f'GoResource [{self._uri}] validation failed for "{path}"',
                validation_errors,
            )

    def links(self) -> dict[str, Any]:
        try:
            value = get_at(self._ensure_data(), "/_links")
            return copy.deepcopy(value) if isinstance(value, dict) else {}
        except JsonPointerError:
            return {}

    def embedded(self) -> dict[str, Any]:
        try:
            value = get_at(self._ensure_data(), "/_embedded")
            return copy.deepcopy(value) if isinstance(value, dict) else {}
        except JsonPointerError:
            return {}

    def child_uris(self, relation_type: str = DEFAULT_RELATION_TYPE) -> list[str]:
        embedded = self.embedded()
        if not embedded:
            return []
        items = embedded.get(relation_type)
        if items is None:
            return []
        if isinstance(items, dict):
            items = [items]
        uris: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            links = item.get("_links") or {}
            self_link = links.get("self") or {}
            href = self_link.get("href")
            if href:
                uris.append(str(href))
        return uris

    def child_count(self, relation_type: str = DEFAULT_RELATION_TYPE) -> int:
        return len(self.child_uris(relation_type))

    def children(self, relation_type: str = DEFAULT_RELATION_TYPE) -> list[GoResource]:
        manager = self._require_manager("children")
        result: list[GoResource] = []
        embedded = self.embedded()
        items = embedded.get(relation_type)
        if items is None:
            return result
        if isinstance(items, dict):
            items = [items]
        for item in items:
            if not isinstance(item, dict):
                continue
            links = item.get("_links") or {}
            self_link = links.get("self") or {}
            href = self_link.get("href")
            if not href:
                continue
            child = manager.get_or_create(str(href))
            if self._is_expanded(item):
                child.cache_payload(item)
            result.append(child)
        return result

    def child(self, child_path: str) -> GoResource:
        manager = self._require_manager("child")
        base = self._uri.rstrip("/")
        relative = child_path.lstrip("/")
        return manager.get_or_create(f"{base}/{relative}")

    def create_child(self, arguments: dict[str, Any] | None = None) -> GoResource:
        self._check_deleted()
        manager = self._require_manager("create_child")
        try:
            response = self._client.create(self._uri, arguments or {}).get_response(self._timeout_ms)
        except GoRequestError as exc:
            self._handle_not_found(exc)
            raise
        payload = response.payload or {}
        new_uri = ""
        if isinstance(payload, dict):
            new_uri = str(payload.get("path") or "")
            if not new_uri:
                links = payload.get("_links") or {}
                self_link = links.get("self") or {}
                new_uri = str(self_link.get("href") or "")
        if not new_uri:
            raise GoResourceError(
                f"GoResource [{self._uri}] create_child(): server response contained no usable URI"
            )
        self.invalidate_cache()
        return manager.get_or_create(new_uri)

    def delete(self) -> None:
        self._check_deleted()
        try:
            self._client.delete(self._uri).check_response(self._timeout_ms)
        except GoRequestError as exc:
            if exc.status == int(GoStatus.ERROR_NOT_FOUND):
                self.mark_deleted()
                if self._manager is not None:
                    self._manager.remove(self._uri)
                return
            raise
        self.mark_deleted()
        if self._manager is not None:
            self._manager.remove(self._uri)

    def delete_child(self, child_uri: str) -> None:
        try:
            self._client.delete(child_uri).check_response(self._timeout_ms)
        except GoRequestError as exc:
            if exc.status == int(GoStatus.ERROR_NOT_FOUND):
                if self._manager is not None:
                    self._manager.mark_and_remove_if_present(child_uri)
                self.invalidate_cache()
                return
            raise
        if self._manager is not None:
            self._manager.mark_and_remove_if_present(child_uri)
        self.invalidate_cache()

    def delete_all_children(self, relation_type: str = DEFAULT_RELATION_TYPE) -> None:
        for uri in self.child_uris(relation_type):
            self._client.delete(uri).check_response(self._timeout_ms)
            if self._manager is not None:
                self._manager.mark_and_remove_if_present(uri)
        self.invalidate_cache()

    def call(self, arguments: dict[str, Any] | None = None, timeout_ms: int = 0) -> dict[str, Any]:
        self._check_deleted()
        timeout = timeout_ms if timeout_ms > 0 else self._timeout_ms
        try:
            if arguments is None:
                response = self._client.call(self._uri).get_response(timeout)
            else:
                response = self._client.call(self._uri, arguments).get_response(timeout)
        except GoRequestError as exc:
            self._handle_not_found(exc)
            raise
        return dict(response.payload or {})

    def call_command(
        self,
        command_name: str,
        arguments: dict[str, Any] | None = None,
        timeout_ms: int = 0,
    ) -> dict[str, Any]:
        uri = f"{self._uri}/commands/{command_name}"
        timeout = timeout_ms if timeout_ms > 0 else self._timeout_ms
        try:
            if arguments is None:
                response = self._client.call(uri).get_response(timeout)
            else:
                response = self._client.call(uri, arguments).get_response(timeout)
        except GoRequestError as exc:
            self._handle_not_found(exc)
            raise
        self.invalidate_cache()
        return dict(response.payload or {})

    def call_action(
        self,
        action_name: str,
        arguments: dict[str, Any] | None = None,
        timeout_ms: int = 0,
    ) -> dict[str, Any]:
        uri = f"{self._uri}/actions/{action_name}"
        timeout = timeout_ms if timeout_ms > 0 else self._timeout_ms
        try:
            if arguments is None:
                response = self._client.call(uri).get_response(timeout)
            else:
                response = self._client.call(uri, arguments).get_response(timeout)
        except GoRequestError as exc:
            self._handle_not_found(exc)
            raise
        self.invalidate_cache()
        return dict(response.payload or {})

    def command_names(self) -> list[str]:
        return self._link_names(GoRelationType.Command)

    def action_names(self) -> list[str]:
        return self._link_names(GoRelationType.Action)

    def call_arguments(self) -> dict[str, Any]:
        try:
            return self.get_object("/parameters")
        except GoResourceError:
            return {}

    def subscribe(self, change_handler: Callable[[GoNotificationResponse], None] | None = None) -> None:
        if self._subscribed:
            return
        self._change_handler = change_handler

        def _on_notification(notification: GoNotificationResponse) -> None:
            if notification.path != self._uri:
                return
            if notification.notification_type == GoNotificationType.DELETED:
                self._deleted = True
            if notification.notification_type in (
                GoNotificationType.UPDATED,
                GoNotificationType.EMBEDDED_UPDATED,
            ):
                if isinstance(notification.payload, dict):
                    self.cache_payload(dict(notification.payload))
                else:
                    self.invalidate_cache()
            elif notification.notification_type == GoNotificationType.DELETED:
                self.invalidate_cache()
            self._has_remote_changes = True
            if self._change_handler is not None:
                self._change_handler(notification)

        self._listener_id = self._client.add_notification_listener(self._uri, _on_notification)
        self._subscribed = True

    def unsubscribe(self) -> None:
        if not self._subscribed:
            return
        try:
            if self._listener_id:
                self._client.remove_notification_listener(self._listener_id)
        finally:
            self._listener_id = 0
            self._subscribed = False
            self._change_handler = None

    def is_subscribed(self) -> bool:
        return self._subscribed

    def reset_subscription_state(self) -> None:
        self._subscribed = False
        self._listener_id = 0
        self._change_handler = None
        self._has_remote_changes = True

    def _require_manager(self, operation: str) -> GoResourceManager:
        if self._manager is None:
            raise GoResourceError(
                f"GoResource [{self._uri}] {operation}(): requires a GoResourceManager (use GoSystem.resource())"
            )
        return self._manager

    def _handle_not_found(self, exc: GoRequestError) -> None:
        if exc.status == int(GoStatus.ERROR_NOT_FOUND):
            self.mark_deleted()
            if self._manager is not None:
                self._manager.remove(self._uri)

    def _link_names(self, relation_type: str) -> list[str]:
        links = self.links()
        items = links.get(relation_type)
        if items is None:
            return []
        if isinstance(items, dict):
            items = [items]
        names: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            href = item.get("href")
            if not href:
                continue
            href = str(href)
            if "/" in href:
                names.append(href.rsplit("/", 1)[-1])
        return names

    @staticmethod
    def _is_expanded(item_data: dict[str, Any]) -> bool:
        return len(item_data) > 1 or "_links" not in item_data

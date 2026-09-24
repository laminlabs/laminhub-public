"""Import Sentry uptime checks into LaminDB records."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import httpx
import lamindb as ln

SENTRY_API_URL = "https://us.sentry.io/api/0"
SENTRY_CREDENTIAL_NAME = "sentry-uptime-read-token"
HTTP_TIMEOUT_SECONDS = 15
MAX_PAGES = 50

MONITOR_TYPE_NAME = "Sentry uptime monitors"
MONITOR_SCHEMA_NAME = "Sentry uptime monitors"
CHECK_TYPE_NAME = "Sentry uptime checks"
CHECK_SCHEMA_NAME = "Sentry uptime checks"

JsonObject = dict[str, Any]
GetJson = Callable[[str, str, dict[str, Any] | None], tuple[Any, dict[str, str]]]


def _get_json(
    url: str,
    bearer_token: str,
    params: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, str]]:
    try:
        response = httpx.get(
            url,
            params=params,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {bearer_token}",
            },
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        detail = error.response.text[:500]
        msg = (
            f"GET {urlparse(url).path} failed with HTTP "
            f"{error.response.status_code}: {detail}"
        )
        raise RuntimeError(msg) from error
    except httpx.RequestError as error:
        msg = f"GET {urlparse(url).path} failed: {error}"
        raise RuntimeError(msg) from error
    headers = {key.title(): value for key, value in response.headers.items()}
    return response.json(), headers


def _next_page_url(current_url: str, link_header: str | None) -> str | None:
    if not link_header:
        return None
    for link in link_header.split(","):
        sections = [section.strip() for section in link.split(";")]
        if not sections or not sections[0].startswith("<"):
            continue
        attributes = set(sections[1:])
        if 'rel="next"' in attributes and 'results="true"' in attributes:
            candidate = sections[0][1:-1]
            next_url = urljoin(current_url, candidate)
            if urlparse(next_url).netloc != urlparse(SENTRY_API_URL).netloc:
                msg = "Sentry pagination returned a link for an unexpected host"
                raise RuntimeError(msg)
            return next_url
    return None


def _get_all_pages(
    url: str,
    token: str,
    params: dict[str, Any] | None = None,
    *,
    get_json: GetJson = _get_json,
) -> list[JsonObject]:
    results: list[JsonObject] = []
    next_url: str | None = url
    next_params = params
    seen_urls: set[str] = set()
    while next_url is not None:
        if next_url in seen_urls or len(seen_urls) >= MAX_PAGES:
            msg = "Sentry pagination did not terminate"
            raise RuntimeError(msg)
        seen_urls.add(next_url)
        page, headers = get_json(next_url, token, next_params)
        if not isinstance(page, list):
            msg = f"Expected a list from Sentry, received {type(page).__name__}"
            raise RuntimeError(msg)
        results.extend(page)
        next_url = _next_page_url(next_url, headers.get("Link"))
        next_params = None
    return results


def _read_sentry_token(organization_id: str) -> str:
    from lamindb_setup import settings

    api_url = settings.instance.api_url
    access_token = settings.user.access_token
    if not api_url or not access_token:
        msg = "The Lamin instance API URL and bot access token are required"
        raise RuntimeError(msg)
    secret_url = (
        f"{api_url.rstrip('/')}/secrets/{quote(organization_id)}/"
        f"{quote(SENTRY_CREDENTIAL_NAME)}"
    )
    response, _ = _get_json(secret_url, access_token)
    try:
        value = response["data"]["value"]
    except (KeyError, TypeError) as error:
        msg = "The Lamin organization-secret response did not contain a value"
        raise RuntimeError(msg) from error
    if not isinstance(value, str) or not value:
        msg = f"Organization secret {SENTRY_CREDENTIAL_NAME!r} is empty"
        raise RuntimeError(msg)
    return value


def _list_monitors(
    token: str,
    organization: str,
    project: str,
    environment: str,
    *,
    get_json: GetJson = _get_json,
) -> list[JsonObject]:
    url = f"{SENTRY_API_URL}/organizations/{quote(organization)}/uptime/"
    monitors = _get_all_pages(
        url,
        token,
        {"project": project, "environment": environment, "per_page": 100},
        get_json=get_json,
    )
    return [monitor for monitor in monitors if monitor.get("status") == "active"]


def _list_checks(
    token: str,
    organization: str,
    project: str,
    monitor_id: str,
    start: datetime,
    end: datetime,
    *,
    get_json: GetJson = _get_json,
) -> list[JsonObject]:
    url = (
        f"{SENTRY_API_URL}/projects/{quote(organization)}/{quote(project)}/"
        f"uptime/{quote(monitor_id)}/checks/"
    )
    return _get_all_pages(
        url,
        token,
        {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "per_page": 100,
        },
        get_json=get_json,
    )


def _feature(name: str, dtype: Any, description: str, *, nullable: bool = False):
    feature = ln.Feature.filter(name=name).one_or_none()
    if feature is None:
        feature = ln.Feature(
            name=name,
            dtype=dtype,
            description=description,
            nullable=nullable,
        ).save()
    elif not (
        feature.dtype_as_str == "url"
        if dtype == "url"
        else feature.dtype_as_object == dtype
    ):
        msg = f"Feature {name!r} has dtype {feature.dtype_as_str!r}; expected {dtype!r}"
        raise RuntimeError(msg)
    return feature


def _schema(name: str, features: list[Any], *, index: Any):
    schema = ln.Schema.filter(name=name).one_or_none()
    if schema is None:
        schema = ln.Schema(features=features, index=index, name=name).save()
    return schema


def _record_type(name: str, schema: Any):
    record_type = ln.Record.filter(name=name, is_type=True).one_or_none()
    if record_type is None:
        record_type = ln.Record(name=name, is_type=True, schema=schema).save()
    elif record_type.schema_id != schema.id:
        msg = f"Record type {name!r} exists with a different schema"
        raise RuntimeError(msg)
    return record_type


def _ensure_record_types():
    monitor_id = _feature("sentry_uptime_monitor_id", str, "Sentry uptime detector ID.")
    monitor_name = _feature(
        "sentry_uptime_monitor_name", str, "Display name of the uptime monitor."
    )
    monitor_environment = _feature(
        "sentry_uptime_environment", str, "Sentry environment monitored."
    )
    monitor_url = _feature("sentry_uptime_url", "url", "URL monitored by Sentry.")
    monitor_method = _feature(
        "sentry_uptime_method", str, "HTTP method used by the uptime monitor."
    )
    monitor_interval = _feature(
        "sentry_uptime_interval_seconds",
        int,
        "Configured interval between uptime checks in seconds.",
    )
    monitor_last_check = _feature(
        "sentry_uptime_last_archived_check_at",
        datetime,
        "Latest check archived for this monitor in UTC.",
        nullable=True,
    )
    monitor_schema = _schema(
        MONITOR_SCHEMA_NAME,
        [
            monitor_name,
            monitor_environment,
            monitor_url,
            monitor_method,
            monitor_interval,
            monitor_last_check.with_config(optional=True),
        ],
        index=monitor_id,
    )
    monitor_type = _record_type(MONITOR_TYPE_NAME, monitor_schema)

    check_id = _feature("sentry_uptime_check_id", str, "Unique Sentry uptime check ID.")
    check_monitor = _feature(
        "sentry_uptime_monitor",
        monitor_type,
        "Uptime monitor that produced this check.",
    )
    check_timestamp = _feature(
        "sentry_uptime_checked_at", datetime, "Time Sentry recorded the check in UTC."
    )
    scheduled_timestamp = _feature(
        "sentry_uptime_scheduled_at", datetime, "Scheduled check time in UTC."
    )
    check_status = _feature(
        "sentry_uptime_status", str, "Sentry check status such as success or failure."
    )
    status_reason = _feature(
        "sentry_uptime_status_reason",
        str,
        "Reason supplied for a failed check.",
        nullable=True,
    )
    http_status = _feature(
        "sentry_uptime_http_status_code",
        int,
        "HTTP response status code.",
        nullable=True,
    )
    duration = _feature(
        "sentry_uptime_duration_ms", int, "End-to-end check duration in milliseconds."
    )
    region = _feature(
        "sentry_uptime_region", str, "Sentry region that executed the check."
    )
    region_name = _feature(
        "sentry_uptime_region_name", str, "Display name of the Sentry region."
    )
    check_environment = _feature(
        "sentry_uptime_check_environment",
        str,
        "Sentry environment recorded on the check.",
    )
    incident_status = _feature(
        "sentry_uptime_incident_status", int, "Sentry incident state for the check."
    )
    assertion_failure = _feature(
        "sentry_uptime_assertion_failure",
        dict,
        "Structured assertion failure details.",
        nullable=True,
    )
    trace_id = _feature(
        "sentry_uptime_trace_id", str, "Sentry trace ID for troubleshooting."
    )
    trace_item_id = _feature(
        "sentry_uptime_trace_item_id", str, "Sentry trace item ID."
    )
    check_schema = _schema(
        CHECK_SCHEMA_NAME,
        [
            check_monitor,
            check_timestamp,
            scheduled_timestamp,
            check_status,
            status_reason.with_config(optional=True),
            http_status.with_config(optional=True),
            duration,
            region,
            region_name,
            check_environment,
            incident_status,
            assertion_failure.with_config(optional=True),
            trace_id,
            trace_item_id,
        ],
        index=check_id,
    )
    check_type = _record_type(CHECK_TYPE_NAME, check_schema)
    return monitor_type, check_type


def _upsert_monitor(
    monitor_type: Any,
    monitor: JsonObject,
    *,
    last_archived_check_at: datetime | None = None,
):
    monitor_id = str(monitor["id"])
    record = ln.Record.filter(type=monitor_type, name=monitor_id).one_or_none()
    if record is not None and last_archived_check_at is None:
        last_archived_check_at = record.features.get_values().get(
            "sentry_uptime_last_archived_check_at"
        )
    values = {
        "sentry_uptime_monitor_id": monitor_id,
        "sentry_uptime_monitor_name": monitor["name"],
        "sentry_uptime_environment": monitor["environment"],
        "sentry_uptime_url": monitor["url"],
        "sentry_uptime_method": monitor["method"],
        "sentry_uptime_interval_seconds": monitor["intervalSeconds"],
    }
    if last_archived_check_at is not None:
        values["sentry_uptime_last_archived_check_at"] = last_archived_check_at
    if record is None:
        record = ln.Record(type=monitor_type, features=values).save()
    else:
        record.features.set_values(values)
    return record


def _parse_timestamp(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is not None:
        timestamp = timestamp.astimezone(UTC).replace(tzinfo=None)
    return timestamp


def _get_monitor_for_fetch(monitor_type: Any, monitor: JsonObject):
    from django.db import transaction

    with transaction.atomic():
        ln.Record.objects.select_for_update().get(id=monitor_type.id)
        return _upsert_monitor(monitor_type, monitor)


def _get_fetch_start(
    monitor_record: Any, end: datetime, overlap_minutes: int
) -> datetime:
    last_check = monitor_record.features.get_values().get(
        "sentry_uptime_last_archived_check_at"
    )
    if last_check is None:
        return end - timedelta(minutes=overlap_minutes)
    return last_check.replace(tzinfo=UTC) - timedelta(minutes=overlap_minutes)


def _save_new_checks(
    check_type: Any, monitor_record: Any, checks: list[JsonObject]
) -> int:
    check_ids = [str(check["uptimeCheckId"]) for check in checks]
    if not check_ids:
        return 0
    existing_ids = set(
        ln.Record.filter(type=check_type, name__in=check_ids).values_list(
            "name", flat=True
        )
    )
    records = []
    for check in checks:
        check_id = str(check["uptimeCheckId"])
        if check_id in existing_ids:
            continue
        values = {
            "sentry_uptime_check_id": check_id,
            "sentry_uptime_monitor": monitor_record,
            "sentry_uptime_checked_at": _parse_timestamp(check["timestamp"]),
            "sentry_uptime_scheduled_at": _parse_timestamp(check["scheduledCheckTime"]),
            "sentry_uptime_status": check["checkStatus"],
            "sentry_uptime_duration_ms": check["durationMs"],
            "sentry_uptime_region": check["region"],
            "sentry_uptime_region_name": check["regionName"],
            "sentry_uptime_check_environment": check["environment"],
            "sentry_uptime_incident_status": check["incidentStatus"],
            "sentry_uptime_trace_id": check["traceId"],
            "sentry_uptime_trace_item_id": check["traceItemId"],
        }
        if check.get("checkStatusReason") is not None:
            values["sentry_uptime_status_reason"] = check["checkStatusReason"]
        if check.get("httpStatusCode") is not None:
            values["sentry_uptime_http_status_code"] = check["httpStatusCode"]
        if check.get("assertionFailureData") is not None:
            values["sentry_uptime_assertion_failure"] = check["assertionFailureData"]
        records.append(ln.Record(type=check_type, features=values))
    if records:
        ln.save(records)
    return len(records)


def _save_monitor_checks(
    monitor_type: Any,
    check_type: Any,
    monitor: JsonObject,
    checks: list[JsonObject],
) -> int:
    from django.db import transaction

    with transaction.atomic():
        ln.Record.objects.select_for_update().get(id=monitor_type.id)
        monitor_record = _upsert_monitor(monitor_type, monitor)
        imported = _save_new_checks(check_type, monitor_record, checks)
        if checks:
            latest_check = max(_parse_timestamp(check["timestamp"]) for check in checks)
            current_last_check = monitor_record.features.get_values().get(
                "sentry_uptime_last_archived_check_at"
            )
            if current_last_check is None or latest_check > current_last_check:
                _upsert_monitor(
                    monitor_type,
                    monitor,
                    last_archived_check_at=latest_check,
                )
        return imported


@ln.flow()
def lamin_executable_export_sentry_uptime(
    organization_id: str,
    sentry_organization: str,
    sentry_project: str,
    environment: str,
    lookback_minutes: int = 60,
) -> dict[str, int]:
    """Import recent Sentry uptime results into the connected LaminDB instance."""
    if lookback_minutes <= 0:
        msg = "lookback_minutes must be positive"
        raise ValueError(msg)

    token = _read_sentry_token(organization_id)
    monitors = _list_monitors(token, sentry_organization, sentry_project, environment)
    monitor_type, check_type = _ensure_record_types()
    end = datetime.now(UTC)

    imported = 0
    seen = 0
    for monitor in monitors:
        monitor_record = _get_monitor_for_fetch(monitor_type, monitor)
        start = _get_fetch_start(monitor_record, end, lookback_minutes)
        checks = _list_checks(
            token,
            sentry_organization,
            sentry_project,
            str(monitor["id"]),
            start,
            end,
        )
        seen += len(checks)
        imported += _save_monitor_checks(monitor_type, check_type, monitor, checks)

    return {"monitors": len(monitors), "checks_seen": seen, "checks_imported": imported}

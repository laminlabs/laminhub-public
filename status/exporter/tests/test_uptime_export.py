from datetime import UTC, datetime

import pytest

from lamin_status.uptime_export import (
    _get_all_pages,
    _list_checks,
    _list_monitors,
    _parse_timestamp,
)


def test_lists_active_monitors_and_paginates_checks():
    calls = []

    def get_json(url, token, params):
        calls.append((url, token, params))
        if "/organizations/" in url:
            return (
                [
                    {"id": "active", "status": "active"},
                    {"id": "disabled", "status": "disabled"},
                ],
                {},
            )
        if "cursor=next" in url:
            return ([{"uptimeCheckId": "second"}], {})
        return (
            [{"uptimeCheckId": "first"}],
            {
                "Link": (
                    "<https://us.sentry.io/api/0/checks/?cursor=next>; "
                    'rel="next"; results="true"'
                )
            },
        )

    monitors = _list_monitors(
        "token", "example-org", "example-project", "staging", get_json=get_json
    )
    checks = _list_checks(
        "token",
        "example-org",
        "example-project",
        "monitor-id",
        datetime(2026, 9, 24, 8, tzinfo=UTC),
        datetime(2026, 9, 24, 9, tzinfo=UTC),
        get_json=get_json,
    )

    assert monitors == [{"id": "active", "status": "active"}]
    assert [check["uptimeCheckId"] for check in checks] == ["first", "second"]
    assert calls[0][2] == {
        "project": "example-project",
        "environment": "staging",
        "per_page": 100,
    }
    assert calls[-1][2] is None
    assert _parse_timestamp("2026-09-24T12:00:01+02:00") == datetime(
        2026, 9, 24, 10, 0, 1
    )


def test_rejects_repeated_pagination_link():
    url = "https://us.sentry.io/api/0/checks/"

    def get_json(url, token, params):
        return [], {"Link": f'<{url}>; rel="next"; results="true"'}

    with pytest.raises(RuntimeError, match="pagination did not terminate"):
        _get_all_pages(url, "token", get_json=get_json)

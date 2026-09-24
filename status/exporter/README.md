# lamin-status

Public status data and UI for Lamin.

The first component is a scheduled Lamin Transform that imports Sentry uptime
checks into `laminlabs/lamin-qms` as records. The public status UI will be added
after the historical data pipeline is running.

## Uptime exporter

`lamin_status/uptime_export.py` is a self-contained Transform source. It:

- discovers active uptime monitors for a Sentry project and environment;
- reads their check history with pagination;
- stores monitor metadata and immutable check results as LaminDB records;
- skips checks that already exist, allowing overlapping scheduled runs.

The scheduled job should invoke:

```text
lamin_executable_export_sentry_uptime
```

with these parameters:

```json
{
  "organization_id": "<lamin-organization-uuid>",
  "sentry_organization": "<sentry-organization-slug>",
  "sentry_project": "<sentry-project-slug>",
  "environment": "staging",
  "lookback_minutes": 60
}
```

Run the Transform manually once before creating a five-minute
(`*/5 * * * *`) Lambda trigger. After the first run, each monitor resumes from
its latest archived check with a one-hour overlap. This fills gaps after a
scheduler outage, while check IDs prevent duplicate records.

The bot running the Transform needs organization-admin access to read the
`sentry-uptime-read-token` organization secret and direct write access to the
`laminlabs/lamin-qms` instance.

Sentry currently marks the uptime monitor and check-history endpoints as
experimental. A failed Transform run therefore needs an alert so API changes or
authentication failures do not silently interrupt the archive.

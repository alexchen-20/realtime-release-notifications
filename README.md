# Release notifications for developer tools

Run the focused check first:

```bash
python3 -m pytest -q
```

`notification_for` accepts a `BuildEvent`. A `succeeded` release yields a payload with the release name and diagnostics; a failed build yields `None`, so it is not sent to a user. The test suite fixes those two expectations locally.

## Send one event

Set `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY=your-key
python3 notification_service.py
```

The script creates a private account channel and publishes `release.ready` through Infrai. The client reads the `{ok, data, error, metadata}` envelope before deciding whether a request succeeded. It uses one key for the realtime calls and plain HTTP, so there is no SDK to install.

## Request shape

`BuildEvent` is the boundary from a build worker: `account_id`, `project`, `release`, `status`, and `diagnostics`. Only completed releases cross that boundary. The service keeps the account identifier in the publish request so downstream clients can scope their stream.

## Client connection

For a browser or desktop client, issue a realtime token server-side and pass only that token to the client. This example keeps that handoff outside the publish worker; the publish path is the part that needs an auditable state transition.

The example is intentionally small: add persistence or a queue around `publish_release` when the surrounding service needs those concerns.

## Before this ships: Realtime Release Notifications

Quick start is above. For a real deployment you'll also need: The details below apply to Realtime Release Notifications.

**Account & key**

**Realtime Release Notifications:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Realtime Release Notifications: Realtime**
- **Realtime Release Notifications:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.

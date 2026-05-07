# ADR-003: Unify Server Configuration into a Single Parameter

**Date:** 2026-05-07
**Status:** Accepted
**Deciders:** Jose Antonio Chavarría

---

## Context

The `migasfree.conf` file had three separate parameters to define the server connection:

| Parameter  | Description              | Default  |
| ---------- | ------------------------ | -------- |
| `Server`   | Hostname or IP           | `localhost` |
| `Protocol` | `http` or `https`        | `http`   |
| `Port`     | TCP port number          | (none)   |

This split had two practical problems:

1. **Redundant surface.** Port and scheme are part of a URL by convention. Splitting them into three keys forces users to reason about something that is naturally a single value.
2. **Misleading default.** `Protocol = http` is wrong for production against migasfree server v5, which always exposes HTTPS via HAProxy (see `migasfree-swarm/build/proxy/defaults/etc/haproxy/haproxy.template`). The mTLS flow in `config.py` already overrides whatever the user sets by calling `_enable_mtls()` → `self.migas_protocol = 'https'`.

## Decision

Remove `Protocol` and `Port` as independent parameters. The `Server` parameter is extended to accept:

```txt
host
host:port
https://host
https://host:port
http://host:port
```

Parsing is done in `MigasFreeCommand._parse_server()` using `urllib.parse.urlparse`. When no scheme is present, `https` is assumed as the default.

The legacy environment variables `MIGASFREE_CLIENT_PROTOCOL` and `MIGASFREE_CLIENT_PORT` are removed. The unified `MIGASFREE_CLIENT_SERVER` variable covers all use cases.

## Backward Compatibility

To ensure zero-disruption for existing deployments, the client implements **two automatic compatibility layers** that activate transparently at startup:

### Layer 1 – Automatic config file migration (disk)

`utils.migrate_legacy_server_config(conf_file)` is called at startup. If the file contains active (non-commented) `Protocol` or `Port` keys, it:

1. Reads the current `Server`, `Protocol`, and `Port` values.
2. Builds the unified URL: `{protocol}://{server}:{port}`.
3. Rewrites the `Server` line in-place.
4. Comments out the obsolete `Protocol` and `Port` lines with a `# migrated to Server` note.
5. Preserves all other lines, comments, and whitespace verbatim.

**Before (automatic migration):**

```ini
[client]
Server   = migasfree.example.com
Protocol = https
Port     = 8443
```

**After (automatic migration):**

```ini
[client]
Server   = https://migasfree.example.com:8443
# Protocol = https  # migrated to Server
# Port     = 8443  # migrated to Server
```

This migration runs silently when the process has write access to the config file (typically when running as root). An `INFO` log entry is emitted.

### Layer 2 – In-memory merge (runtime fallback)

If the file could not be rewritten (read-only filesystem, insufficient permissions, or env var override), the client reads any remaining `Protocol` / `Port` values from:

- Config keys: `_config_client.get('protocol')` / `_config_client.get('port')`
- Legacy env vars: `MIGASFREE_CLIENT_PROTOCOL` / `MIGASFREE_CLIENT_PORT`

These are merged into `_raw_server` before calling `_parse_server()`. A `WARNING` log entry is emitted asking the user to update the config manually.

Both layers are **non-destructive**: they never remove content, only comment it out or merge in memory.

## Why `Package_Proxy_Cache` Was Kept

`Package_Proxy_Cache` was reviewed and **retained**. It serves a functionally different purpose: it rewrites the base URL of APT/DNF repository entries to route package downloads through an intermediate caching proxy (e.g., `apt-cacher-ng`). This is independent of the mTLS/HTTPS connection to the migasfree API, and the swarm provides no built-in equivalent.

## Consequences

### Positive

- Configuration surface reduced from 3 parameters to 1 for server address.
- Default is now `https`, matching production reality for v5.
- Users can express non-standard ports naturally (`host:8443`), the same way browsers and other tools do.

### Negative / Migration

- Existing `migasfree.conf` files with `Protocol` or `Port` parameters will silently ignore those keys (the INI parser does not error on unknown keys). The `Server` parameter must be updated if a non-default port is used.
- The environment variables `MIGASFREE_CLIENT_PROTOCOL` and `MIGASFREE_CLIENT_PORT` are no longer read. Deployments using them must migrate to `MIGASFREE_CLIENT_SERVER=https://host:port`.

## Migration Guide

**Before (v5.0):**

```ini
[client]
Server   = migasfree.example.com
Protocol = https
Port     = 8443
```

**After (v5.1+):**

```ini
[client]
Server = https://migasfree.example.com:8443
```

Standard ports (80 for http, 443 for https) do not need to be specified:

```ini
[client]
Server = migasfree.example.com
```

## See Also

- [Configuration Reference](../reference/configuration.md)
- [Environment Variables](../reference/environment-variables.md)
- [ADR-001: mTLS Authentication](001-mtls-authentication.md)

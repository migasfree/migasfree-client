# CLI Command: conf

> **Namespace:** `migasfree conf`
> **Access Privilege:** **Root / Administrator**
> **Scope:** Multi-platform (Linux & Windows)

---

## 1. Overview

The `conf` subcommand allows administrators to view, set, or modify the local `migasfree-client` configurations directly via the command-line interface. This ensures automated configuration updates can be run programmatically without manually parsing or editing the configuration file on disk.

---

## 2. CLI Usage Reference

```bash
migasfree conf [options]
```

### Options

If no options are passed, `migasfree conf` outputs the entire active configuration parameters of the client.

| Parameter | Accepted Values | Target Config Key | Description |
| :--- | :--- | :--- | :--- |
| `-s`, `--server` | `String (URL/Host)` | `Server` | Sets the full address of the Migasfree Server. |
| `-p`, `--project` | `String` | `Project` | Sets the name of the project repository channel. |
| `-a`, `--auto-update-packages` | `true`, `false` | `Auto_Update_Packages` | Enables or disables automatic mandatory package upgrades. |
| `-m`, `--manage-devices` | `true`, `false` | `Manage_Devices` | Enables or disables logical printer provisioning. |
| `-u`, `--upload-hardware` | `true`, `false` | `Upload_Hardware` | Toggles detailed hardware inventory collection. |
| `-c`, `--computer-name` | `String` | `Computer_Name` | Overrides local hostname reporting. |
| `--debug-mode` | `true`, `false` | `Debug` | Toggles verbose debugging in log files. |
| `-x`, `--proxy` | `String` | `Proxy` | Configures HTTP/HTTPS network proxy. |
| `-k`, `--package-proxy-cache` | `String` | `Package_Proxy_Cache` | Configures proxy cache address for package downloads. |

---

## 3. Business Rules & Configuration Migration

> [!WARNING]
>
> - **Legacy Settings Migration**: The client contains double-layer backwards compatibility for legacy configurations.
>   - **Layer 1 (On-disk Migration)**: When parsing configurations, the client automatically translates legacy settings (e.g. `Protocol` and `Port` keys) on disk into a unified `Server = <protocol>://<host>:<port>` parameter, rewriting the configuration file safely.
>   - **Layer 2 (In-memory Merge)**: If the configuration file is read-only, legacy settings are merged in memory, printing warning messages to instruct administrators to update parameters to the modern unified format.

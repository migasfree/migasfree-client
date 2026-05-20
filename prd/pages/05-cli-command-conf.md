# CLI Command: conf

> **Namespace:** `migasfree conf`
> **Access Privilege:** **Root / Administrator**
> **Scope:** Multi-platform (Linux & Windows)

---

## 1. Overview

The `conf` subcommand allows administrators to view, set, modify, or **reset** the local `migasfree-client` configurations directly via the command-line interface. This ensures automated configuration updates can be run programmatically without manually parsing or editing the configuration file on disk.

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
| `-c`, `--computer-name` | `String` or `""` | `Computer_Name` | Overrides local hostname reporting. Pass `""` to reset to system hostname. |
| `--debug-mode` | `true`, `false` | `Debug` | Toggles verbose debugging in log files. |
| `-x`, `--proxy` | `String` or `""` | `Proxy` | Configures HTTP/HTTPS network proxy. Pass `""` to disable. |
| `-k`, `--package-proxy-cache` | `String` or `""` | `Package_Proxy_Cache` | Configures proxy cache address for package downloads. Pass `""` to disable. |

---

## 3. Resetting Optional Parameters

Certain optional parameters can be **reset to their default value** by passing an empty string `""`. When reset, the configuration key is **commented out** in `/etc/migasfree.conf`, which restores the built-in default behaviour without requiring manual file editing.

**Resettable parameters:**

| Parameter | Default when reset |
| :--- | :--- |
| `--computer-name` | System hostname (`socket.getfqdn()`) |
| `--proxy` | No proxy (direct connection) |
| `--package-proxy-cache` | No proxy cache |

**Example — reset a custom computer name:**

```bash
migasfree conf --computer-name ""
```

This is equivalent to commenting out `Computer_Name` in the configuration file:

```ini
[client]
Server = migasfree.example.com
Project = myproject
# Computer_Name = mcs-builder
```

> [!NOTE]
> Parameters that are **mandatory** (`Server`, `Project`) cannot be reset to empty — they will be rejected with a validation error.

---

## 4. Business Rules & Configuration Migration

> [!WARNING]
>
> - **Legacy Settings Migration**: The client contains double-layer backwards compatibility for legacy configurations.
>   - **Layer 1 (On-disk Migration)**: When parsing configurations, the client automatically translates legacy settings (e.g. `Protocol` and `Port` keys) on disk into a unified `Server = <protocol>://<host>:<port>` parameter, rewriting the configuration file safely.
>   - **Layer 2 (In-memory Merge)**: If the configuration file is read-only, legacy settings are merged in memory, printing warning messages to instruct administrators to update parameters to the modern unified format.

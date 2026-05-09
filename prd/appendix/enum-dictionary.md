# Enum & Constant Dictionary

This document aggregates system constants, CLI exit codes, and key configuration options defined within the `migasfree-client` codebase.

---

## 1. System Exit Codes

| Constant / Code | Numeric Value | Meaning | Description |
| :--- | :--- | :--- | :--- |
| `ALL_OK` | `0` | Success | Command completed successfully with no errors. |
| `EPERM` | `1` | Operation not permitted | Critical permission or cryptographic validation failure (e.g., failed to fetch/verify keys). |
| `ENOENT` | `2` | No such file or directory | Missing necessary directories, config file, or script paths. |
| `EACCES` | `13` | Permission denied | Local system file-write failures, or logging configuration issues. |
| `EAGAIN` | `11` | Resource temporarily unavailable | Server saturation or lock file conflict; retry required. |
| `ENODATA` | `61` | No data available | Missing server metadata, invalid computer ID, or missing registration information. |
| `EINPROGRESS` | `115` | Operation in progress | Interrupted by user signal (SIGINT, SIGTERM, SIGQUIT). Exit gracefully. |
| `EPROTO` | `71` | Protocol error | Package Management System (PMS) transaction failed or returned an error status. |

---

## 2. Configuration Settings (`migasfree.conf`)

Located at `/etc/migasfree.conf` on Linux and `%PROGRAMDATA%\migasfree-client\migasfree.conf` on Windows.

### `[client]` Section

| Parameter Name | Data Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `Server` | `String` | `localhost` | Full URL (scheme, host, port) of the Migasfree Server. |
| `Project` | `String` | Automatically discovered | Name of the deployment project. Used for package channels. |
| `Auto_Update_Packages` | `Boolean` | `True` | Determines whether the client automatically runs upgrades for mandatory packages. |
| `Manage_Devices` | `Boolean` | `True` | If `True`, enables automatic CUPS/Windows printer installation and matching. |
| `Upload_Hardware` | `Boolean` | `True` | Controls whether local hardware profiles are uploaded to the server inventory. |
| `Computer_Name` | `String` | Hostname | Override name used to identify this computer on the server. |
| `Debug` | `Boolean` | `False` | Toggles detailed debug logs in `/var/tmp/migasfree.log` or `%WINDIR%\temp\migasfree.log`. |
| `Proxy` | `String` | `None` | Network HTTP/HTTPS proxy to route API requests. |
| `Package_Proxy_Cache` | `String` | `None` | Proxy caching server address for package file downloads. |

### `[packager]` Section

| Parameter Name | Data Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `User` | `String` | `None` | Username of authorized package manager for file uploads. |
| `Password` | `String` | `None` | Password of package manager. |
| `Project` | `String` | `None` | Targeted repository project. |
| `Store` | `String` | `None` | Server-side directory to upload files to. |

---

## 3. CLI Subcommand Arguments & Mutual Exclusions

### Subcommand: `sync`

- `--force-upgrade` / `-f`: Forces package updates. Sets `auto_update_packages` to true in memory.
- Mutually exclusive synchronization filters (Only one allowed):
  - `--devices` / `-dev`: Run ONLY device (printer) synchronization.
  - `--hardware` / `-hard`: Run ONLY hardware inventory collection and upload.
  - `--software` / `-soft`: Run ONLY software inventory upload.
  - `--attributes` / `-att`: Run ONLY attribute evaluation and upload.
  - `--faults` / `-fau`: Run ONLY fault evaluation and upload.

### Subcommand: `tags`

- Mutually exclusive operations (Exactly one required):
  - `--get` / `-g`: Output currently assigned tags in JSON format.
  - `--set` / `-s`: Specify new tags to set in server.
  - `--communicate` / `-c`: Commits/reports tags to server.

### Subcommand: `upload`

- Mutually exclusive targets (Exactly one required):
  - `--file` / `-f`: Specific path of file/package to upload.
  - `--dir` / `-r`: Directory containing files/packages to upload.

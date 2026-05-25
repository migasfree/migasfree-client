# CLI Command: devices

> **Namespace:** `migasfree devices`
> **Access Privilege:** **Root / Administrator**
> **Scope:** Multi-platform (Linux & Windows)

---

## 1. Overview

The `devices` subcommand is the central interface for reading peripheral and logical device relationships assigned to the computer or globally available in the Migasfree backend. It replaces insecure direct RPC/Python bindings that were previously used by frontends, bringing the entire querying process into the secure mTLS scope.

---

## 2. CLI Usage Reference

```bash
migasfree devices [options]
```

> [!IMPORTANT]
> The `devices` command allows querying specific slices of the hardware inventory based on the flag provided. If no mutually exclusive operational flag is provided, it returns the **assigned devices** by default.

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-a`, `--available` | `Flag` | No | `False` | Retrieves physical devices available (unassigned) for connection. |
| `-l`, `--logical` | `Flag` | No | `False` | Retrieves logical device relationships. |
| `-c`, `--capabilities` | `String` | No | `None` | Retrieves hardware capabilities by specific capability ID. |
| `--device-id` | `String` | No | `None` | Used alongside `-l` to filter logical relations targeting a specific device ID. |
| `-j`, `--json` | `Flag` | No | `False` | Outputs the result in JSON format instead of human-readable text. |

---

## 3. Interaction Logic

### Get Assigned Devices (Default)

- **Trigger**: `migasfree devices`
- **Network call**: Uses standard REST call to `get_devices`.
- **System behavior**: Fetches currently assigned hardware via standard endpoints.

### Get Available Devices (`-a` / `--available`)

- **Trigger**: `migasfree devices -a`
- **Network call**: `POST` to `/api/v1/safe/devices/devices/available/` passing `cid` in the encrypted JSON body.
- **Outcome**: The backend `SafeDeviceViewSet` resolves devices not currently assigned and returns them encrypted.

### Get Logical Devices (`-l` / `--logical`)

- **Trigger**: `migasfree devices -l` (optionally with `--device-id ID`)
- **Network call**: `POST` to `/api/v1/safe/devices/logical/available/` passing `cid` and optionally `did` in the encrypted JSON body.
- **Outcome**: Resolves logical associations from `SafeLogicalViewSet`.

### Get Capabilities (`-c` / `--capabilities`)

- **Trigger**: `migasfree devices -c ID`
- **Network call**: `POST` to `/api/v1/safe/devices/capabilities/` passing `id` in the encrypted JSON body.
- **Outcome**: Fetches capability details from `SafeCapabilityViewSet` securely over mTLS.

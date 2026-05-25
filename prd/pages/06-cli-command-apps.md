# CLI Command: apps

> **Namespace:** `migasfree apps`
> **Access Privilege:** **Root / Administrator**
> **Scope:** Multi-platform (Linux & Windows)

---

## 1. Overview

The `apps` subcommand allows administrators and automated tools to query the migasfree backend catalog for applications available for the current registered computer. It leverages the secure mTLS \`/safe/\` namespace using JWE encrypted payloads to avoid unauthorized catalog enumeration.

---

## 2. CLI Usage Reference

```bash
migasfree apps [options]
```

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-c`, `--category` | `String` | No | `None` | Filters the returned available applications by a specific category ID. |
| `-j`, `--json` | `Flag` | No | `False` | Outputs the result in JSON format instead of human-readable text. |

---

## 3. Interaction Logic

### Get Available Apps

- **Trigger**: `migasfree apps` (optionally with `-c ID`)
- **Network call**: `POST` to `/api/v1/safe/catalog/apps/available/` passing the encrypted computer ID (`cid`) and optionally the category ID (`category`) inside the JWE encrypted request body.
- **System behavior**: Connects via mTLS using the system's client certificate and private key.
- **Outcome**: The backend `SafeApplicationViewSet` decrypts the payload, queries the database for apps available to the computer's project, encrypts the response, and returns it. The client unwraps it and outputs to `stdout`.

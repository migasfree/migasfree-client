# CLI Command: categories

> **Namespace:** `migasfree categories`
> **Access Privilege:** **Root / Administrator**
> **Scope:** Multi-platform (Linux & Windows)

---

## 1. Overview

The `categories` subcommand allows the system or administrator to retrieve the list of software categories defined in the migasfree catalog. Like `apps`, it relies on the safe mTLS infrastructure.

---

## 2. CLI Usage Reference

```bash
migasfree categories [options]
```

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-j`, `--json` | `Flag` | No | `False` | Outputs the result in JSON format instead of human-readable text. |

---

## 3. Interaction Logic

### Get Categories

- **Trigger**: `migasfree categories`
- **Network call**: `POST` to `/api/v1/safe/catalog/categories/` passing the encrypted computer ID (`cid`).
- **System behavior**: Connects via mTLS using the system's client certificate and private key.
- **Outcome**: The backend `SafeCategoryViewSet` decrypts the payload, queries the categories from the database, encrypts the response, and returns it. The client unwraps it and outputs to `stdout`.

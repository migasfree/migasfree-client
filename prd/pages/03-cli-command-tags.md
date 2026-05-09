# CLI Command: tags

> **Namespace:** `migasfree tags`
> **Access Privilege:** **Root / Administrator**
> **Scope:** Multi-platform (Linux & Windows)

---

## 1. Overview

Tags allow administrators to classify systems on the server. The `tags` subcommand lets the client read assigned tags, view available tags on the server, and assign custom tags to group systems dynamically.

---

## 2. CLI Usage Reference

```bash
migasfree tags [options]
```

> [!IMPORTANT]
> The `tags` command requires **exactly one** of the following mutually exclusive operation arguments:

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-g`, `--get` | `Flag` | Yes (if no other) | `False` | Retrieves and prints currently assigned tags from the server in JSON format. |
| `-s`, `--set` | `Array` | Yes (if no other) | `None` | Sets a list of specified tags on the server for the machine. |
| `-c`, `--communicate` | `Array` | Yes (if no other) | `None` | Commits/communicates system tags to the server database. |

---

## 3. Interaction Logic

### Get Assigned Tags (`-g` / `--get`)

- **Trigger**: `migasfree tags -g`
- **Network call**: `GET` to `/api/v1/safe/computers/tags/assigned/` passing computed computer ID.
- **System behavior**: Downloads tags list and outputs them to `stdout` in formatted JSON.

### Set Tags (`-s` / `--set`)

- **Trigger**: `migasfree tags -s tag1 tag2`
- **Validation**: Checks that specified tag names contain only alphanumeric characters, hyphens, or underscores.
- **Network call**: `POST` to `/api/v1/safe/computers/tags/` with data:

  ```json
  {
    "id": "[computer_id]",
    "tags": ["tag1", "tag2"]
  }
  ```

- **Outcome**: Overwrites previous tags assigned on the server. Prints confirmation status.

### Communicate Tags (`-c` / `--communicate`)

- **Trigger**: `migasfree tags -c tag1 tag2`
- **Network call**: `POST` to `/api/v1/safe/computers/tags/` with data, forcing a synchronization refresh on the server.

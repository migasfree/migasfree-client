# ADR-006: Stricter & More Resilient Security Keys Auto-Registration Flow

**Date:** 2026-05-16  
**Status:** Accepted  
**Deciders:** Alberto Gacías, Jose Antonio Chavarría  

---

## Context

During the initial bootstrap phase, `migasfree-client` must discover or generate standard security keys (a project private key and server public key) to sign and encrypt subsequent communications.

In previous versions, the auto-registration flow was highly fragile:

1. If the GPG signing keys were missing, the client printed a warning log at a loud `WARNING` level with excessive exclamation marks (`Security keys are not present!!!`).
2. The client would trigger auto-registration. If `_save_computer` (the server-side step to save the computer record) failed or returned a falsy ID, the client would immediately exit, even if the signing keys had been successfully downloaded and stored.
3. This rigid behavior caused synchronization tasks to fail entirely during minor server hiccups or temporary registration constraints, even when the machine now possessed all the necessary keys to authenticate and execute standard commands.
4. Furthermore, once keys were created, the client did not store the computer ID in-memory immediately, triggering duplicate redundant `get_computer_id` requests in subsequent execution phases.

## Decision

Re-engineer the auto-registration sequence to make it resilient to temporary server-side save issues, optimize API roundtrips, and professionalize CLI output.

### 1. Robust Continuation on Key Possession

Modify the validation block in `MigasFreeCommand._check_sign_keys()`:

* If keys are missing, download them via `_auto_register()`.
* Re-evaluate the existence of the GPG key files on disk directly after the download attempt.
* If the files successfully exist on disk, return `True` (allowing client execution to proceed), regardless of whether the `_save_computer` API step reported success or failed with a falsy value.
* If subsequently executing subcommands require a computer ID, the existing `require_computer_id` decorator will lazily recover or retry registering the computer ID in-memory.

### 2. Direct Computer ID Caching

Directly store the returned computer ID to `self._computer_id` during the successful `_auto_register` flow:

```python
if self._save_sign_keys(self.auto_register_user, self.auto_register_password):
    self._computer_id = self._save_computer(self.auto_register_user, self.auto_register_password)
    return self._computer_id != 0
```

This ensures that the client caches the server-assigned computer ID immediately and avoids making redundant roundtrips to `/api/v1/safe/computers/id/` on subsequent decorators or commands.

### 3. Log & Text Refinement

* Eliminate unprofessional exclamation marks (e.g., changing `Error writing key file!!!` to `Error writing key file`) in system-wide messages.
* Downgrade the missing security keys log from `warning` to `info`, as missing keys on a brand-new computer installation is a perfectly standard, expected state rather than an operational anomaly.

## Consequences

### Positive

* **High Resiliency**: Computers that have successfully acquired their mTLS and JWS/JWE credentials can continue executing sync phases even if the computer-registry save endpoint had a temporary database lock or hiccup.
* **Network Efficiency**: Reduces redundant `/api/v1/safe/computers/id/` API requests immediately after registration.
* **Professional CLI Tone**: Standardized and refined log outputs present a cleaner, enterprise-grade interface.

### Negative / Limitations

* If a computer successfully downloads the keys but fails to register the hardware record on the server, the initial sync phase might see certain API tasks fail, but this is a standard, expected server-auth response.

## See Also

* [ADR-001: Mutual TLS (mTLS) for Client Authentication](001-mtls-authentication.md)
* [ADR-004: Command-Line Interface for Configuration Management](004-cli-configuration-management.md)

# ADR-005: Support for DEB822 (.sources) Repository Format in Modern APT

**Date:** 2026-05-16  
**Status:** Accepted  
**Deciders:** Alberto Gacías, Jose Antonio Chavarría  

---

## Context

Debian and Ubuntu distributions have introduced a new repository format, **DEB822** (using `.sources` files), to replace the legacy one-line format (using `.list` files). Modern package managers (starting with APT 3.0) prefer or natively use this structured format.

To align with modern system standards, `migasfree-client` needs a robust, transparent way to:

1. Detect whether the target system supports modern DEB822 configurations.
2. Upgrade repository configurations from the legacy `.list` syntax to the structured `.sources` format.
3. Handle repository signing keys (`Signed-By`) and other advanced repository options (e.g., `arch`, `check-valid-until`) seamlessly across formats.

Manual or direct parsing of legacy formats to DEB822 blocks in Python is complex and error-prone. We should leverage the package manager's native tools (like `apt modernize-sources`) while guaranteeing the sandboxed execution doesn't corrupt or modify system-wide configurations.

## Decision

Implement an automated, backward-compatible transition to the DEB822 `.sources` repository format when APT 3.0+ is detected.

### 1. Version Detection & Shell Reduction

Use Python's built-in `re` module to parse output from `apt --version` instead of launching fragile pipelines with shell utilities (such as `awk` or `sed`). If detection fails or is unavailable, default to APT 2.x behavior.

### 2. Sandboxed Modernization via `apt modernize-sources`

To avoid writing custom transpilars, the client invokes `apt modernize-sources` on a temporary file. The invocation is heavily secured using isolated settings:

* **Custom Environment**: Execute inside a secure `tempfile.TemporaryDirectory()` block.
* **Configuration Isolation**: Override APT's local config by passing `-o Dir::Etc::SourceList` and `-o Dir::Etc::SourceParts` pointed inside the sandboxed folder. This prevents `apt` from touching system-wide sources.
* **Safe Filesystem Guard**: Avoid referencing `/dev/null` directly as a source file during the conversion, preventing unintended truncation of the special device file when executed with root privileges.

### 3. Option Migration & Normalization

Since `apt modernize-sources` might strip custom fields or map them to empty parameters, a custom `_adapt_sources` parser runs directly after the conversion:

* Extrapolates options from the original repository template (e.g. `[arch=amd64]`, `[signed-by=...]`).
* Matches DEB822 blocks by URI and dynamically injects the appropriate parameters (like `Signed-By: <path>`, `Architectures: <arch>`) into the parsed block.
* Cleanly removes duplicate or non-active files (e.g., if `.sources` is generated and saved, any legacy `.list` configuration is automatically removed to prevent duplicate sources warnings).

## Consequences

### Positive

* **Modern Standards Compliance**: Leverages native DEB822 formats on modern distributions (Ubuntu 24.04+ and Debian Trixie+).
* **Robust Safety**: High-integrity execution sandbox preserves `/dev/null` and existing repository configuration files from corruption.
* **Metadata Integrity**: Advanced properties like `Signed-By` are accurately preserved and reformatted into the DEB822 block structure.
* **Seamless Fallback**: Gracefully degrades to writing legacy `.list` files if `apt modernize-sources` fails or the APT version is less than 3.0.

### Negative / Limitations

* **Increased Subprocess Call**: One additional lightweight subprocess is spawned to determine the APT version and run the modernization routine, but this only occurs when creating or updating repository layouts.

## See Also

* [ADR-001: Mutual TLS (mTLS) for Client Authentication](001-mtls-authentication.md)
* [ADR-003: Unify Server Configuration into a Single Parameter](003-unified-server-parameter.md)

# ADR-004: Command-Line Interface for Configuration Management

**Date:** 2026-05-07  
**Status:** Accepted  
**Deciders:** Jose Antonio Chavarría, AI Assistant  

---

## Context

Configuration in `migasfree-client` is managed via the `/etc/migasfree.conf` (or distribution-equivalent) INI file. Prior to this decision, administrators and automated scripts had to edit this configuration file manually (e.g., using `sed`, `awk`, or text editors). This manual approach presented several drawbacks:

1. **Error Prone**: Hand-editing INI files frequently introduces syntax errors, duplicated keys, or incorrect formatting.
2. **No Source Visibility**: Active configuration parameters could be defined in multiple places (environment variables, configuration files, or hardcoded defaults). There was no built-in mechanism to inspect active values and trace their precise origin at runtime.
3. **Destruction of Comments**: Automatic tools that parsed and wrote INI files would often strip comments, wipe formatting, or rearrange keys, making the configuration file difficult to read for humans.

## Decision

Introduce a dedicated `conf` subcommand (`migasfree conf`) to act as a unified, safe, and transparent interface for both inspecting and updating client configurations.

### 1. Unified Inspection (Reading)

Invoking `migasfree conf` without parameters outputs all active configuration options, their current values, and their provenance indicator:

* **`(ENV)`**: The parameter is set and overridden via an environment variable.
* **`(FILE)`**: The parameter is defined in the local configuration file.
* **`(DEFAULT)`**: The parameter is not explicitly defined, falling back to the client's internal default.

This logic is cleanly integrated into `RendererMixin._show_config_options()`.

### 2. Intelligent, Non-Destructive Update (Writing)

When write flags (e.g., `-s`, `-a`, `-x`) are passed, `migasfree-client` updates `migasfree.conf` following a non-destructive strategy:

* If the key already exists and is active, it is modified **in-place**.
* If the key is not active but is commented out as a template placeholder (e.g., `# Debug = True`), the new active key-value pair is inserted **directly below the comment**. This preserves the original file structure and groups parameters logically.
* If the key does not exist at all, it is appended to the end of the `[client]` section.

### 3. Comprehensive Parameter Validation

All parameters set via the CLI undergo strict validation (e.g., verifying that `Server` is a valid hostname/URL, `Computer_Name` complies with hostname RFC 1123, and `Proxy` matches `host:port` patterns) to guarantee the configuration remains syntactically valid and secure.

## Consequences

### Positive

* **Safety**: Administrators can configure clients programmatically and manually without risk of corrupting the configuration file.
* **Transparency**: The source indicators (`(ENV)`, `(FILE)`, `(DEFAULT)`) greatly simplify debugging configuration precedence issues.
* **Preserved File Layout**: Active configurations are cleanly grouped next to their commented template equivalents, maintaining maximum human readability.

### Negative / Limitations

* Writing to `/etc/migasfree.conf` requires elevated root/administrator privileges in production environments (as expected for system-wide configurations).

## See Also

* [ADR-003: Unify Server Configuration into a Single Parameter](003-unified-server-parameter.md)
* [Configuration Specification (conf.spec)](../governance/conf.spec)

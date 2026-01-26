# migasfree-client Project Context

This file provides project-specific context to enhance the AI agent's understanding of the migasfree-client codebase.

## Project Overview

migasfree-client is a **cross-platform systems management client** that synchronizes computers with a central migasfree server. It is used by organizations to:

- Deploy software packages to fleets of computers
- Manage hardware/software inventory
- Configure printers and devices
- Enforce configuration policies
- Track system faults and errors

### Primary Deployment

- **Organization**: Ayuntamiento de Zaragoza (Municipal Government)
- **Scale**: Hundreds to thousands of managed desktops
- **Platforms**: Debian-based Linux (AZLinux), Windows 10+

## Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `__main__.py` | CLI entry point, argument parsing |
| `sync.py` | Main synchronization logic (`MigasFreeSync` class) |
| `command.py` | Command execution and subprocess handling |
| `url_request.py` | HTTP client with auth and retry logic |
| `mtls.py` | mTLS certificate management |
| `secure.py` | Cryptographic utilities |
| `utils.py` | Shared utilities and helpers |
| `settings.py` | Configuration and constants |

### Plugin Architecture

**Package Management Systems** (`pms/`):
- Base class: `pms.py` - Abstract PMS interface
- Implementations: `apt.py`, `yum.py`, `dnf.py`, `zypper.py`, `pacman.py`, `apk.py`, `wpt.py`

**Device Management** (`devices/`):
- Base class: `__init__.py`
- Implementations: `printer.py`, `cupswrapper.py`

## Technical Requirements

- **Python Version**: 3.6+ (for compatibility with older systems)
- **Cross-Platform**: Must work on Linux and Windows
- **Security**: mTLS for server communication, secure credential handling

## Coding Conventions

- **Formatter**: Ruff with single quotes, 120 char line length
- **Linters**: ruff, flake8, mypy
- **Type hints**: Required for new code
- **Logging**: Use `logging.getLogger('migasfree_client')`

## Key Files for Reference

- `pyproject.toml` - Project configuration and dependencies
- `tests/` - Test suite (pytest)
- `conf/migasfree.conf` - Example configuration file

## Security Considerations

### Critical Areas to Review

1. **Code Execution** (`sync.py`): `_eval_code()` executes server-provided code
2. **mTLS Handling** (`mtls.py`): Certificate management and storage
3. **Subprocess Execution** (`command.py`): Command injection prevention
4. **Credential Storage**: `/var/migasfree-client/mtls/` (Linux), `%PROGRAMDATA%\migasfree-client\` (Windows)

### Best Practices for This Project

- Never log credentials or tokens
- Validate all server responses before use
- Use parameterized subprocess calls (lists, not shell strings)
- Check file permissions on sensitive files (600 for private keys)

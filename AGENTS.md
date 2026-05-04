# AGENTS.md

> **Context for AI Agents working on `migasfree-client`**
> This file provides the essential context, commands, and conventions for AI agents to work effectively on this project.

## 1. Project Overview

**migasfree-client** is the client-side component of the Migasfree Systems Management System. It synchronizes local computers with the Migasfree server for software deployment, hardware/software inventory, and device management.

- **Language**: Python 3.6+
- **Architecture**: CLI-based client with secure communication (mTLS, JWS, JWE).
- **Communication**: REST API.
- **Security**: Mutual TLS (mTLS) for identity, JSON Web Encryption/Signature for payloads.
- **Cross-Platform**: Linux (multiple distros) and Windows 10+.

## 2. Setup & Commands

Always use a virtual environment (e.g., `.venv`).

- **Install Dependencies**: `pip install -e .[dev]`
- **Run Client (Debug)**: `sudo migasfree sync -d` (requires installation or `PYTHONPATH` adjustment)
- **Run Tests**: `pytest`
- **Lint Code**: `ruff check .`
- **Format Code**: `ruff format .`
- **Build Package**: `python setup.py sdist bdist_wheel`

## 3. Code Style & Conventions

- **Compatibility**: Code MUST be compatible with **Python 3.6+**. Avoid features introduced in later versions (e.g., structural pattern matching).
- **Linter/Formatter**: Ruff is used for both linting and formatting.
- **Quote Style**: Single quotes (`'`) are preferred for strings as per `ruff` configuration.
- **CLI Design**: Follow the existing subcommand pattern in `migasfree_client.__main__`.
- **Error Handling**: Use the built-in logging system with appropriate levels (`DEBUG`, `INFO`, `ERROR`).

## 4. Architecture Standards

The project is organized into functional modules:

- **`migasfree_client`**: Main logic and CLI entry point.
- **`migasfree_client.devices`**: Hardware detection and peripheral management (printers).
- **`migasfree_client.pms`**: Package Management Systems abstraction (APT, DNF, WPT, etc.).
- **`migasfree_client.utils`**: Security (mTLS, JWE), networking, and common helpers.

## 5. Available Skills & Specialized Constraints

This project is supported by specialized AI Skills in `.agent/skills`. **ALWAYS** check and use these skills:

- **Python Language**: `python-expert` (Pythonic patterns, quality)
- **Bash & Scripting**: `bash-expert` (Automation and integration scripts)
- **Security**: `security-expert` (AppSec, mTLS, encryption)
- **QA & Testing**: `qa-expert` (Testing patterns, mocks)
- **CI/CD & DevOps**: `cicd-expert` (GitHub Actions, packaging)
- **Documentation**: `docs-expert` (Diátaxis, ADRs)

## 6. Critical Rules

1. **Python 3.6 Support**: DO NOT use Python features that break compatibility with version 3.6.
2. **Privileges**: Most client operations (`sync`, `register`) require root/admin privileges.
3. **mTLS Integrity**: Be careful when modifying the certificate handling logic in `utils/mtls.py`.
4. **PMS Safety**: Package management operations can be destructive. Always ensure safety checks are in place.
5. **Security First**: All communication with the server should be signed/encrypted as per protocol.
6. **Platform Detection Best Practices**: Always use the direct built-in platform detection helpers in `migasfree_client.utils` (`is_windows()`, `is_linux()`) instead of raw `sys.platform` or negations.

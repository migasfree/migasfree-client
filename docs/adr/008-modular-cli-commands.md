# ADR 008: Refactoring CLI Commands into a Modular Subpackage (cli)

## Status

Accepted

## Context

The `migasfree-client` project has grown to encompass many subcommand classes (such as `apps.py`, `attributes.py`, `conf.py`, `device.py`, `info.py`, `label.py`, `packages.py`, `sync.py`, `tags.py`, `upload.py`, and `usercheck.py`), all of which were previously located directly under the top-level `migasfree_client/` package directory.

This flat structure created several drawbacks:
- It cluttered the core package directory, mixing base utility classes (like `command.py` and `mtls.py`) with specific subcommand implementations.
- It reduced discoverability and code organization, making it harder for developers to distinguish core client library logic from user-facing command-line interface logic.
- It made dependency packaging less clean.

## Decision

We will isolate all CLI subcommand modules into a dedicated subdirectory/subpackage named `migasfree_client.cli`.

1. **Relocation**: Move `apps.py`, `attributes.py`, `conf.py`, `device.py`, `info.py`, `label.py`, `packages.py`, `sync.py`, `tags.py`, `upload.py`, and `usercheck.py` into `migasfree_client/cli/`.
2. **Package Initialization**: Create an empty `migasfree_client/cli/__init__.py` file to turn the folder into a valid Python subpackage.
3. **Import Updates**: Update internal relative imports inside each command module to target their parent package directory (e.g. changing `from .command import ...` to `from ..command import ...`).
4. **Main Entrypoint**: Update the dynamic module loading mechanism in `migasfree_client/__main__.py` to import commands from `migasfree_client.cli.<command>` instead of `migasfree_client.<command>`.
5. **Test Adaptation**: Update import paths across all corresponding test suites (under `tests/unit/`) to point to the new CLI modules path.
6. **Packaging & Distribution**: Register `'migasfree_client.cli'` / `"migasfree_client.cli"` within BOTH `setup.py` and `pyproject.toml` to guarantee that all submodules are included in binary distributions and pip installs.
7. **Translation Support**: Update paths inside `po/POTFILES` (relative to the `po/` directory) and run `make -C po update-po` to keep translation extraction functional and accurate.

## Consequences

### Positive

- **Clarity & Separation of Concerns**: Clean isolation between core systems administration libraries and individual command implementation files.
- **Improved Maintainability**: Clear, structured architecture where adding a new subcommand simply involves dropping a module into `migasfree_client/cli/` and updating references.
- **Backward Compatibility**: Fully preserved command invocation syntax and internal behavior without exposing internal path shifts to the end users or integrations.

### Negative

- **Packaging Overhead**: Developers must remember to maintain packaging configurations in both `setup.py` and `pyproject.toml` to ensure the subpackage files are distributed correctly.

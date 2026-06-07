# ADR 009: Isolated Python Script Execution in Frozen Environments

## Status

Accepted

## Context

The `migasfree-client` evaluates dynamic Python traits and faults supplied by the server via the `CodeEvaluatorMixin._eval_code` helper. On Windows platforms, `migasfree-client` is packaged and distributed as a standalone frozen executable (`migasfree.exe`) using `cx_Freeze`. In this environment:

1. `sys.executable` points to the `migasfree.exe` binary rather than a standard `python.exe` interpreter.
2. There is no guarantee that a system-wide Python interpreter is installed on the host workstation.
3. Spawning a script execution subprocess using `[sys.executable, filename]` invokes `migasfree.exe <temp_file_path>`. The client's parser fails with a choice syntax error because `<temp_file_path>` is not a registered subcommand of the CLI.
4. Spawning scripts directly requires a clean, robust, and isolated execution model that doesn't leak process contexts or crash the main execution loop.

## Decision

We will introduce a dedicated internal subcommand `eval` to `migasfree-client` and route all Python script execution processes through it when running inside a frozen application context on Windows.

1. **Subcommand Registration**: Add an internal `eval` subcommand (`migasfree eval <file>`) to the CLI entrypoint (`migasfree_client/__main__.py`).
2. **Script Runner**: Implement the subcommand using the standard library `runpy.run_path` function to evaluate arbitrary scripts inside the client's built-in Python environment.
3. **Clean Environment Isolation**: Override `sys.argv` to contain only the script file path `[args.file]` immediately before execution, protecting the script from getting confused by CLI arguments.
4. **Frozen Application Detection**: In the evaluator mixin (`migasfree_client/mixins/evaluator.py`), inspect the `getattr(sys, 'frozen', False)` flag on Windows:
   - **If frozen (`True`)**: Spawns the subprocess as `[sys.executable, 'eval', filename]`.
   - **If unfrozen (`False`)**: Spawns the subprocess as `[sys.executable, filename]` (utilizing the executing `python.exe` interpreter).
5. **Linux Isolation**: Keep the existing path for Linux, invoking the script through the standard `python3` command.

## Consequences

### Positive

- **Zero-Dependency Execution**: Python trait/fault script evaluation runs perfectly on target systems even when Python is not globally installed.
- **Process Isolation**: Execution occurs in a separate subprocess, ensuring script-level issues (crashes, memory leaks, timeouts) do not terminate the parent synchronizing process.
- **Standard Compatibility**: Keeps developers and test suites running smoothly via source execution on all operating systems without needing compiled binaries.

### Negative

- **argparse Subcommand Choice Exposure**: The `eval` subcommand becomes technically visible in choices if CLI arguments fail parsing (though it is clearly marked as an internal helper tool in help descriptions).

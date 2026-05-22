# ADR 007: Disable Console Line-Wrapping for Machine-Readable Output (JSON)

## Status

Accepted

## Context

The `migasfree-client` CLI tool is not only run directly by system administrators, but is also invoked as a subprocess by external integrations, notably the desktop graphical interface `migasfree-play` (an Electron/NodeJS application). These integrations capture the standard output (`stdout`) of the CLI commands (e.g., `migasfree info --json`) and parse the resulting data stream (using `JSON.parse(result)`).

The client uses the `rich` Python library's `Console` class for styled terminal rendering. By default, `rich.Console.print()` automatically word-wraps printed text to fit the terminal boundary. In non-TTY environments (such as Node's `child_process` pipe), `rich` falls back to a default fixed width of 80 or 100 characters and inserts literal physical newline (`\n`) characters to break long strings.

For JSON outputs, this auto-wrapping breaks compliance with the RFC 8259 specification, which strictly forbids raw control characters (including unescaped newlines) within string literals. For example, a long CPU string would be wrapped physically:

```json
"cpu": "Intel Core i3-9100   
3.60GHz"
```

When parent processes attempt to parse this output, standard JSON parsers throw a `SyntaxError: Bad control character in string literal` and fail, causing integration errors such as `"Computer info unavailable"`.

## Decision

We will explicitly disable auto-wrapping when printing machine-readable data payloads (specifically JSON outputs) in `migasfree-client` commands.

1. **Implementation**: Pass the `soft_wrap=True` keyword argument to all `self.console.print()` invocations that output JSON formatted strings.
2. **Coverage**: Apply this systematically to:
   - `info` command (`migasfree_client/info.py`) when the `--json` flag is provided.
   - `label` command (`migasfree_client/label.py`) when the `--json` flag is provided.
   - `tags` command (`migasfree_client/tags.py`) when querying tags.
   - `sync/traits` commands (`migasfree_client/sync.py`) when exporting traits.
3. **Preservation**: Normal, human-readable terminal commands and tables will continue to use standard auto-wrapping for optimal CLI visual layout.

## Consequences

### Positive

- **Standard Compliance**: Standard output JSON payloads are guaranteed to be single-line, perfectly formed, valid JSON strings.
- **Robust Integration**: Complete resolution of parsing errors in parent callers (such as Electron or automated monitoring scripts).
- **Surgical Impact**: Only affects machine-readable outputs, preserving the rich, beautiful wrapping behaviour for human-interactive terminal views.

### Negative

- **Developer Vigilance**: Developers must remember to add the `soft_wrap=True` parameter to `console.print` whenever creating a new command or endpoint that outputs JSON or structured data intended for machine consumption.

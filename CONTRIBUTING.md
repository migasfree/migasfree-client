# Contributing to Migasfree Client

Thank you for your interest in contributing to Migasfree Client! We welcome contributions from the community.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/your-username/migasfree-client.git
    cd migasfree-client
    ```
3.  **Set up a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
4.  **Install dependencies**:
    ```bash
    pip install --upgrade pip
    pip install -e .[dev]
    ```

## Development Workflow

1.  Create a new branch for your feature or bugfix:
    ```bash
    git checkout -b my-feature-branch
    ```
2.  Make your changes.
3.  Ensure your code follows the project's style and passes all checks.

## Testing

We use `pytest` for testing. Run the full test suite with:

```bash
pytest
```

Ensure all tests pass before submitting your changes.

## Code Style and Quality

We use `ruff` for linting and formatting, and `mypy` for static type checking.

### Linting & Formatting

Check for linting errors:

```bash
ruff check .
```

Format your code:

```bash
ruff format .
```

### Type Checking

Run type checks:

```bash
mypy .
```

## Submitting a Pull Request

1.  Push your branch to your fork:
    ```bash
    git push origin my-feature-branch
    ```
2.  Open a Pull Request against the `master` (or `REST-API`) branch on the original repository.
3.  Describe your changes clearly in the PR description.
4.  Wait for review and address any feedback.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on the GitHub repository.

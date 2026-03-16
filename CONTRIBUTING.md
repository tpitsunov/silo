# Contributing to SILO

Thank you for your interest in improving the SILO Framework! We welcome contributions of all kinds — from fixing typos in documentation to implementing new security features.

## How to Contribute

### 1. Reporting Bugs
- Use the [GitHub Issue Tracker](https://github.com/tpitsunov/silo-framework/issues).
- Provide a clear description of the bug and steps to reproduce it.

### 2. Feature Requests
- Open an issue titled "Feature Request: [Your Idea]".
- Describe the use case and how it benefits SILO users.

### 3. Submitting Pull Requests
1. **Fork the repository** and create your branch from `main`.
2. **Install dependencies**:
   ```bash
   uv pip install -e .
   uv pip install pytest
   ```
3. **Write tests**: Ensure your changes are covered by tests in the `tests/` directory.
4. **Run tests**:
   ```bash
   PYTHONPATH=src pytest
   ```
5. **Ensure Python 3.9 compatibility**: Avoid using Python 3.10+ specific syntax like the `|` pipe operator in type hints.
6. **Submit the PR**: Provide a descriptive title and explanation of your changes.

## Development Guidelines

- **Style**: We follow standard Python PEP 8 guidelines.
- **Type Hints**: All new code should include type hints compatible with Python 3.9 (use `typing.Optional`, `typing.Union`, etc.).
- **Security**: Be extremely careful with any changes to the `silo.security` or `silo.secrets` modules. Security is our core priority.

## Documentation

If you're contributing to documentation:
- We use [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).
- Most pages have both English (`.md`) and Russian (`.ru.md`) versions. Please try to update both if possible.

## License

By contributing to SILO, you agree that your contributions will be licensed under the project's **MIT License**.

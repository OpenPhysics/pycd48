# AGENTS.md

This file contains development information for AI assistants working on this codebase.

## Quick Commands

```bash
# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=pycd48 --cov-report=term-missing

# Linting and formatting
uv run black pycd48/ tests/          # Format code
uv run ruff check pycd48/ tests/     # Lint code
uv run ruff check --fix pycd48/      # Auto-fix lint issues
uv run mypy pycd48/ --ignore-missing-imports  # Type checking

# Check all (what CI runs)
uv run black --check pycd48/ tests/ && uv run ruff check pycd48/ tests/ && uv run mypy pycd48/ --ignore-missing-imports
```

## Project Structure

```
pycd48/
├── pycd48/              # Main package
│   ├── __init__.py      # Public API exports
│   ├── cd48.py          # Core CD48 class and serial communication
│   ├── async_cd48.py    # Async version of CD48 class
│   ├── config.py        # Device configuration from YAML/JSON files
│   ├── constants.py     # Protocol constants
│   ├── experiments.py   # YAML experiment configuration with Pydantic models
│   ├── logging.py       # DataLogger for CSV/JSON export
│   ├── plotting.py      # Real-time plotting utilities
│   ├── protocols.py     # TypedDict definitions
│   ├── utils.py         # Device discovery utilities
│   └── py.typed         # PEP 561 marker for type hints
├── tests/               # Unit tests (mocked serial)
├── examples/            # Example scripts (require hardware), YAML configs, tutorial notebook
└── .github/workflows/   # CI configuration
```

## GitHub Actions

The CI workflow (`.github/workflows/ci.yml`) runs on push to `main`, `develop`, and `claude/*`, and on pull requests to `main` and `develop`:

1. **lint**: Black formatting, Ruff linting, Mypy type checking
2. **test**: Pytest on Ubuntu (Python 3.12 and 3.13) and Windows (Python 3.13)
3. **examples**: Syntax check of example scripts

## Code Style

- **Formatter**: Black (line-length: 100)
- **Linter**: Ruff with rules: E, F, W, I (isort), UP (pyupgrade), B (bugbear), C4, SIM
- **Type checker**: Mypy (Python 3.13 target)
- **Type hints**: Modern style (`list[int]`, `X | None` instead of `List[int]`, `Optional[X]`)
- **Pydantic**: 2.x with discriminated unions, validators, and `model_validate()`

## Testing

Tests use `pytest` with `pytest-mock` for mocking serial communication. No hardware required.

```bash
# Run specific test
uv run pytest tests/test_cd48.py::TestCD48 -v

# Run with print output visible
uv run pytest -s
```

## Dependencies

Managed via `pyproject.toml` with uv. Lock file: `uv.lock`.

- **Runtime**: pyserial, numpy, matplotlib
- **Optional extras**: `async` (aioserial), `yaml` (pyyaml, pydantic), `all`, `docs` (sphinx)
- **Dev**: pytest, pytest-cov, pytest-mock, pytest-asyncio, black, ruff, mypy, pre-commit, ipython (plus the async and yaml dependencies)

## License

GPL-3.0-or-later

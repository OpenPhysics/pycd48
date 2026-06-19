# Best Practices for pycd48 Development

This document outlines the best practices and recommendations implemented in this project.

## ✅ Implemented Best Practices

### 1. Testing ✓
- **Unit Tests**: Comprehensive test suite in `tests/` directory
- **Mocking**: Hardware dependencies mocked for testing without physical device
- **Coverage**: Code coverage reporting via pytest-cov (~77%)
- **CI Integration**: Automated testing on every commit via GitHub Actions

**Run tests:**
```bash
pytest tests/ -v --cov=pycd48
```

### 2. Continuous Integration/Deployment ✓
- **GitHub Actions**: `.github/workflows/ci.yml`
  - Tests on Ubuntu and Windows
  - Tests on Python 3.12 and 3.13
  - Lint job: Black, Ruff, Mypy on `pycd48/`
  - Example syntax checks via `py_compile`
  - Coverage reporting to Codecov

### 3. Code Quality Tools ✓
- **Black**: Automatic code formatting (line length 100)
- **Ruff**: Fast linting and style checking
- **MyPy**: Static type checking on `pycd48/`
- **Pre-commit hooks**: Automatic checks before commits

**Setup pre-commit:**
```bash
uv run pre-commit install
```

**Manual code quality checks (matches CI):**
```bash
uv run black pycd48/ tests/
uv run ruff check pycd48/ tests/
uv run mypy pycd48/ --ignore-missing-imports
```

### 4. Documentation ✓
- **README.md**: Comprehensive project documentation
- **CONTRIBUTING.md**: Contribution guidelines
- **CHANGELOG.md**: Version history tracking
- **Docstrings**: Google-style docstrings for all public APIs
- **Examples**: 11 example scripts plus `pycd48_tutorial.ipynb`

### 5. Project Structure ✓
```
pycd48/
├── .github/
│   ├── workflows/        # CI/CD pipelines
│   ├── dependabot.yml    # Dependency updates
│   └── ISSUE_TEMPLATE/   # Issue templates
├── pycd48/              # Main package
│   ├── __init__.py
│   ├── cd48.py          # Core CD48 implementation
│   ├── async_cd48.py    # Async CD48 classes
│   ├── experiments.py   # YAML experiment runner (Pydantic)
│   ├── config.py        # Device configuration from files
│   ├── constants.py     # Protocol constants
│   ├── protocols.py     # TypedDict definitions
│   ├── utils.py         # Device discovery utilities
│   ├── logging.py       # DataLogger for CSV/JSON export
│   ├── plotting.py      # Visualization support
│   └── py.typed         # PEP 561 marker
├── examples/            # Example scripts and configs
├── tests/               # Unit tests
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml       # Modern Python packaging (uv/pip)
└── uv.lock              # Dependency lock file
```

### 6. Version Control ✓
- **.gitignore**: Comprehensive Python gitignore
- **Branch naming**: Feature/, bugfix/, docs/, etc.
- **Commit messages**: Clear, descriptive format
- **Pull requests**: Template-based workflow

### 7. Dependency Management ✓
- **pyproject.toml**: Modern dependency specification with optional extras
- **uv.lock**: Deterministic dependency locking
- **uv sync**: Fast, reliable dependency installation
- **Version pinning**: Minimum versions specified
- **Optional extras**: `async`, `yaml`, `all`, `dev`, `docs`

### 8. Issue and PR Templates ✓
- **Bug report template**: Structured bug reporting
- **Feature request template**: Enhancement proposals
- **Clear guidelines**: In CONTRIBUTING.md

### 9. Error Handling and Configuration ✓
- **Custom exceptions**: `CD48Error`, `CD48ConnectionError`, `CD48ResponseError`, etc.
- **Structured logging**: `logging` module used across core modules
- **YAML configuration**: Experiment and device configs via Pydantic models
- **Async support**: `AsyncCD48` with optional `aioserial` dependency
- **Reconnect support**: `CD48WithReconnect` and `AsyncCD48WithReconnect`

### 10. Security and Maintenance ✓
- **Dependabot**: Weekly updates for pip and GitHub Actions dependencies

## 📋 Future Enhancements

#### 1. **Documentation Site**
Use Sphinx to generate a documentation website (`docs` extra in `pyproject.toml`):

```bash
pip install pycd48[docs]
# docs/ directory not yet created
sphinx-quickstart docs/
```

#### 2. **Package Distribution**
Publish to PyPI for easy installation:

```bash
python -m build
twine upload dist/*
```

#### 3. **Integration Tests**
Add hardware integration tests with a pytest marker:

```python
@pytest.mark.integration
@pytest.mark.skipif(not HAS_HARDWARE, reason="Hardware not available")
def test_real_device_connection():
    """Test with real CD48 hardware."""
    cd48 = CD48()
    assert cd48.get_version() is not None
```

#### 4. **Benchmarking**
Add performance benchmarks for count acquisition loops.

#### 5. **Security Policy**
Add `SECURITY.md` for vulnerability reporting.

## 🎯 Development Workflow

### For Contributors

1. **Fork and clone** the repository
2. **Install dev dependencies**: `uv sync --extra dev` (or `pip install -e ".[dev]"`)
3. **Install pre-commit hooks**: `pre-commit install`
4. **Create feature branch**: `git checkout -b feature/new-feature`
5. **Make changes** following style guide
6. **Write tests** for new code
7. **Run tests locally**: `pytest`
8. **Format and lint**: `black pycd48/ tests/` and `ruff check pycd48/ tests/`
9. **Commit changes** with clear messages
10. **Push and create PR**

### For Maintainers

1. **Review PRs** for:
   - Code quality
   - Test coverage
   - Documentation updates
   - Breaking changes
2. **Run CI checks**
3. **Merge approved PRs**
4. **Update CHANGELOG**
5. **Create releases** with semantic versioning

## 📊 Code Quality Metrics

### Current Status
- ✅ Unit tests with mocking (92 tests)
- ✅ CI/CD pipeline
- ✅ Code formatting (Black)
- ✅ Linting (Ruff)
- ✅ Type checking (MyPy on `pycd48/`)
- ✅ Documentation
- ✅ Type hints (comprehensive)
- ⏳ Test coverage >80% (currently ~77%)
- ⏳ Integration tests with hardware

### Goals
- 🎯 >90% test coverage
- 🎯 100% type hint coverage
- 🎯 Zero ruff warnings
- 🎯 MyPy strict mode compliance
- 🎯 Published on PyPI

## 🔧 Tools Reference

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=pycd48 --cov-report=html

# Run specific test
uv run pytest tests/test_cd48.py::TestCD48::test_set_channel
```

### Code Quality
```bash
# Format code (auto-fix)
uv run black pycd48/ tests/

# Check formatting (no changes, matches CI)
uv run black --check pycd48/ tests/

# Lint code
uv run ruff check pycd48/ tests/

# Type check (matches CI)
uv run mypy pycd48/ --ignore-missing-imports

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

### Development
```bash
# Using uv (recommended)
uv sync --extra dev

# Or using pip
pip install -e ".[dev]"

# Update dependencies
uv lock --upgrade
```

## 📚 Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [Testing with pytest](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Type Hints PEP 484](https://www.python.org/dev/peps/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

## ✨ Summary

This project follows modern Python best practices:

1. ✅ **Tested**: Comprehensive unit tests
2. ✅ **Automated**: CI/CD pipeline
3. ✅ **Formatted**: Black code style
4. ✅ **Linted**: Ruff compliance
5. ✅ **Typed**: MyPy checked
6. ✅ **Documented**: README, CONTRIBUTING, examples
7. ✅ **Versioned**: CHANGELOG and semantic versioning
8. ✅ **Structured**: Clean project layout
9. ✅ **Collaborative**: Issue/PR templates

These practices ensure code quality, maintainability, and ease of contribution!

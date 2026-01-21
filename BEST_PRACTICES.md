# Best Practices for pycd48 Development

This document outlines the best practices and recommendations implemented in this project.

## ✅ Implemented Best Practices

### 1. Testing ✓
- **Unit Tests**: Comprehensive test suite in `tests/` directory
- **Mocking**: Hardware dependencies mocked for testing without physical device
- **Coverage**: Code coverage reporting via pytest-cov
- **CI Integration**: Automated testing on every commit via GitHub Actions

**Run tests:**
```bash
pytest tests/ -v --cov=pycd48
```

### 2. Continuous Integration/Deployment ✓
- **GitHub Actions**: `.github/workflows/ci.yml`
  - Tests on multiple OS (Ubuntu, Windows, macOS)
  - Tests on multiple Python versions (3.10-3.13)
  - Automated code quality checks
  - Coverage reporting to Codecov

### 3. Code Quality Tools ✓
- **Black**: Automatic code formatting
- **Ruff**: Fast linting and style checking
- **MyPy**: Static type checking
- **Pre-commit hooks**: Automatic checks before commits

**Setup pre-commit:**
```bash
pip install pre-commit
pre-commit install
```

**Manual code quality checks:**
```bash
black pycd48/ tests/
ruff check pycd48/ tests/
mypy pycd48/
```

### 4. Documentation ✓
- **README.md**: Comprehensive project documentation
- **CONTRIBUTING.md**: Contribution guidelines
- **CHANGELOG.md**: Version history tracking
- **Docstrings**: Google-style docstrings for all public APIs
- **Examples**: 10 well-documented example scripts

### 5. Project Structure ✓
```
pycd48/
├── .github/
│   ├── workflows/        # CI/CD pipelines
│   └── ISSUE_TEMPLATE/   # Issue templates
├── pycd48/              # Main package
│   ├── __init__.py
│   ├── cd48.py          # Core implementation
│   ├── logging.py       # Logging utilities
│   ├── plotting.py      # Visualization support
│   └── py.typed         # PEP 561 marker
├── examples/            # Example scripts
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

### 8. Issue and PR Templates ✓
- **Bug report template**: Structured bug reporting
- **Feature request template**: Enhancement proposals
- **Clear guidelines**: In CONTRIBUTING.md

## 📋 Additional Recommendations

### Future Enhancements

#### 1. **Improved Error Handling**
Enhance error handling with custom exceptions:

```python
class CD48Error(Exception):
    """Base exception for CD48 errors."""
    pass

class CD48ConnectionError(CD48Error):
    """Raised when device connection fails."""
    pass

class CD48CommandError(CD48Error):
    """Raised when command execution fails."""
    pass
```

#### 2. **Logging**
Add structured logging instead of print statements:

```python
import logging

logger = logging.getLogger(__name__)

def _send_command(self, command):
    logger.debug(f"Sending command: {command}")
    # ...
```

#### 3. **Configuration Files**
Support configuration files for common setups:

```python
# cd48_config.yaml
device:
  port: /dev/ttyUSB0
  baudrate: 115200

channels:
  0: {A: 1, B: 0, C: 0, D: 0}  # A singles
  4: {A: 1, B: 1, C: 0, D: 0}  # A-B coinc

trigger_level: 0.5
```

#### 4. **Performance Optimization**
- Profile code to identify bottlenecks
- Consider async I/O for multiple devices
- Optimize data collection loops

#### 5. **Documentation Site**
Use Sphinx to generate documentation website:

```bash
pip install sphinx sphinx-rtd-theme
cd docs/
sphinx-quickstart
make html
```

#### 6. **Package Distribution**
Publish to PyPI for easy installation:

```bash
python -m build
twine upload dist/*
```

Then users can install with:
```bash
pip install pycd48
```

#### 7. **Integration Tests**
Add integration tests with actual hardware:

```python
@pytest.mark.integration
@pytest.mark.skipif(not HAS_HARDWARE, reason="Hardware not available")
def test_real_device_connection():
    """Test with real CD48 hardware."""
    cd48 = CD48()
    assert cd48.get_version() is not None
```

#### 8. **Benchmarking**
Add performance benchmarks:

```python
import pytest

@pytest.mark.benchmark
def test_count_acquisition_speed(benchmark):
    result = benchmark(cd48.get_counts)
    assert result is not None
```

#### 9. **Security**
- Add security policy (SECURITY.md)
- Use Dependabot for dependency updates
- Regular security audits

## 🎯 Development Workflow

### For Contributors

1. **Fork and clone** the repository
2. **Install dev dependencies**: `uv sync --extra dev` (or `pip install -e ".[dev]"`)
3. **Install pre-commit hooks**: `pre-commit install`
5. **Create feature branch**: `git checkout -b feature/new-feature`
6. **Make changes** following style guide
7. **Write tests** for new code
8. **Run tests locally**: `pytest`
9. **Format code**: `black pycd48/`
10. **Commit changes** with clear messages
11. **Push and create PR**

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
- ✅ Unit tests with mocking
- ✅ CI/CD pipeline
- ✅ Code formatting (Black)
- ✅ Linting (Ruff)
- ✅ Type checking (MyPy)
- ✅ Documentation
- ✅ Type hints (comprehensive)
- ⏳ Test coverage >80%
- ⏳ Integration tests

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
pytest

# Run with coverage
pytest --cov=pycd48 --cov-report=html

# Run specific test
pytest tests/test_cd48.py::TestCD48::test_set_channel

# Run integration tests only
pytest -m integration
```

### Code Quality
```bash
# Format code (auto-fix)
black pycd48/ tests/ examples/

# Check formatting (no changes)
black --check pycd48/

# Lint code
ruff check pycd48/ tests/

# Type check
mypy pycd48/

# Run all pre-commit hooks
pre-commit run --all-files
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

This project now follows modern Python best practices:

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

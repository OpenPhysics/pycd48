# Contributing to pycd48

Thank you for considering contributing to pycd48! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/pycd48.git
   cd pycd48
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/OpenPhysics/pycd48.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setting Up Development Environment

**Using uv (recommended):**
```bash
# Install all dependencies including dev tools
uv sync --extra dev

# Run commands with uv
uv run pytest
uv run black pycd48/ tests/
```

**Using pip:**
```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the [code style](#code-style) guidelines

3. Add or update tests as needed

4. Update documentation if you're changing functionality

## Testing

We use pytest for testing. All new features should include tests.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pycd48 --cov-report=html

# Run specific test file
pytest tests/test_cd48.py

# Run specific test
pytest tests/test_cd48.py::TestCD48::test_set_channel
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test names that explain what is being tested
- Mock hardware dependencies (serial port) in unit tests
- Include both positive and negative test cases

Example:
```python
def test_set_trigger_level_valid_range(self):
    """Test that valid voltage range works correctly."""
    cd48.set_trigger_level(2.0)
    # Assert expected behavior

def test_set_trigger_level_out_of_range(self):
    """Test that out-of-range voltages are clamped."""
    cd48.set_trigger_level(10.0)
    # Assert voltage was clamped to maximum
```

## Code Style

### Python Code

We follow PEP 8 with some modifications:

- Maximum line length: 100 characters
- Use Black for code formatting
- Use ruff for linting
- Use type hints where possible

### Formatting

Before committing, format your code:

```bash
# Format code
black pycd48/ tests/

# Check linting
ruff check pycd48/ tests/

# Type checking
mypy pycd48/
```

### Documentation

- Use docstrings for all public functions, classes, and modules
- Follow Google-style docstrings
- Include parameter types, return types, and examples where helpful

Example:
```python
def set_trigger_level(self, voltage: float) -> str:
    """
    Set trigger level voltage.

    Parameters:
    -----------
    voltage : float
        Voltage threshold (0.0 to 4.08V)

    Returns:
    --------
    str
        Device response

    Example:
    --------
    >>> cd48.set_trigger_level(0.5)
    'OK'
    """
```

## Submitting Changes

### Commit Messages

Write clear, descriptive commit messages:

```
Short (50 chars or less) summary

More detailed explanatory text, if necessary. Wrap it to
about 72 characters. The blank line separating the summary
from the body is critical.

- Bullet points are okay
- Use imperative mood ("Add feature" not "Added feature")
- Reference issues and PRs: "Fixes #123", "See #456"
```

### Pull Request Process

1. Update your branch with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a pull request on GitHub

4. Ensure all CI checks pass

5. Wait for review and address any feedback

### Pull Request Guidelines

- Include a clear description of the changes
- Reference any related issues
- Add tests for new features
- Update documentation as needed
- Keep PRs focused - one feature/fix per PR
- Ensure CI passes before requesting review

## Reporting Bugs

### Before Submitting a Bug Report

- Check if the bug has already been reported in Issues
- Try to reproduce the bug with the latest version
- Collect information about your environment (OS, Python version, etc.)

### How to Submit a Bug Report

Create an issue with:

- **Clear title** describing the bug
- **Steps to reproduce** the problem
- **Expected behavior**
- **Actual behavior**
- **Environment details** (OS, Python version, library version)
- **Code samples** if applicable
- **Error messages** or logs

Example:
```markdown
## Bug: Device auto-detection fails on Windows

**Environment:**
- OS: Windows 11
- Python: 3.10.5
- pycd48: 0.1.0

**Steps to Reproduce:**
1. Connect CD48 to USB
2. Run `CD48()` without specifying port
3. Error occurs

**Expected:** Device should be auto-detected
**Actual:** ValueError raised

**Error message:**
```
ValueError: Could not find CD48
```

**Workaround:** Specify port manually: `CD48(port='COM3')`
```

## Suggesting Enhancements

We welcome suggestions for new features or improvements!

### Before Submitting

- Check if the enhancement has already been suggested
- Consider if it fits the project scope
- Think about how it would benefit other users

### How to Suggest an Enhancement

Create an issue with:

- **Clear title** describing the enhancement
- **Use case** - why is this needed?
- **Proposed solution** - how should it work?
- **Alternatives considered**
- **Additional context** - examples, mockups, etc.

## Development Workflow

### Typical Workflow

1. **Pick an issue** or create one for your planned work
2. **Create a branch** from `main`
3. **Make changes** following style guidelines
4. **Write tests** for new functionality
5. **Run tests** locally
6. **Update docs** if needed
7. **Commit changes** with clear messages
8. **Push to your fork**
9. **Create PR** and wait for review
10. **Address feedback** if any
11. **Merge** after approval

### Branch Naming

- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test improvements
- `refactor/` - Code refactoring

Examples:
- `feature/add-voltage-sweep`
- `bugfix/fix-overflow-detection`
- `docs/update-readme`

## Questions?

If you have questions about contributing:

- Check existing documentation
- Look at closed issues/PRs for similar questions
- Open a discussion on GitHub
- Contact maintainers

Thank you for contributing to pycd48! 🎉

# Code Linting Guide

This project uses multiple linting tools to maintain code quality and consistency.

## Tools

- **Black**: Code formatter (enforces consistent style)
- **isort**: Import statement organizer
- **Ruff**: Fast Python linter (replaces flake8, pylint, etc.)
- **MyPy**: Static type checker (optional)

## Quick Start

### Install Linting Tools

```bash
cd backend
pip install -r requirements-dev.txt
```

### Run All Linting Checks

```bash
# Check only (doesn't modify files)
./lint.sh

# Auto-fix issues
./lint.sh fix
```

## Individual Tools

### Black (Code Formatter)

```bash
# Check formatting
black --check .

# Auto-format code
black .
```

### isort (Import Sorter)

```bash
# Check import order
isort --check-only .

# Auto-sort imports
isort .
```

### Ruff (Linter)

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .
```

### MyPy (Type Checker)

```bash
# Type checking
mypy . --ignore-missing-imports
```

## Configuration

All linting tools are configured in `pyproject.toml`:
- Line length: 100 characters
- Python version: 3.12
- Excludes: migrations, venv, __pycache__

## Pre-commit Workflow

Before committing code:

```bash
# 1. Run auto-fix
./lint.sh fix

# 2. Run tests
python manage.py test

# 3. Commit
git add .
git commit -m "Your message"
```

## CI/CD

Linting is automatically run in GitHub Actions on every push/PR. The build will fail if linting issues are found.

## Tips

- Run `./lint.sh fix` before committing to auto-fix most issues
- Black and isort are opinionated - they will reformat your code
- Ruff catches common bugs and style issues
- MyPy is optional but helps catch type-related bugs


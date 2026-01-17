# Pivot Agent Guidelines

This document provides instructions and guidelines for AI agents and developers working on the Pivot codebase.

## 1. Project Overview

Pivot is a Windows desktop application built with [Flet](https://flet.dev) for directory and version management (similar to Scoop/Homebrew).
It relies on separating physical file storage (`Versions/`) from access points (`Persists/`) using symbolic links (Symlinks/Junctions).

### Key Technologies
- **Language**: Python >= 3.10
- **Framework**: Flet (Flutter based UI for Python)
- **Package Manager**: `uv`

## 2. Environment & Commands

### Setup & Run
Always use `uv` for dependency management and execution.

- **Install Dependencies**:
  ```bash
  uv sync
  ```

- **Run Application (Desktop)**:
  ```bash
  uv run flet run
  ```

- **Run Application (Web/Debug)**:
  ```bash
  uv run flet run --web
  ```

### Build (Windows)
```bash
flet build windows
```

### Linting & Formatting
We use `ruff` for both linting and formatting.

- **Check Code**:
  ```bash
  uv run ruff check .
  ```
- **Format Code**:
  ```bash
  uv run ruff format .
  ```

### Testing
We use `pytest` for unit testing, especially for file system logic.

- **Run All Tests**:
  ```bash
  uv run pytest
  ```
- **Run Single Test File**:
  ```bash
  uv run pytest tests/test_linking.py
  ```
- **Run Specific Test Case**:
  ```bash
  uv run pytest tests/test_linking.py::test_create_link_success -v
  ```

*Note: If `pytest` or `ruff` are missing, add them via `uv add --dev pytest ruff`.*

## 3. Code Style Guidelines

### General Python
- **Formatting**: Follow the "Black" style (enforced by `ruff format`).
  - Max line length: 88 characters.
  - Double quotes `"` for strings.
- **Imports**:
  - Sort imports using `ruff check --select I --fix`.
  - Order: Standard Lib > Third Party > Local Application.
- **Type Hinting**:
  - **Mandatory** for function signatures.
  - Use modern Union syntax `str | int` (Python 3.10+).
  - Use `pathlib.Path` for all file paths, never string manipulation.

### Naming Conventions
- **Variables/Functions**: `snake_case` (e.g., `create_symlink`)
- **Classes**: `PascalCase` (e.g., `VersionManager`)
- **Constants**: `UPPER_CASE` (e.g., `DEFAULT_VERSION_DIR`)
- **Private Members**: `_snake_case` (prefix with underscore)

### Flet Specifics
- **Import Style**: Always use `import flet as ft`.
- **Component Structure**:
  - Break complex UI into separate classes inheriting from `ft.Container`, `ft.Column`, or `ft.Row`.
  - Avoid massive `main` functions; keep `main.py` clean.
- **Event Handlers**:
  - Name handlers as `on_<event>_<element>` or `<action>_click`.
  - Example: `on_submit_click(e: ft.ControlEvent)` or `on_link_version(app_name: str)`.

### Error Handling
- Use `try/except` blocks specifically for file system operations (Symlink creation can fail due to permissions).
- Log errors clearly before showing UI alerts.
- **Windows Permissions**: Be aware that creating symlinks on Windows might require Developer Mode or Admin privileges. Code should check/handle this gracefully.

## 4. Architectural Guidelines

### Directory Management
- **Path Handling**: ALWAYS use absolute paths internally.
- **Symlinks**:
  - Use `os.symlink()` or `Path.symlink_to()`.
  - For directories on Windows, ensure `target_is_directory=True` is considered if using low-level calls, though `Path` handles much of this.
  - Distinguish between **Junctions** (mklink /J) and **Symlinks** (mklink /D). Pivot prefers Symlinks but may fallback to Junctions if configured.

### Environment Abstraction
- **Dev vs Prod**:
  - The app detects if it is frozen (packaged via PyInstaller) via `sys.frozen`.
  - In **Dev** (local run): Root is `parent/dummy` relative to source. Use `dummy/Versions` and `dummy/Persists` to avoid messing with real system files.
  - In **Prod** (exe): Root is the executable's directory.
- **Config**: Always import paths from `src/config.py` rather than hardcoding them.

### State Management
- For simple state, use `page.client_storage` or variable passing.
- For complex app state (like selection tracking), implement a dedicated State class (e.g., `AppState` in `src/state.py`) that uses the Observer pattern.

## 5. Git & Workflow Guidelines

### Commit Messages
Use semantic commit messages to keep history clean:
- `feat:` New features (e.g., "feat: add folder open button")
- `fix:` Bug fixes (e.g., "fix: resolve path issue on windows")
- `docs:` Documentation changes
- `style:` Formatting, missing semi-colons, etc; no production code change
- `refactor:` Refactoring production code, eg. renaming a variable
- `test:` Adding missing tests, refactoring tests; no production code change

### Pull Requests
- Keep PRs small and focused on a single task.
- Ensure `ruff check .` and `pytest` pass before requesting review.

## 6. Documentation
- Update `README.md` if architectural changes occur.
- Docstrings: Use Google-style docstrings for complex logic (especially the Symlink manager).

```python
def create_version_link(version_path: Path, link_name: str) -> None:
    """Creates a symbolic link in the Persists directory.

    Args:
        version_path: Absolute path to the source version directory.
        link_name: Name of the link to create in Persists.

    Raises:
        PermissionError: If the user lacks symlink privileges.
    """
    ...
```

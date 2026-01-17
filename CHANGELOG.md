# Changelog

All notable changes to this project will be documented in this file.

## [v0.1.0] - 2026-01-17

### Added
- **Batch Linking**: Select multiple application versions and link them in bulk.
- **Portable Mode**: Support for running as a standalone executable (frozen mode) with correct path resolution.
- **UI Enhancements**:
    - Open folder button for linked app groups.
    - Improved grid layout for version management.
    - Status indicators for linked vs unlinked versions.
- **Type Safety**: Comprehensive static typing across the codebase using Python 3.10+ syntax.

### Changed
- **Architecture**: Refactored `main.py` and split UI components into dedicated modules (`ui/`).
- **Performance**: Optimized batch selection state management.
- **Documentation**: Updated guidelines for developers and agents (`AGENTS.md`).

### Fixed
- Fixed path resolution issues on Windows when running as a frozen executable.

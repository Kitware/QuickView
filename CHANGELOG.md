# Changelog

All notable changes to QuickView will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Pre-commit hooks for code quality (ruff, prettier, codespell)
- CI/CD pipeline with GitHub Actions
- Visual indicators for manual color range override mode
- Override range persistence in saved states
- Pull request templates for different types of changes

### Changed

- Improved color range override logic to properly persist through state changes
- ViewManager methods renamed for clarity (e.g., `reset_views()` →
  `render_all_views()`)
- Toolbar UI improvements with visual grouping and pipeline status indicators

### Fixed

- Menu expansion conflict with tooltips in toolbar
- Context manager error in ViewManager
- Color range override flag lost during view rebuilding
- Module-level import issues in ParaView plugins

### Security

- Added defensive security measures to prevent malicious code execution

## [0.1.0] - 2024-01-01

### Added

- Initial release of QuickView
- Support for E3SM atmospheric data visualization
- Multiple projection support (Cylindrical Equidistant, etc.)
- Variable selection for 2D and 3D data
- Time step navigation
- State save/load functionality
- Cross-platform desktop application using Tauri
- ParaView-based rendering pipeline

### Known Issues

- Performance optimization needed for large datasets
- Limited to specific E3SM data formats

[Unreleased]: https://github.com/E3SM-Project/QuickView/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/E3SM-Project/QuickView/releases/tag/v0.1.0

# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- refactor: Improve code quality and linting configuration
- refactor: Fix import order in test files
- refactor: Remove unused imports and arguments
- refactor: Clean up type hints
- chore: Add TODO.md for tracking future improvements

## [0.2.0] - 2024-02-10

### Added

- feat: Add battery information gathering
- feat: Add multiple output formats (text, JSON, YAML, markdown, simple, public)
- feat: Add comprehensive test suite
- feat: Add GitHub Actions CI workflow for macOS
- feat: Add proper Python package structure

### Changed

- refactor: Split functionality into modules (hardware, battery, utils)
- refactor: Improve error handling and logging
- refactor: Add type hints throughout the codebase
- refactor: Use dataclasses for structured data

### Fixed

- fix: Handle missing battery gracefully
- fix: Handle permission issues gracefully
- fix: Add proper type annotations
- fix: Use safe test data in test suite

## [0.1.1] - 2024-02-10

### Added

- feat: Graceful permission handling with sudo and non-sudo modes
- feat: Fallback mechanisms for non-privileged access
- feat: Basic information gathering without sudo
- docs: Detailed permission level documentation
- docs: Improved installation and usage instructions

### Changed

- refactor: Improved error handling for system commands
- refactor: Better logging messages for permission issues
- docs: Updated README with permission levels and usage modes

## [0.1.0] - 2024-02-10

### Added

- feat: Initial release of about-this-mac
- feat: Basic hardware information gathering
- feat: Battery information gathering
- feat: Multiple output formats (text, JSON, YAML)
- feat: Command-line interface with various options
- feat: Logging and error handling
- docs: Initial README with features and usage
- docs: MIT License
- build: Basic Python package structure
- build: Dependencies in requirements.txt

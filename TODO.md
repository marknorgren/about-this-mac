# TODO

## Code Quality Improvements

### Pylint Warnings to Address

- [ ] C0111: Add missing docstrings where appropriate (currently handled by black)
- [ ] C0103: Review and fix variable naming conventions
- [ ] C0301: Review long lines and consider refactoring (currently handled by black)
- [ ] R0902: Reduce number of instance attributes in classes
  - BatteryInfo
  - HardwareInfo
  - StorageInfo
- [ ] R0903: Add more public methods where appropriate
- [ ] R0912: Reduce number of branches in complex functions
  - MacInfoGatherer.\_parse_apple_silicon_info
  - MacInfoGatherer.get_hardware_info
- [ ] R0913: Reduce number of arguments in functions
- [ ] R0914: Reduce number of local variables
  - MacInfoGatherer.get_hardware_info
  - BatteryInfoGatherer.get_battery_info
- [x] R0915: Reduce number of statements in functions
  - cli.format_output - moved to commands/report.py
  - cli.main - split into commands/raw.py and commands/report.py
- [ ] W0212: Review protected member access
  - Consider making some methods public or restructuring
- [ ] W0702: Add specific exception types
  - BatteryInfoGatherer.get_battery_info
  - MacInfoGatherer.\_get_uptime
- [ ] W0718: Replace broad exception catches with specific ones
- [ ] W1203: Update logging to use % formatting
- [x] R0801: Address code duplication
  - Formatting functions consolidated in commands/report.py and utils/formatting.py
- [ ] R1705: Remove unnecessary "elif" after "return"

### Test Coverage Improvements

- [ ] Increase overall test coverage (currently 45%)
- [x] Add tests for cli.py (now 80% coverage)
- [ ] Improve coverage of hardware_info.py (currently 16%)
- [ ] Add integration tests for system commands
- [ ] Add more edge case tests for battery_info.py

### General Improvements

- [ ] Add more type hints and improve type safety
- [x] Consider breaking down large modules into smaller ones (cli.py split into commands/)
- [x] Add more error handling and recovery mechanisms (CliError with hints)
- [ ] Improve logging and debugging capabilities
- [ ] Add performance benchmarks
- [ ] Consider adding async support for long-running operations

## Documentation

- [ ] Add more detailed API documentation
- [x] Add architecture documentation (project structure in README)
- [ ] Add contribution guidelines
- [ ] Add troubleshooting guide
- [ ] Improve inline code comments

## Build and CI

- [ ] Add more Python versions to test matrix
- [ ] Add code coverage requirements
- [ ] Add performance regression tests
- [ ] Add security scanning
- [ ] Add dependency vulnerability checking

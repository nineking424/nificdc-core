# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial implementation of NiFi CDC Core
- NiFi API Client for programmatic flow creation
- Config Parser for properties file handling
- CDC Flow Builder for orchestrating CDC pipelines
- Support for Oracle to Oracle CDC
- Comprehensive test suite with 100% coverage
- Documentation for setup and usage
- Environment configuration via .env file
- Flexible mapping configuration system

### Technical Details
- Python-based implementation using NiFi REST API
- Test-Driven Development (TDD) approach
- Properties file format for configurations
- Support for incremental CDC based on timestamp columns

## [0.1.0] - 2025-07-27

### Initial Release
- Core modules implementation
- Basic Oracle CDC support
- Test infrastructure setup
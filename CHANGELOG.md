# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [4.0.0] - 2022-09-19
### Added

 - Install `tahoe-sites` and `site-configuration-client` to simulate Tahoe environment.
 - Add support for Tahoe 2.0 site by reading `LAUNCHCONTAINER_WHARF_URL` from Site Config Service `secret`s. Tahoe 1.0 sites will still use `site_values` as usual
- Breaking change: Drop support for pre-Juniper Tahoe installations. The last version to support Hawthorn is `3.0.0`
need to complicate the XBlock with caching calls.

### Fixed
 - Simplify reading the Wharf URL
   * Read from `ENV_TOKENS` for regular Open edX installation (non-Tahoe)
   * Read from [Site Configuration Client](https://github.com/appsembler/site-configuration-client/) for Juniper+ installations

### Changed
 - Refactored unit tests
 - Refactor testing environments in `tox.ini` to test for `tahoe` and non `tahoe` environments removing `tox-gh-actions`.
 - Remove complex and low-value caching for `wharf_url`

## [3.0.0] - 2021-09-03

### Added
- Get support_url and timeout_seconds from XBlock settings or revert to platform-wide defaults
- Styling improvements on error message links

### Fixed
- Fixed a Python 3 incompatibility in tests
- Fixed test requirements
- Refactored JS variables for better readability and DRY

### Changed
- Dropped Python 2 support

## [2.3.2] - 2021-07-30
### Added
- Update support message with `help` page when support email is not set

## [2.3.1] - 2021-04-29
### Fixed
- Fixed static files resource decoding as part of Python3 support

## [2.3.0] - 2020-11-17
### Added
- python3 and Django 2.x support

## [2.2.2] - 2019-05-14
### Fixed
- Fixed the mailto: link

## [2.2.1] - 2019-05-02
### Fixed
- Fixed the support email default value

## [2.2.0] - 2019-04-16
### Added
- Helpful message with support email (editable in XBlock) is shown for users when deploy is taking a long time

### Fixed
- Improved error handling for responses from AVL

## 2.1.12 - 2019-04-09
### Added
- Added a changelog
### Changed
- fixed import bug on Hawthorn

(sorry, we didn't keep a proper changelog previous to this release)

[Unreleased]: https://github.com/appsembler/xblock-launchcontainer/compare/v2.3.2...HEAD
[2.3.2]: https://github.com/appsembler/xblock-launchcontainer/compare/v2.3.1...v2.3.2
[2.3.1]: https://github.com/appsembler/xblock-launchcontainer/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/appsembler/xblock-launchcontainer/compare/v2.2.2...v2.3.0
[2.2.2]: https://github.com/appsembler/xblock-launchcontainer/compare/v2.2.1...v2.2.2
[2.2.1]: https://github.com/appsembler/xblock-launchcontainer/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/appsembler/xblock-launchcontainer/compare/v2.1.12...v2.2.0

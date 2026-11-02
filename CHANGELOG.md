# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versions use `<benchmark>_<major>.<minor>.<iterative>`: the CIS benchmark version the role
implements, then the role's own version.

## [Unreleased]

## [3.0.0_0.0.3]

### Changed

- Versions now start with the CIS benchmark version the role implements, for example
  `3.0.0_0.0.3` for role version 0.0.3 on benchmark v3.0.0. Earlier entries are renamed
  to match (#15).
- The role's own version keeps counting when the benchmark version changes, and older
  benchmarks are maintained on `support/<benchmark>` branches (#15).

## [3.0.0_0.0.2]

### Added

- Role skeleton (#2): `defaults/`, `vars/`, `tasks/`, `handlers/` and `meta/` at the repo
  root, with empty placeholder task files for each section (1 to 7) and level.
- Preflight check: the role stops with a clear message unless the host is RHEL 9, and
  records the minor release in `cis_rhel_minor_release` (a string such as `"4"`; compare
  with `| int`).
- Handlers for sshd, rsyslog, chronyd, auditd (reload and rule load) and sysctl reload.
- Role metadata: MIT license, Ansible 2.15 minimum, EL 9 platform, and the
  `ansible.posix` and `community.general` collections.

## [3.0.0_0.0.1]

### Added

- Project setup: README, license, contributor notes and release placeholder.
- Control inventory (`docs/controls.md`) listing every CIS RHEL 9 Benchmark v3.0.0
  recommendation with its profile and planned disposition.
- Stated requirements: Ansible 8.7 (ansible-core 2.15) or later on the control node, with
  the bundled `ansible.posix` and `community.general` collections.

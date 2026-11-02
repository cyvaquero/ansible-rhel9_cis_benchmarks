# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versions use `major.minor.iterative`.

## [Unreleased]

## [0.0.2]

### Added

- Role skeleton (#2): `defaults/`, `vars/`, `tasks/`, `handlers/` and `meta/` at the repo
  root, with empty placeholder task files for each section (1 to 7) and level.
- Preflight check: the role stops with a clear message unless the host is RHEL 9, and
  records the minor release in `cis_rhel_minor_release` (an integer such as `4`).
- Handlers for sshd, rsyslog, chronyd, auditd (reload and rule load) and sysctl reload.
- Role metadata: MIT license, Ansible 2.15 minimum, EL 9 platform, and the
  `ansible.posix` and `community.general` collections.

## [0.0.1]

### Added

- Project setup: README, license, contributor notes and release placeholder.
- Control inventory (`docs/controls.md`) listing every CIS RHEL 9 Benchmark v3.0.0
  recommendation with its profile and planned disposition.
- Stated requirements: Ansible 8.7 (ansible-core 2.15) or later on the control node, with
  the bundled `ansible.posix` and `community.general` collections.

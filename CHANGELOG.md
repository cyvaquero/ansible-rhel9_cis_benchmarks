# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versions use `<benchmark>_<major>.<minor>.<iterative>`: the CIS benchmark version the role
implements, then the role's own version.

## [Unreleased]

## [3.0.0_0.0.5]

### Added

- Audit mode (#4): `cis_audit_only` (default `false`) checks and reports without
  changing the host, and `cis_fail_on_findings` (default `false`) fails each host that
  ends the run with findings. Preflight rejects values that are not true or false.
- A shared control pattern: a read-only check, remediation only when not in audit mode,
  and `tasks/finding.yml` to record a finding. It is documented in `CLAUDE.md` and in the
  header of `tasks/finding.yml` (#23).
- An end-of-run summary per host listing the failing CIS IDs. Selected audit-only and
  manual controls always count as findings; their IDs come from the new
  `cis_control_dispositions` map in `vars/controls.yml`, which mirrors `docs/controls.md`.
- `tests/check_controls.py` fails when `vars/controls.yml` and `docs/controls.md`
  disagree on IDs, levels, dispositions or totals, and `tests/audit-summary.yml`
  exercises the summary and failure behavior without a RHEL 9 host.

## [3.0.0_0.0.4]

### Added

- Level and profile selection (#3): `cis_apply_level_2` (Level 1 by default, Level 2
  includes Level 1), `cis_profile` (`server` or `workstation`) and `cis_exclusions`.
- `cis_default_exclusions` skips 2.1.20, 2.1.21, 2.1.22 and 5.2.6 by default because
  they can lock out or disrupt a host; override it to run them.
- `vars/controls.yml` records the level of each of the 352 controls per profile, and
  preflight computes `cis_selected_controls`, the list every control task tests.
- Preflight fails with a clear message on an invalid `cis_profile`, a
  `cis_apply_level_2` that is not true or false, a non-list exclusion variable, or an
  unknown CIS ID in the exclusions.

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

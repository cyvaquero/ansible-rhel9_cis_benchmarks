# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versions use `<benchmark>_<major>.<minor>.<iterative>`: the CIS benchmark version the role
implements, then the role's own version.

## [Unreleased]

## [3.0.0_0.0.17]

### Fixed

- The README status now lists the implemented control ranges as bullets instead of one
  run-on sentence with missing commas. Fixes #35.

## [3.0.0_0.0.16]

### Added

- Controls 2.1.1 to 2.1.18, the services that should not be in use: autofs, avahi, cockpit,
  dhcp server, dns server, dnsmasq, samba, ftp server, message access servers (dovecot,
  cyrus-imapd), nfs server, print server (cups), rpcbind, rsync daemon, snmp, telnet
  server, tftp server, web proxy (squid) and web servers (httpd, nginx). On each host the
  role removes an installed service package with dnf when no other installed package needs
  it. When another package needs it, the package stays and the service's units (services,
  sockets, paths) are stopped and masked; the same applies to a unit that exists with none
  of its packages installed. Dependent packages are never removed. A masked, inactive unit
  is compliant. Audit mode only reports. New variable `cis_services_keep` (default `[]`)
  lists the CIS IDs of services the site needs; those controls are skipped with no finding.
  Shared logic is in `tasks/lib/service_not_in_use.yml`. Part of #6.

### Changed

- `docs/controls.md` marks the 18 controls implemented. Part of #6.

## [3.0.0_0.0.15]

### Added

- Controls 1.7.1 to 1.7.6 (command-line warning banners) and 1.8.1 to 1.8.7 (GNOME Display
  Manager), 13 controls. 1.7.1 to 1.7.3 write `cis_banner_text` to `/etc/motd`, `/etc/issue`
  and `/etc/issue.net` when the file holds a login escape or the OS name (an empty
  `/etc/motd` is compliant); a compliant file is left alone. 1.7.4 to 1.7.6 set root:root
  and 0644 or stricter; a symlink is a finding. The 1.8 controls run only when GDM is
  installed: 1.8.1 to 1.8.5 write system-wide dconf keys with locks (login banner, user
  list, idle and lock delay, automount, autorun) and run `dconf update`, checking the
  compiled value; 1.8.6 disables XDMCP and 1.8.7 removes `WaylandEnable=false` in
  `/etc/gdm/custom.conf`, flagging `cis_reboot_required` while GDM has not restarted since
  the file changed. New variables `cis_banner_text`, `cis_gdm_idle_delay` (900) and
  `cis_gdm_lock_delay` (5). Shared logic is in `tasks/lib/banner.yml`,
  `banner_access.yml`, `dconf.yml` and `gdm_custom.yml` (#5).

### Changed

- `docs/controls.md` marks the 13 controls implemented (#5).

## [3.0.0_0.0.14]

### Added

- Controls 1.6.1 to 1.6.7 (system-wide crypto policy), 7 controls. The checks read the
  effective policy and, for the MAC and SSH controls, the generated OpenSSH back-ends.
  Fixes change the policy string with `update-crypto-policies --set`, keeping the base
  policy and every module in it: 1.6.1 replaces a LEGACY base with DEFAULT, 1.6.2 appends
  `NO-SHA1`, 1.6.3 and 1.6.4 write and append the role's own `CIS-NO-WEAKMAC` and
  `CIS-NO-SSHCBC` modules only on a host that needs them, and 1.6.7 (Level 2) appends `PQ`
  when the release ships it, otherwise it is a finding. 1.6.5 and 1.6.6 only report.
  The role restarts no service: `cis_reboot_required` is set, in both modes, while the
  policy state is newer than the boot. Shared logic is `tasks/lib/crypto_policy.yml` (#5).

### Changed

- `docs/controls.md` marks the 7 controls implemented (#5).

## [3.0.0_0.0.13]

### Added

- Controls 1.4.1 to 1.4.5 (boot loader) and 1.5.1 to 1.5.10 (kernel and process
  hardening), 15 controls. 1.4.1 writes the boot loader password hash from the new
  `cis_grub_password_hash` variable (default empty) to `/boot/grub2/user.cfg`; with the
  variable empty it only reports. 1.4.2 sets 0600 root:root on the grub2 files and
  `uid=0,gid=0,umask=0077` on the `/boot/efi` fstab entry. 1.4.3 and 1.4.4 (Level 2) keep
  the root password prompt in rescue and emergency mode. 1.4.5 removes
  `systemd.confirm_spawn` from the boot entries and `ConfirmSpawn=yes` from the systemd
  configuration. 1.5.1 to 1.5.7 (1.5.2 is Level 2) set the sysctl values in a role-owned
  file that overrides vendor files, and set the running value. 1.5.8 sets a hard core
  limit of 0, and 1.5.9 and 1.5.10 set `ProcessSizeMax=0` and `Storage=none` for
  systemd-coredump. A setting that another file overrides is a finding. 1.4.2 and 1.4.5
  set `cis_reboot_required` when the live state still differs. Shared logic is
  `tasks/lib/sysctl.yml`, `sulogin_unit.yml` and `coredump.yml` (#5).

### Changed

- `docs/controls.md` marks the 15 controls implemented (#5).

## [3.0.0_0.0.12]

### Added

- Controls 1.2.1.1 to 1.2.2.1 (package manager) and 1.3.1.1 to 1.3.1.8 (SELinux), 14
  controls. 1.2.1.2 sets `gpgcheck=1` in `/etc/dnf/dnf.conf` and in every repository file
  section that turns it off, except `redhat.repo`, which subscription-manager owns: a
  repository there with `gpgcheck=0` is a finding and is never edited. 1.2.1.5 (Level 2)
  sets `install_weak_deps=False`. 1.2.1.3 (repo_gpgcheck, Level 2), 1.2.1.1, 1.2.1.4,
  1.2.2.1 (pending updates; an unreadable `dnf check-update` reports unknown and never
  fails the run) and 1.3.1.6 (processes in `unconfined_service_t`) only report. 1.3.1.1,
  1.3.1.7 and 1.3.1.8 install `libselinux` and remove `mcstrans` and `setroubleshoot`
  (1.3.1.8 is Server only). 1.3.1.2 removes `selinux=0` and `enforcing=0` from every boot
  entry with `grubby`. 1.3.1.3 sets `SELINUXTYPE=targeted`. 1.3.1.4 moves a disabled
  configuration to the mode SELinux is running in (permissive when it is not running), so
  it never lowers an enforcing host. 1.3.1.5 (Level 2) sets enforcing in the configuration
  and at runtime. The SELinux controls read the state once and share it, so the Level 1
  and Level 2 controls do not undo each other (#5).
- Leaving the disabled SELinux state creates `/.autorelabel` and sets
  `cis_reboot_required`, as do a boot entry fix while the running kernel still has
  `selinux=0` or `enforcing=0`, and a policy type change while another policy is loaded.
  A host that is not running SELinux is switched to enforcing by 1.3.1.5 only on a run
  after that reboot (#5).
- Package facts are gathered once in preflight for the controls that read installed
  packages (#5).

## [3.0.0_0.0.11]

### Added

- Controls 1.1.2.1.1 to 1.1.2.7.4 (26 mount controls). 1.1.2.1.1 enables systemd's
  `tmp.mount` when `/tmp` is not already a mount, without starting it, because mounting
  tmpfs over a live `/tmp` would hide files running services hold there; the mount
  appears at the next boot, and until then the control reports that a reboot is pending.
  The `nodev`, `nosuid` and `noexec` controls for `/tmp`, `/dev/shm`, `/home`, `/var`,
  `/var/tmp`, `/var/log` and `/var/log/audit` act only when the mount exists (for `/tmp`,
  when `tmp.mount` is enabled): they add the option to the `/etc/fstab` entry (a new entry
  for `/dev/shm`) or to a `tmp.mount` drop-in, and remount the live mount. A control that
  cannot be fixed is recorded as a finding and does not fail the run. The audit compares
  the live options. The separate-partition controls (1.1.2.2.1 and 1.1.2.x.1) only report.
  Shared logic is `tasks/lib/mount_option.yml` and `tasks/lib/mount_separate.yml` (#5).
- `cis_reboot_required` (default `false`), set by any control whose fix only takes effect
  after a reboot, and printed in the end-of-run summary. The role never reboots (#5).

### Changed

- `docs/controls.md` marks the 26 mount controls implemented (#5).

## [3.0.0_0.0.10]

### Fixed

- The titles of controls 7.1.2, 7.1.4, 7.1.6 and 7.1.8 in `docs/controls.md` had lost the
  space after the backup file name (`/etc/passwd- is configured`) (#25).

## [3.0.0_0.0.9]

### Fixed

- The placeholder task files for sections 2 to 7 no longer warn that a noop task does
  not support a `when` conditional. They now use a `debug` task that prints only at
  `-v` and above (#22).

## [3.0.0_0.0.8]

### Added

- Controls 1.1.1.1 to 1.1.1.10 (cramfs, freevxfs, hfs, hfsplus, jffs2, overlay,
  squashfs, udf, firewire-core and usb-storage kernel modules). A module that
  is not shipped for the running kernel passes; otherwise it must be blocked from loading
  (`install ... /bin/false`), blacklisted and not loaded. Remediate mode writes
  `/etc/modprobe.d/<module>.conf` (root:root, 0644) and unloads the module, then checks
  again; a control that still fails (a module in use, or a conflicting `install` line
  elsewhere) is recorded as a finding and does not fail the run. Audit mode only reports.
  The shared logic is `tasks/lib/kernel_module.yml` (#5).
- Control 1.1.1.11 (manual) lists the loaded filesystem kernel modules for review (#5).
- A Status column (`planned` or `implemented`) in every control table of
  `docs/controls.md`. `tests/check_controls.py` accepts only those values and fails when
  an implemented control has no task file, a planned control has one, or a control task
  file is not at the path the inventory implies (#5).

### Changed

- `tasks/section-1/level-1.yml` and `level-2.yml` import the section 1.1.1 control
  files instead of the placeholder task (#5). This also removes the noop `when` warning
  for section 1 (#22).

## [3.0.0_0.0.7]

### Added

- `cis_benchmark` in `vars/main.yml` records the benchmark document the role implements:
  title, version (3.0.0) and date (2026-08-28). `docs/controls.md` states the same in its
  header (#17).
- Preflight prints the benchmark title and version, and the end-of-run summary includes
  them (#17).
- `tests/check_benchmark_version.py`, run by CI, fails unless `cis_benchmark`, the
  `docs/controls.md` header and the version prefix of the newest CHANGELOG entry agree.
  CI now also runs `tests/check_controls.py` (#17).

## [3.0.0_0.0.6]

### Added

- ansible-lint configuration (`.ansible-lint`, `production` profile) and a GitHub
  Actions workflow that runs it, plus `ansible-playbook --syntax-check` of
  `tests/syntax.yml`, on pushes and pull requests to `develop`, `main`, `release/**`,
  `feature/**`, `bugfix/**` and `hotfix/**` (#13). The toolchain is pinned in
  `tests/requirements.txt`: Ansible 8.7.0 and ansible-lint 6.22.2, on Python 3.9.
- The README and `CLAUDE.md` describe running the lint locally.

### Changed

- `meta/main.yml` sets `role_name` and `namespace`, so the role name is valid whatever
  the checkout folder is called (#13).
- The auditd reload handler waives ansible-lint's `command-instead-of-module` rule,
  because auditd refuses the service module (#13).

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

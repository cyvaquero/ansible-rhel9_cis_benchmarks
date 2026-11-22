# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
versions use `<benchmark>_<major>.<minor>.<iterative>`: the CIS benchmark version the role
implements, then the role's own version.

## [Unreleased]

## [3.0.0_0.0.32]

### Changed

- Section 1: every value a control writes or expects now comes from an overridable role variable
  whose default is the benchmark value (`defaults/main.yml`, grouped by control ID). New variables
  cover the kernel modules (`cis_module_<name>_blocked`), `/tmp` mounting and the mount options of
  each mount point, `gpgcheck` and weak dependencies, whether `libselinux`, `mcstrans` and
  `setroubleshoot` are installed, the SELinux policy, mode and boot arguments, the boot loader file
  owner, group and mode and the `/boot/efi` options, the rescue and emergency commands,
  `ConfirmSpawn`, the sysctl values of 1.5.1 to 1.5.7, the core file limit, the coredump settings,
  the crypto policy base, modules and removed algorithms, the banner paths, owner, group and mode,
  and the GDM values. Overriding a value changes what the role writes; the checks still judge the
  benchmark value, now kept as `cis_expect_*` constants in `vars/main.yml`, so a weaker value is
  written and reported as a finding. With default values nothing changes. Preflight validates only
  the type and format of the new variables. The README has an "Overriding values" section and a
  table per group of controls. The shared `tasks/lib/` helpers take the new inputs as optional
  parameters, so sections 2 to 5 behave as before. Part of #58 (sections 2 to 5 follow).

## [3.0.0_0.0.31]

### Added

- Section 5.4, user accounts and environment, 5.4.1.1 to 5.4.3.4; this completes section 5.
  Password aging (5.4.1.1, 5.4.1.3, 5.4.1.5) sets the maximum age (365 days), the warning
  (7 days) and the inactive period (45 days) in `login.defs` and `useradd -D -f`, and with
  `chage` on every existing account that has a password hash; accounts without a hash are left
  alone. An account whose password would be expired or inactive with the new value (a last change
  date of 0 or none, or a password older than the maximum) is skipped, named in a message and
  recorded as a finding, never changed; a stricter value is never loosened. 5.4.1.4 sets
  `ENCRYPT_METHOD` in `login.defs` (SHA512, or YESCRYPT when PAM already uses it). 5.4.2.6 sets
  root's umask in `/root/.bash_profile` and `/root/.bashrc`. 5.4.2.7 gives system accounts a
  nologin shell and 5.4.2.8 locks them, behind a lockout guard: never root, the benchmark's
  exceptions, the account the role is connected as or becomes, an account with a running process
  or one in `cis_account_exceptions`; skipped accounts are reported and are findings. 5.4.3.2
  (`TMOUT`, readonly, exported, interactive shells only) and 5.4.3.4 (`umask 027`) go in one
  role-owned file, `/etc/profile.d/zz-cis-rhel9.sh`, judging every file the shells read; a weaker
  setting in a file the role does not own is a finding with its file and line. 5.4.3.3 sets
  `UMASK` in `login.defs`. 5.4.3.1 (Level 2) removes `nologin` lines from `/etc/shells`. 5.4.1.2
  (manual, Level 2), 5.4.1.6 and 5.4.2.1 to 5.4.2.5 (audit-only) report what they found and
  change nothing; they are listed in `docs/review-controls.md`. New variables `cis_pass_max_days`
  (365), `cis_pass_warn_age` (7), `cis_inactive_days` (45), `cis_umask` (`"027"`), `cis_tmout`
  (900) and `cis_account_exceptions` (`[]`), validated at preflight. New
  `tests/check_accounts_scan.py`, run in CI. Part of #9.

## [3.0.0_0.0.30]

### Added

- Section 5.3, PAM and authselect, 5.3.1.1 to 5.3.3.4.4. The role changes PAM only through
  authselect, never by editing `/etc/pam.d`. 5.3.1.1 to 5.3.1.3 check `pam`, `authselect` and
  `libpwquality` against the minimum version the benchmark names (1.5.1-14, 1.2.6-1, 1.4.4-8)
  and upgrade a package only when it is missing or below that. 5.3.2.1 moves a host authselect
  does not manage to a custom profile of its own, `cis-rhel9` (variable `cis_authselect_profile`,
  a copy of `sssd`), selected with `--force` and a backup (`authselect backup-restore` undoes it),
  with `with-faillock`, `with-pwhistory` and `without-nullok` enabled for the selected controls;
  a host already on an authselect profile keeps it and only gets the features enabled.
  A lockout guard renders what authselect would write before anything is selected and refuses,
  with a finding, when it names a PAM module or name service library that is not installed,
  would drop a module or name service the host uses now, or cannot be rendered; after a change
  the role checks `authselect check`, opens a new connection and runs a become task. 5.3.2.2 to
  5.3.2.5 check the modules in `system-auth` and `password-auth` (5.3.2.2 and 5.3.2.4 enable the
  feature). 5.3.3.x write the settings to the module configuration files: `deny` and
  `unlock_time` (and for Level 2 5.3.3.1.3 `even_deny_root`) to `/etc/security/faillock.conf`;
  `difok`, `minlen`, `maxrepeat`, `maxsequence`, `dictcheck` and `enforce_for_root` to the role's
  own `/etc/security/pwquality.conf.d/zz-cis-rhel9.conf`; `remember` and `enforce_for_root` to
  `/etc/security/pwhistory.conf`. Compliance is judged on the value in effect (libpwquality's
  last-file-wins order), a stricter value is never loosened, and a value in a file the role does
  not own that still wins is a finding with its file and line. Arguments on PAM lines that
  override the files are judged from the active stacks and fixed through the templates of the
  role's own profile (`authselect apply-changes`); on another profile only the features
  (`without-nullok`) can fix them and the rest is a finding. 5.3.3.2.3 (manual) reports the
  complexity settings in effect. New variables `cis_authselect_profile`, `cis_faillock_deny` (5),
  `cis_faillock_unlock_time` (900), `cis_faillock_root_unlock_time` (60), `cis_pwquality_difok`
  (2), `cis_pwquality_minlen` (14), `cis_pwquality_maxrepeat` (3), `cis_pwquality_maxsequence`
  (3) and `cis_pwhistory_remember` (24), validated at preflight. New `tests/check_pam_scan.py`,
  run in CI. Part of #9.

## [3.0.0_0.0.29]

### Added

- Section 5.2, sudo and su, 5.2.1 to 5.2.12. The role writes its sudo `Defaults` lines
  (5.2.4 `use_pty`, 5.2.5 `logfile`, 5.2.8 `!pwfeedback`, 5.2.9 `!visiblepw`, 5.2.10
  `timestamp_timeout`, 5.2.11 `timestamp_type`) to one file, `/etc/sudoers.d/zz-cis-rhel9`
  (mode 0440), named to sort last because sudo applies the last `Defaults` line it reads. Each
  control judges all the sudoers files sudo reads, not one, writes a line only when the
  effective value is not compliant (a stricter value is never loosened), validates every
  write with `visudo -cf` and checks the whole configuration with `visudo -c`. A
  non-compliant line elsewhere that would still win (a later file, a line after the
  `#includedir` line, or a user, host, command or runas scoped line) is a finding with its
  file and line; the role edits none of them. 5.2.1 installs sudo; 5.2.2 and 5.2.3 set owner
  and mode on the sudoers files and `/etc/sudoers.d`. 5.2.6 (Level 2, still in
  `cis_default_exclusions`) and 5.2.7 remove the `NOPASSWD:` tag and `!authenticate` from
  sudoers files the role does not own, with `visudo -cf` validation, except lines that give
  the account the role is connected as its sudo when no become password is set for the run:
  those are left alone with a message and are a finding. 5.2.12 adds
  `auth required pam_wheel.so use_uid group=sugroup` to `/etc/pam.d/su` after `pam_rootok`
  and creates the group empty; members found in it are a finding and are never removed. New
  variables `cis_sudo_logfile` (`/var/log/sudo.log`), `cis_sudo_timestamp_timeout` (15) and
  `cis_su_group` (`sugroup`), validated at preflight. New `tests/check_sudoers_scan.py`,
  run in CI. Part of #9.

## [3.0.0_0.0.28]

### Added

- Section 5.1, SSH server, 5.1.1 to 5.1.23. The role writes its sshd settings to one
  drop-in, `/etc/ssh/sshd_config.d/00-cis-rhel9.conf`, which sorts before `50-redhat.conf`
  because sshd uses the first value it reads for most keywords (`MaxStartups` takes the last,
  so a later file can override 5.1.18, which is then a finding). Each control judges the effective
  configuration with `sshd -T` (and `sshd -T -C` for the role's own account, so Match
  blocks are seen), writes a line only when the value is not compliant, validates it with
  `sshd -t -f`, and a handler checks the whole configuration with `sshd -t` and reloads
  sshd (never a restart) only when it is running. A value an earlier file sets is a finding;
  the role edits no file it does not own. 5.1.1 to 5.1.4 set owner and mode on `sshd_config`,
  its `.conf` drop-ins, the drop-in folder (0700) and the host keys, which are found from
  `sshd -T` and a glob (a private key keeps the `ssh_keys` group). 5.1.5 to 5.1.7 remove weak
  ciphers, key exchanges and MACs through the system crypto policy, the same modules as
  1.6.2 to 1.6.4, and reload sshd. 5.1.9 sets `Banner /etc/issue.net`. 5.1.10 to 5.1.23 set
  the remaining options. 5.1.8 writes new variables `cis_sshd_allow_users`,
  `cis_sshd_allow_groups`, `cis_sshd_deny_users` and `cis_sshd_deny_groups` (default `[]`)
  only when the account the role is connected as stays allowed; with all four empty it is a
  finding and changes nothing. 5.1.21 does not run while the role is connected as root over
  SSH. New variables `cis_sshd_client_alive_interval` (15), `cis_sshd_client_alive_count_max`
  (3), `cis_sshd_login_grace_time` (60), `cis_sshd_log_level` (`INFO`), `cis_sshd_max_auth_tries`
  (4), `cis_sshd_max_startups` (`10:30:60`) and `cis_sshd_max_sessions` (10), validated at
  preflight. 5.1.11 and 5.1.12 are Level 1 on a workstation and Level 2 on a server.
  Part of #9.

### Changed

- The crypto policy controls 1.6.1 to 1.6.4 and 1.6.7 now also reload sshd (through the
  same handler, only when it is running) after they change the policy, so a running sshd
  reads the new algorithm lists.

## [3.0.0_0.0.27]

### Added

- Section 4.1, Level 2 and manual firewalld controls, which completes section 4: 4.1.10
  sets `LogDenied` to `cis_firewalld_log_denied` only when it is `off`, with
  `firewall-cmd --set-log-denied` when `firewalld` runs and in `firewalld.conf` otherwise;
  4.1.11 blocks the ICMP `timestamp-request` and `timestamp-reply` types permanently in each
  active zone bound to an interface other than `lo` or `virbr*` whose target is `default`
  (removing them from the list when icmp-block-inversion is on) and reloads `firewalld`
  once, and a runtime-only difference is fixed by the reload alone. Neither restricts SSH.
  4.1.5, 4.1.6, 4.1.7 and 4.1.8 are manual: the role prints the loopback interface rules,
  the loopback address rules, the active zones' services and ports and the default zone,
  and changes nothing; 4.1.8 is a lockout risk. New variable `cis_firewalld_log_denied`
  (default `unicast`, or `all`, `broadcast` or `multicast`), validated at preflight.
  Part of #8.

## [3.0.0_0.0.26]

### Added

- Section 4.1 firewalld basics: 4.1.1 installs `firewalld`; 4.1.2 sets `FirewallBackend`
  to `nftables` only when it is explicitly `iptables` and restarts `firewalld` only when it
  runs; 4.1.3 unmasks, enables and starts `firewalld.service`; 4.1.4 sets the permanent
  target of active zones that are `ACCEPT` or empty and reloads `firewalld`, and reloads
  alone on a runtime and permanent mismatch; 4.1.9 stops, disables and masks
  `nftables.service` when it is enabled or active and removes `iptables-services` and `ufw`
  when nothing else needs them. Starting `firewalld` (4.1.3) and replacing an `ACCEPT`
  target (4.1.4) happen only when SSH is already allowed in the zone that applies to the
  role's own connection; otherwise the host is left unchanged and the control is a finding
  to fix by hand. New variable `cis_firewalld_zone_target` (default `default`, or `REJECT`
  or `DROP`), validated at preflight. Part of #8.

## [3.0.0_0.0.25]

### Added

- Section 3.3.2 controls, the IPv6 kernel parameters 3.3.2.1 to 3.3.2.8, using the same
  sysctl logic as 3.3.1: each sets one parameter to 0. They are skipped with no finding
  when IPv6 is disabled (the `ipv6` module parameter `disable` is missing or not 0, or the
  `all` and `default` `disable_ipv6` sysctls are both 1), which preflight records in the
  new fact `cis_ipv6_disabled`. IPv6 forwarding (3.3.2.1, 3.3.2.2) is set to 0, so hosts
  that route IPv6 or run containers or libvirt with IPv6 networking must list those IDs in
  `cis_exclusions`; hosts that rely on the kernel's router-advertisement handling must list
  3.3.2.7 and 3.3.2.8. Part of #7.

## [3.0.0_0.0.24]

### Added

- Section 3.3.1 controls, the IPv4 kernel parameters 3.3.1.1 to 3.3.1.20, using the same
  sysctl logic as 1.5.1 to 1.5.7: the role writes a late-sorting file under
  `/etc/sysctl.d/` and sets the running value, and a conflicting value in
  `/etc/sysctl.conf` is a finding. IPv4 forwarding (3.3.1.1 to 3.3.1.3) is set to 0, so hosts
  that route or run rootful containers or libvirt NAT must list those IDs in
  `cis_exclusions`. 3.3.1.1 is Level 1 on a workstation and Level 2 on a server. Part of #7.

## [3.0.0_0.0.23]

### Added

- Section 3.1 and 3.2 controls. 3.1.1 prints whether IPv6 is disabled for review. 3.1.2
  (Level 1 Server) finds the driver module of every wireless interface and blocks,
  blacklists and unloads it; a host with no wireless interface passes, and a driver that
  cannot be unloaded or found is a finding. 3.1.3 removes `bluez` when nothing else needs
  it, otherwise stops and masks `bluetooth.service` (Level 1 Server, Level 2 Workstation;
  `cis_services_keep` skips it). 3.2.1 to 3.2.6 block, blacklist and unload the `dccp`,
  `tipc`, `rds`, `sctp`, `atm` and `can` kernel modules. Part of #7.

## [3.0.0_0.0.22]

### Fixed

- Preflight now stops the run when `cis_cron_allow_users` or `cis_at_allow_users` is not a
  list, or has an item that is not a plain login name (a typo with a space, a leading digit,
  a trailing newline, an empty string, a number), and names the rejected items. Before, such items were dropped
  without any message. #44

## [3.0.0_0.0.21]

### Added

- Section 2.3 and 2.4 controls. 2.3.1 installs chrony. 2.3.2 appends the new `cis_time_sources`
  lines to `/etc/chrony.conf` when chrony has no `server` or `pool` source (included files
  are followed; DHCP sources under `/run/chrony-dhcp` are ignored) and reports a finding when
  none is configured and the list is empty. 2.3.3 removes only `-u root` from the
  `OPTIONS` in `/etc/sysconfig/chronyd`. Both restart chronyd only when it is running.
  2.4.1.1 unmasks, enables and starts crond. 2.4.1.2 to 2.4.1.8 set root:root and remove
  group and other access on `/etc/crontab` and the `/etc/cron.*` directories, skipping
  missing paths and reporting symlinks. 2.4.1.9 and 2.4.2.1 create the cron and at allow
  files when missing, fix owner, group and mode of the allow and deny files, and add the
  users in the new `cis_cron_allow_users` and `cis_at_allow_users` (never removing any).
  With the empty defaults, a host that had no allow file ends up with an empty one, so only
  root can use `crontab` or `at`. The cron and at controls pass when `cronie` or `at` is not
  installed. Part of #6.

## [3.0.0_0.0.20]

### Fixed

- `LICENSE` no longer says parts of the role are adapted from the RHEL 7 and RHEL 8
  projects or misstates their licenses; it is the plain MIT license. The README credits
  those projects for the structure and approach, says no code is copied from them and
  lists each one's actual license. Fixes #39.

## [3.0.0_0.0.19]

### Added

- Section 2.1.19 to 2.1.23 and 2.2 controls. 2.1.19 passes a host with no mail transfer
  agent or one that listens only on loopback for the mail ports; it sets postfix to
  `loopback-only` (restarting it only when running) and reports any other agent that
  listens more widely. 2.1.20 (Level 2 Server, skipped by default) fails on the "Server with GUI"
  group, gdm or gnome-shell, or a graphical default target; it marks the minimal and
  Server environments as installed first (without installing them, so packages other
  controls removed stay removed) so sshd stays, removes the group and the leftover packages,
  sets the default target to `multi-user.target` and flags a pending reboot while the
  graphical target is still running. 2.1.21 and 2.1.22 remove the X server and Xwayland
  together with everything that depends on them. 2.1.23 prints the listening sockets
  for review. 2.2.1 to 2.2.4 remove the ftp, openldap-clients, telnet and tftp clients
  unless another installed package needs them, which is a finding. Part of #6.
- `cis_services_keep` also skips 2.1.19 to 2.1.22. Part of #6.

## [3.0.0_0.0.18]

### Added

- `docs/review-controls.md`: for each implemented audit-only and manual control, what the
  role reports and what is left for you to decide; the controls skipped by default and why;
  and the controls that behave differently between RHEL 9 minor releases. The README and
  `docs/controls.md` link to it. Fixes #12.
- `tests/check_controls.py` also fails when that page does not list exactly the
  implemented audit-only and manual controls, with their dispositions, and exactly
  `cis_default_exclusions`. Fixes #12.

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

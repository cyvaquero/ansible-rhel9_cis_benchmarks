# rhel9_cis_benchmarks

Ansible role that applies the
[CIS Red Hat Enterprise Linux 9 Benchmark](https://www.cisecurity.org/benchmark/red_hat_linux)
(v3.0.0) to RHEL 9 hosts.

**Status: pre-alpha (3.0.0_0.0.34).** The role skeleton, preflight check, profile
selection, audit mode and lint CI exist, and these controls are implemented:

- kernel modules, 1.1.1.1 to 1.1.1.11;
- mounts, 1.1.2.1.1 to 1.1.2.7.4;
- package manager, 1.2.1.1 to 1.2.2.1;
- SELinux, 1.3.1.1 to 1.3.1.8;
- boot loader, 1.4.1 to 1.4.5;
- kernel and process hardening, 1.5.1 to 1.5.10;
- crypto policy, 1.6.1 to 1.6.7;
- command-line banners, 1.7.1 to 1.7.6;
- GDM, 1.8.1 to 1.8.7;
- services, 2.1.1 to 2.1.23;
- service clients, 2.2.1 to 2.2.4;
- time synchronization, 2.3.1 to 2.3.3;
- job schedulers, 2.4.1.1 to 2.4.2.1;
- network devices and kernel modules, 3.1.1 to 3.2.6;
- IPv4 kernel parameters, 3.3.1.1 to 3.3.1.20;
- IPv6 kernel parameters, 3.3.2.1 to 3.3.2.8;
- firewalld, 4.1.1 to 4.1.11 (section 4 is complete);
- SSH server, 5.1.1 to 5.1.23;
- sudo and su, 5.2.1 to 5.2.12;
- PAM and authselect, 5.3.1.1 to 5.3.3.4.4;
- user accounts and environment, 5.4.1.1 to 5.4.3.4 (section 5 is complete).

Every other control is still planned. Do not run this against hosts you care about.

## Relationship to the RHEL 7 and RHEL 8 projects

This role follows the structure and approach of
[ansible-rhel7_cis_benchmarks](https://github.com/cyvaquero/ansible-rhel7_cis_benchmarks) and
[ansible-rhel8_cis_benchmarks](https://github.com/cyvaquero/ansible-rhel8_cis_benchmarks),
which build on [ansible-role-cis-amazon-linux](https://github.com/anthcourtney/ansible-role-cis-amazon-linux)
by Anth Courtney. It is a new implementation for RHEL 9: control IDs follow the RHEL 9
benchmark, it uses current RHEL 9 tooling, and it adds Server and Workstation profiles and
an audit mode. No code is copied from those projects.

Their licenses, for reference:

- ansible-rhel7_cis_benchmarks: MIT, copyright 2019 HarryHarcourt.
- ansible-rhel8_cis_benchmarks: no license file; its README says BSD and its role
  metadata says MIT.
- ansible-role-cis-amazon-linux: MIT, copyright 2014 Mikael Sandström.

## Requirements

- Control node: Ansible 8.7 or later (ansible-core 2.15 or later). The role uses nothing
  newer than ansible-core 2.15, so it runs from a RHEL 9 control node on Python 3.9.
- Collections: `ansible.posix` and `community.general`, both bundled with the Ansible 8.7
  package.
- Managed nodes: RHEL 9, any minor release. Where a control behaves differently between
  minor releases, the tasks detect the release and branch on it.

## Controls

[docs/controls.md](docs/controls.md) lists every benchmark recommendation by CIS ID with
its profile, whether this role implements it, only audits it, or leaves it for manual
review, and its status: `implemented` (the task file exists) or `planned`.
[docs/review-controls.md](docs/review-controls.md) lists the implemented controls that only
report, what each one reports and what is left for you to decide, plus the controls
excluded by default and those that depend on the RHEL 9 minor release. The
benchmark text itself is not reproduced here; get the benchmark from
[CIS](https://www.cisecurity.org/cis-benchmarks).

## Preflight

The role first prints the benchmark it implements (title, version and date, from
`cis_benchmark` in `vars/main.yml`; the end-of-run summary repeats the title and version),
then checks that the host is Red Hat Enterprise Linux 9 and fails with a clear message
otherwise. It sets `cis_rhel_minor_release`, a string such as `"4"` on RHEL 9.4,
for tasks that differ between minor releases. Compare it with the `int` filter, for
example `cis_rhel_minor_release | int >= 4`.

It then validates the selection variables below and fails with a clear message on an
invalid `cis_profile`, a `cis_apply_level_2`, `cis_audit_only` or `cis_fail_on_findings`
that is not true or false, a `cis_firewalld_zone_target` other than `default`, `REJECT` or
`DROP`, or a CIS ID in `cis_exclusions` that is not in the benchmark. The section 1 and 2 variables
below are checked for type and format only (a yes/no value, a whole number, a quoted octal mode,
a name, a path, a list), never against the benchmark's bounds; see "Overriding values".

## Usage (planned)

Install the role into a `roles/` directory next to your playbook as
`rhel9_cis_benchmarks`, then:

```yaml
---
# Hosts
- hosts: "{{ target }}"
  become: true
  gather_facts: true

# Vars
  vars:
    cis_profile: server

# Roles
  roles:
    - rhel9_cis_benchmarks
...
```

```sh
ansible-playbook -i inventory site.yml -e target=webservers
```

### Selecting profiles

| Variable | Default | Meaning |
|---|---|---|
| `cis_apply_level_2` | `false` | Level 1 always runs. `true` adds Level 2, which includes Level 1. |
| `cis_profile` | `server` | `server` or `workstation`. |
| `cis_exclusions` | `[]` | Your list of CIS IDs to skip, for example `["1.1.1.10"]`. |
| `cis_default_exclusions` | `["2.1.20", "2.1.21", "2.1.22", "5.2.6"]` | Controls skipped by default because they can disrupt or lock out a host (they remove the desktop, or make `sudo` ask for a password, which breaks passwordless `become`). Set it to `[]` or a shorter list to run them; `cis_exclusions` is unaffected. |

- Each control has a level per profile (some are Level 1 for Server but Level 2 for
  Workstation), so the same control can run at different levels in the two profiles.
- Controls with no Workstation profile in the benchmark (for example 2.1.11 and 3.1.2)
  never run with `cis_profile: workstation`.
- A control runs when it is in the selected level and profile and in neither exclusion
  list. Preflight records the result in `cis_selected_controls`.
- Tags: run a section, level or single control, for example `-t section-5` or
  `-t 5.1.21`.

### Overriding values

Every value a control writes or expects comes from a role variable whose default is the
benchmark value; the variables for sections 1 to 3 are listed below, and each has a comment in
`defaults/main.yml`. Set one at any Ansible precedence level above the role defaults:
inventory or `group_vars` / `host_vars`, play `vars`, role parameters, `set_fact` and `-e`.
Do not edit the role's own files.

```yaml
roles:
  - role: rhel9_cis_benchmarks
    vars:
      cis_sysctl_kernel_kptr_restrict: 2
      cis_tmp_mount_options: [nodev, nosuid]
      cis_libselinux_installed: true
```

- The role enforces the configured value exactly: whenever the host differs from it, the role
  changes the host to it, also when the host is stricter than the benchmark (with the defaults, a
  `kernel.kptr_restrict` of 2 becomes 1, a screen lock delay of 0 becomes 5 and a banner file of
  mode 0600 becomes 0644). A second run with the same values changes nothing. The checks always
  judge against the benchmark value (constants in `vars/main.yml`, named `cis_expect_*`, which are
  not meant to be overridden): a configured value stricter than the benchmark's passes, a weaker
  one is written and the control reports a finding, in remediate and audit mode; a site that
  accepts the weaker value lists the control in `cis_exclusions`. In audit mode nothing is
  written and a host that differs from the configured value but meets the benchmark is not a
  finding.
- For a package, the variable is whether it should be installed: the role installs or removes
  the package to match it, and the control reports a finding while the host differs from the
  benchmark. This holds for every package of sections 2 and 3 (the service and client packages,
  chrony, bluez), with its own variable (`cis_<name>_installed`); `cis_services_keep` wins over them: a control
  listed there is skipped completely, so nothing is installed or removed for it.
- Preflight checks only the type and format of each value (a yes/no value, a whole number, a
  quoted octal mode such as `"0640"`, a name, a path, a list) and stops the run on anything
  else. Quote file modes: an unquoted `0600` is a number in YAML. Values passed with `-e` are
  strings; use JSON (`-e '{"cis_tmp_mount_options": ["nodev"]}'`) for lists.

### Kernel modules, mounts, package manager and SELinux (1.1 to 1.3)

| Variable | Default | Meaning |
|---|---|---|
| `cis_module_<name>_blocked` | `true` | 1.1.1.1 to 1.1.1.10: whether the role blocks (install line to `/bin/false` plus blacklist) and unloads the module. `<name>` is `cramfs`, `freevxfs`, `hfs`, `hfsplus`, `jffs2`, `overlay`, `squashfs`, `udf`, `firewire_core` or `usb_storage`. `false` removes the role's own `/etc/modprobe.d/<module>.conf` (a file it did not write stays) and the control reports the module as not blocked. |
| `cis_tmp_mount_enabled` | `true` | 1.1.2.1.1: enable `tmp.mount` (for the next boot) when `/tmp` is not a mount point. `false` does not enable it; the role never disables a `tmp.mount` the host already enabled. |
| `cis_tmp_mount_options`, `cis_dev_shm_mount_options`, `cis_home_mount_options`, `cis_var_mount_options`, `cis_var_tmp_mount_options`, `cis_var_log_mount_options`, `cis_var_log_audit_mount_options` | `/tmp`, `/dev/shm`, `/var/tmp`, `/var/log`, `/var/log/audit`: `[nodev, nosuid, noexec]`; `/home`, `/var`: `[nodev, nosuid]` | 1.1.2.x.2 to 1.1.2.x.4: the options that mount point holds. A listed option is added (fstab entry, unit drop-in, remount); one of `nodev`, `nosuid`, `noexec` left out of the list is removed from the fstab entry or drop-in and remounted out, and its control reports a finding while the mount lacks it. Other fstab options are never touched. |
| `cis_dnf_gpgcheck` | `true` | 1.2.1.2: the `gpgcheck` value written to `dnf.conf` and to each repository file (except `redhat.repo`) where it is off. |
| `cis_dnf_install_weak_deps` | `false` | 1.2.1.5 (Level 2): the `install_weak_deps` value written to `dnf.conf`. |
| `cis_libselinux_installed` | `true` | 1.3.1.1: whether `libselinux` should be installed. `false` removes it; leave it `true` unless the host does not need SELinux tooling. |
| `cis_selinux_remove_boot_args` | `["selinux=0", "enforcing=0"]` | 1.3.1.2: the kernel arguments removed from every boot entry. |
| `cis_selinux_policy` | `targeted` | 1.3.1.3: the `SELINUXTYPE` written to `/etc/selinux/config`; the policy must be installed. |
| `cis_selinux_target_mode` | `enforcing` | 1.3.1.5 (Level 2): the SELinux mode set in the configuration and at runtime (`enforcing`, `permissive` or `disabled`). |
| `cis_mcstrans_installed` | `false` | 1.3.1.7: whether `mcstrans` should be installed. |
| `cis_setroubleshoot_installed` | `false` | 1.3.1.8 (Server profile): whether `setroubleshoot` and `setroubleshoot-server` should be installed. |

### Boot loader, kernel and crypto policy (1.4 to 1.6)

| Variable | Default | Meaning |
|---|---|---|
| `cis_grub_password_hash` | `""` | 1.4.1: a `grub.pbkdf2.sha512...` hash from `grub2-mkpasswd-pbkdf2`. Empty: 1.4.1 only reports a missing boot loader password and changes nothing. Set: the role writes it to `/boot/grub2/user.cfg`. The hash is a secret: keep it in Ansible Vault. A value that is not in the hash format is a finding and is not written. |
| `cis_bootloader_file_owner`, `cis_bootloader_file_group`, `cis_bootloader_file_mode` | `root`, `root`, `"0600"` | 1.4.1, 1.4.2: the owner, group and mode set on `user.cfg` and on `grub.cfg`, `grubenv` and `user.cfg`. |
| `cis_bootloader_efi_uid`, `cis_bootloader_efi_gid`, `cis_bootloader_efi_umask` | `0`, `0`, `"0077"` | 1.4.2: the `uid`, `gid` and `umask` options set on the `/boot/efi` vfat fstab entry. |
| `cis_rescue_exec_start`, `cis_emergency_exec_start` | `-/usr/lib/systemd/systemd-sulogin-shell rescue` and `... emergency` | 1.4.3, 1.4.4 (Level 2): the `ExecStart` written in the drop-in of `rescue.service` and `emergency.service`. |
| `cis_systemd_confirm_spawn` | `false` | 1.4.5: the `ConfirmSpawn` value written where it is on. |
| `cis_remove_confirm_spawn_boot_arg` | `true` | 1.4.5: whether `systemd.confirm_spawn` is removed from the boot entries. |
| `cis_sysctl_fs_protected_hardlinks`, `cis_sysctl_fs_protected_symlinks`, `cis_sysctl_fs_suid_dumpable`, `cis_sysctl_kernel_dmesg_restrict`, `cis_sysctl_kernel_kptr_restrict`, `cis_sysctl_kernel_randomize_va_space`, `cis_sysctl_kernel_yama_ptrace_scope` | `1`, `1`, `0`, `1`, `1`, `2`, `1` | 1.5.1 to 1.5.7: the value written to `/etc/sysctl.d/99-zz-cis-benchmarks.conf` and set live when the configured value is not accepted. |
| `cis_core_hard_limit` | `0` | 1.5.8: the `* hard core` value written to the role's `limits.d` file. |
| `cis_coredump_process_size_max`, `cis_coredump_storage` | `"0"`, `none` | 1.5.9, 1.5.10: the `ProcessSizeMax` and `Storage` written to the role's `coredump.conf.d` drop-in. |
| `cis_crypto_policy_base` | `DEFAULT` | 1.6.1: the base policy that replaces `LEGACY`. |
| `cis_crypto_policy_module_sha1`, `cis_crypto_policy_module_pq` | `NO-SHA1`, `PQ` | 1.6.2, 1.6.7 (Level 2): the shipped policy module appended to the policy. |
| `cis_crypto_policy_module_mac`, `cis_crypto_policy_mac_excluded` | `CIS-NO-WEAKMAC`, `["*-64", "*-MD5"]` | 1.6.3: the role's own module and the MAC patterns it removes. |
| `cis_crypto_policy_module_sshcbc`, `cis_crypto_policy_ssh_ciphers_excluded` | `CIS-NO-SSHCBC`, `["*-CBC"]` | 1.6.4: the role's own module and the SSH cipher patterns it removes. |

### Banners and GDM (1.7, 1.8)

| Variable | Default | Meaning |
|---|---|---|
| `cis_motd_path`, `cis_issue_path`, `cis_issue_net_path` | `/etc/motd`, `/etc/issue`, `/etc/issue.net` | 1.7.1 to 1.7.6: the banner files. |
| `cis_banner_text` | a short notice that the computer is for approved users and use may be logged | The text the role holds in the three banner files (1.7.1 to 1.7.3) and as the GDM login banner (1.8.1). A file or banner that differs from it is replaced, also when its text is compliant, so a site's own banner is overwritten: set your text here. Keep it free of the escapes `\m`, `\r`, `\s`, `\v` and of the operating system name, or the controls cannot pass. |
| `cis_banner_file_owner`, `cis_banner_file_group`, `cis_banner_file_mode` | `root`, `root`, `"0644"` | 1.7.1 to 1.7.6: the owner, group and mode of a new banner file; 1.7.4 to 1.7.6 set exactly this owner, group and mode on an existing file that differs (a stricter mode is replaced). |
| `cis_gdm_banner_enable`, `cis_gdm_disable_user_list` | `true`, `true` | 1.8.1, 1.8.2: the `banner-message-enable` and `disable-user-list` values. |
| `cis_gdm_idle_delay` | `900` | 1.8.3: the idle time in seconds the role writes when the configured one is not accepted. The check accepts 1 to 900 (0, never, is not). |
| `cis_gdm_lock_delay` | `5` | 1.8.3: the lock delay in seconds the role writes when the configured one is not accepted. The check accepts 0 to 5. |
| `cis_gdm_automount`, `cis_gdm_automount_open` | `false`, `false` | 1.8.4: the `automount` and `automount-open` values. |
| `cis_gdm_autorun_never` | `true` | 1.8.5: the `autorun-never` value. |
| `cis_gdm_xdmcp_enable` | `false` | 1.8.6: the `Enable` value written in `[xdmcp]` when it is true or 1. |
| `cis_gdm_wayland_enable` | `absent` | 1.8.7: `absent` removes a `WaylandEnable` of false or 0 from `[daemon]`; `true` sets it to true. |

### Services (2.1.1 to 2.1.22 and 3.1.3)

| Variable | Default | Meaning |
|---|---|---|
| `cis_services_keep` | `[]` | CIS IDs of service controls whose service the site needs, for example `["2.1.1", "2.1.10"]`. A listed control (2.1.1 to 2.1.22, or 3.1.3 for bluetooth) is skipped with no change and no finding. It wins over the package variables below: nothing is installed or removed for a listed control, whatever they say. |
| `cis_autofs_installed`, `cis_avahi_installed`, `cis_cockpit_installed`, `cis_cockpit_ws_installed`, `cis_dhcp_server_installed`, `cis_bind_installed`, `cis_dnsmasq_installed`, `cis_samba_installed`, `cis_vsftpd_installed`, `cis_dovecot_installed`, `cis_cyrus_imapd_installed`, `cis_nfs_utils_installed`, `cis_cups_installed`, `cis_rpcbind_installed`, `cis_rsync_daemon_installed`, `cis_net_snmp_installed`, `cis_telnet_server_installed`, `cis_tftp_server_installed`, `cis_squid_installed`, `cis_httpd_installed`, `cis_nginx_installed` | `false` | 2.1.1 to 2.1.18 (2.1.3 is Level 2): whether each service package should be installed, named after the package (`dhcp-server`, `bind`, `nfs-utils`, `cups`, ...). `false`: the role removes it when no other installed package needs it, otherwise stops and masks its units. `true`: the role installs it when missing and leaves its units alone, and the control reports a finding on every run, since the benchmark wants it absent. Set packages that depend on each other together (`cockpit` and `cockpit-ws`). |
| `cis_x_server_installed`, `cis_xwayland_installed` | `false` | 2.1.21, 2.1.22 (Level 2, skipped by default): whether `xorg-x11-server-common` and `xorg-x11-server-Xwayland` should be installed. `false` removes them with everything that depends on them. `true` installs them when missing. |
| `cis_gui_installed` | `false` | 2.1.20 (Level 2 Server, skipped by default): whether the graphical interface (the "Server with GUI" group) should be installed. `false` removes the group; `true` installs the group when it is missing and removes nothing, and the control reports a finding. |
| `cis_default_target` | `multi-user.target` | 2.1.20: the default systemd target the role links `default.target` to whenever it is another one, also when it is not `graphical.target`. `graphical.target` is reported as a finding. |
| `cis_postfix_inet_interfaces` | `loopback-only` | 2.1.19: the postfix `inet_interfaces` value the role sets (`postconf -e`) whenever the current one differs, also when it is already loopback only in another spelling (`localhost`). postfix restarts only when running. A value that is not loopback only is written and reported as a finding. |

### Client packages (2.2)

| Variable | Default | Meaning |
|---|---|---|
| `cis_ftp_client_installed`, `cis_ldap_client_installed`, `cis_telnet_client_installed`, `cis_tftp_client_installed` | `false` | 2.2.1, 2.2.2 (Level 2), 2.2.3, 2.2.4: whether `ftp`, `openldap-clients`, `telnet` and `tftp` should be installed. `false` removes the package when nothing else needs it (a needed one stays and is reported); `true` installs it when missing and the control reports a finding. |

### Time synchronization and job schedulers (2.3, 2.4)

| Variable | Default | Meaning |
|---|---|---|
| `cis_chrony_installed` | `true` | 2.3.1: whether `chrony` should be installed. `false` removes it when no other installed package needs it; one that is needed stays installed and `chronyd` is stopped and masked instead. `true` only installs it: the role never enables or starts `chronyd`. `false` is reported as a finding when chrony is gone. |
| `cis_time_sources` | `[]` | 2.3.2: the time sources, as full chrony directive lines, for example `["server time.example.com iburst"]`. Empty: the host's sources are left alone (a host with no source is a finding). Non-empty: the role enforces the list exactly. The `server` and `pool` lines in `/etc/chrony.conf` and in the files it includes (`include`, `confdir`, and the `sourcedir` `*.sources` files, never the DHCP directory) become exactly the list: other such lines are removed, missing ones are appended to `/etc/chrony.conf`, nothing else is touched, and `chronyd` restarts only on a change. |
| `cis_chronyd_run_as_root` | `false` | 2.3.3: whether `chronyd` runs as root. `false` removes the `-u root` option from `OPTIONS` in `/etc/sysconfig/chronyd` and keeps the others; `true` drops every `-u` option and sets `-u root` (creating the file or the line when missing). `true` is reported as a finding. |
| `cis_cronie_installed` | `null` | 2.4.1.1: whether `cronie` should be installed. `null` leaves it alone (the benchmark judges cron only when it is installed); `true` installs it when missing (install only; the controls then enable and start `crond` as usual and create an empty `cron.allow`); `false` removes it when no other installed package needs it, otherwise it stays and `crond` is stopped and masked. The cron controls still judge the benchmark (they pass without `cronie`). |
| `cis_at_installed` | `null` | 2.4.2.1: whether `at` should be installed. `null` leaves it alone (the control applies only when it is installed); `true` installs it, `false` removes it with the same rules as `cronie`. |
| `cis_crond_enabled`, `cis_crond_active` | `true`, `true` | 2.4.1.1: whether `crond` is enabled and whether it is running. The role unmasks, enables and starts it, or stops and disables it, to match; `false` is reported as a finding. |
| `cis_cron_owner`, `cis_cron_group` | `root`, `root` | 2.4.1.2 to 2.4.1.8: the owner and group set on `/etc/crontab` and the `/etc/cron.*` directories. |
| `cis_cron_file_mode`, `cis_cron_dir_mode` | `"0600"`, `"0700"` | 2.4.1.2: the mode of `/etc/crontab`; 2.4.1.3 to 2.4.1.8: the mode of the directories. A stricter mode is replaced. |
| `cis_cron_allow_owner`, `cis_cron_allow_group`, `cis_cron_allow_mode` | `root`, `crontab`, `"0640"` | 2.4.1.9: the owner, group and mode set on `/etc/cron.allow` and `/etc/cron.deny` (when present) and on a new `cron.allow`. A group that does not exist on the host is replaced by `root`; the benchmark accepts `root` or `crontab`. |
| `cis_at_allow_owner`, `cis_at_allow_group`, `cis_at_allow_mode` | `root`, `daemon`, `"0640"` | 2.4.2.1: the same for `/etc/at.allow` and `/etc/at.deny`; the benchmark accepts `root` or `daemon`. |
| `cis_cron_allow_users` | `[]` | 2.4.1.9: users added to `/etc/cron.allow` when missing from it. Users already in the file are never removed. Must be a list of plain login names; anything else stops the run at preflight. |
| `cis_at_allow_users` | `[]` | 2.4.2.1: users added to `/etc/at.allow`, with the same rules; invalid names stop the run at preflight. |

**Warning:** with the default empty lists, a host that had no `/etc/cron.allow` (or
`/etc/at.allow`) gets an empty one, and from then on only root can use `crontab` (or `at`):
once an allow file exists the deny file is ignored. List every account that needs them
before running the role on such a host. To skip a control, list its ID in `cis_exclusions`;
`cis_services_keep` applies only to the service controls (2.1.1 to 2.1.22, and 3.1.3).

### Network devices, kernel modules and network parameters (3.1 to 3.3)

| Variable | Default | Meaning |
|---|---|---|
| `cis_module_wireless_blocked` | `true` | 3.1.2: whether the role blocks (install line to `/bin/false` plus blacklist) and unloads the driver module of each wireless interface. The modules are found at run time, so one variable covers them all. `false` removes the role's own `/etc/modprobe.d/<module>.conf` for wireless drivers (a file it did not write stays), blocks and unloads nothing, and 3.1.2 reports a finding while a wireless interface exists. |
| `cis_bluez_installed` | `false` | 3.1.3: whether `bluez` should be installed. `false` removes it when no other installed package needs it, otherwise stops and masks `bluetooth.service`. `true` installs it when missing and leaves the unit alone; the control reports a finding on every run. `cis_services_keep` listing 3.1.3 wins. |
| `cis_module_dccp_blocked`, `cis_module_tipc_blocked`, `cis_module_rds_blocked`, `cis_module_sctp_blocked`, `cis_module_atm_blocked`, `cis_module_can_blocked` | `true` | 3.2.1 to 3.2.6: whether the role blocks and unloads the module, as for 1.1.1.x. `false` removes the role's own drop-in for it (a file it did not write stays) and the control reports the module as not blocked. |
| `cis_sysctl_net_ipv4_<parameter>` | `0`, except `1` for `icmp_ignore_bogus_error_responses`, `icmp_echo_ignore_broadcasts`, `conf_all_rp_filter`, `conf_default_rp_filter`, `conf_all_log_martians`, `conf_default_log_martians` and `tcp_syncookies` | 3.3.1.1 to 3.3.1.20: the value held for `net.ipv4.<parameter>`, with dots written as underscores (`cis_sysctl_net_ipv4_ip_forward`, `cis_sysctl_net_ipv4_conf_all_send_redirects`, `cis_sysctl_net_ipv4_conf_default_route_localnet`, and so on, one per control). The role writes it to `/etc/sysctl.d/99-zz-cis-benchmarks.conf` and sets it live whenever the configured or the running value is another one, a stricter value included. A whole number. |
| `cis_sysctl_net_ipv6_<parameter>` | `0` | 3.3.2.1 to 3.3.2.8: the same for `net.ipv6.conf.all.` and `net.ipv6.conf.default.` `forwarding`, `accept_redirects`, `accept_source_route` and `accept_ra` (`cis_sysctl_net_ipv6_conf_all_accept_ra`, ...). These controls are skipped, with no finding, while IPv6 is disabled on the host. |

A site that needs IPv4 or IPv6 forwarding can set the forwarding variables to 1 instead of excluding
the controls; the control then reports a finding on every run. 3.1.1 (manual) only reports.

### Firewall (4.1)

| Variable | Default | Meaning |
|---|---|---|
| `cis_firewalld_zone_target` | `default` | 4.1.4: the permanent target set on an active zone whose target is `ACCEPT` or empty. One of `default`, `REJECT` or `DROP`; anything else stops the run at preflight. A target that is already acceptable is never changed. |
| `cis_firewalld_log_denied` | `unicast` | 4.1.10 (Level 2): the `LogDenied` value set when it is `off`. One of `all`, `unicast`, `broadcast` or `multicast`; anything else stops the run at preflight. A value other than `off` is never changed. |

### SSH server (5.1)

| Variable | Default | Meaning |
|---|---|---|
| `cis_sshd_allow_users`, `cis_sshd_allow_groups`, `cis_sshd_deny_users`, `cis_sshd_deny_groups` | `[]` | 5.1.8: users and groups written to `AllowUsers`, `AllowGroups`, `DenyUsers` and `DenyGroups` in the role's sshd drop-in. A non-empty list is written; an empty one leaves that directive alone. All empty: nothing is written, and 5.1.8 is a finding unless a list is already in effect. Plain names only (letters, digits, underscore, dot, hyphen); anything else stops the run at preflight. **Lockout risk:** an allow list locks out every account not in it, and a deny list every account in it. The role writes the lists only when the account it is connected as is still allowed by the result; otherwise it changes nothing and says why. List every account that needs SSH, including the one Ansible uses. |
| `cis_sshd_client_alive_interval`, `cis_sshd_client_alive_count_max` | `15`, `3` | 5.1.10: the values written when the effective ones are not both above zero. Whole numbers of 1 or more. |
| `cis_sshd_login_grace_time` | `60` | 5.1.15: seconds, from 1 to 60, written when the effective value is 0 or above 60. |
| `cis_sshd_log_level` | `INFO` | 5.1.16: `INFO` or `VERBOSE`, written when the effective level is neither. |
| `cis_sshd_max_auth_tries` | `4` | 5.1.17: from 1 to 4, written when the effective value is higher. |
| `cis_sshd_max_startups` | `10:30:60` | 5.1.18: `start:rate:full`, each at least 1 and at most 10, 30 and 60, written when any effective number is higher. |
| `cis_sshd_max_sessions` | `10` | 5.1.19: from 1 to 10, written when the effective value is higher. |

Values outside these ranges stop the run at preflight. A setting that is already compliant,
wherever it comes from, is never changed.

### sudo and su (5.2)

| Variable | Default | Meaning |
|---|---|---|
| `cis_sudo_logfile` | `/var/log/sudo.log` | 5.2.5: the path written as `Defaults logfile=` when no sudo log file is set. An absolute path of letters, digits, underscore, dot, hyphen and slash; anything else stops the run at preflight. A log file the site already set is kept. Rotate the file (logrotate) to keep it from filling the disk. |
| `cis_sudo_timestamp_timeout` | `15` | 5.2.10: minutes, from 1 to 15, written when the effective timeout is above 15 or disabled (negative). No line (sudo's own default of 5) and any value from 0 to 15 are compliant and never changed. |
| `cis_su_group` | `sugroup` | 5.2.12: the group `pam_wheel` allows to use `su`. A plain group name (lowercase letters, digits, underscore, hyphen); anything else stops the run at preflight. The role creates it empty when missing and never adds or removes members. A group that has members is a finding. |

### PAM and authselect (5.3)

| Variable | Default | Meaning |
|---|---|---|
| `cis_authselect_profile` | `cis-rhel9` | 5.3.2.1: the name of the custom authselect profile the role creates (based on `sssd`) and selects on a host authselect does not manage. Lowercase letters, digits, underscore and hyphen, starting with a letter, at most 32 characters, and not `minimal`, `sssd`, `winbind` or `nis`; anything else stops the run at preflight. A host already on an authselect profile keeps it. |
| `cis_faillock_deny` | `5` | 5.3.3.1.1: `deny` in `/etc/security/faillock.conf`, from 1 to 5, written when the value there is not from 1 to 5. A lower value already set is kept. |
| `cis_faillock_unlock_time` | `900` | 5.3.3.1.2: `unlock_time` in `faillock.conf`, in seconds: 0 (never unlocked automatically) or 900 to 604800. Written when the value there is not 0 or at least 900; a longer time already set is kept. |
| `cis_faillock_root_unlock_time` | `60` | 5.3.3.1.3 (Level 2): seconds, 60 to 604800, used only to replace a `root_unlock_time` below 60 that is already in `faillock.conf`. The role itself adds `even_deny_root`. |
| `cis_pwquality_difok`, `cis_pwquality_minlen` | `2`, `14` | 5.3.3.2.1, 5.3.3.2.2: the values written to the role's pwquality drop-in when the value in effect is below 2 and below 14. A higher value already set anywhere is kept. |
| `cis_pwquality_maxrepeat`, `cis_pwquality_maxsequence` | `3`, `3` | 5.3.3.2.4, 5.3.3.2.5: from 1 to 3, written when the value in effect is unset, 0 or above 3. |
| `cis_pwhistory_remember` | `24` | 5.3.3.3.1: `remember` in `/etc/security/pwhistory.conf`, from 24 to 400, written when the value there is below 24. |

### Accounts and environment (5.4)

| Variable | Default | Meaning |
|---|---|---|
| `cis_pass_max_days` | `365` | 5.4.1.1: the maximum password age, from 1 to 365, written to `PASS_MAX_DAYS` in `login.defs` and with `chage --maxdays` to each existing account that has a password hash, when the value there is not from 1 to 365. A lower value already set is kept. |
| `cis_pass_warn_age` | `7` | 5.4.1.3: the warning days, 7 or more, written to `PASS_WARN_AGE` and with `chage --warndays` to each account with a password hash, when the value there is below 7. A longer warning already set is kept. |
| `cis_inactive_days` | `45` | 5.4.1.5: the inactive days, from 0 to 45, written with `useradd -D -f` and with `chage --inactive` to each account with a password hash, when the value there is unset, negative or above 45. A shorter period already set is kept. |
| `cis_umask` | `"027"` | 5.4.2.6, 5.4.3.3, 5.4.3.4: the umask written to `UMASK` in `login.defs`, to the role's `/etc/profile.d` file and to root's `.bash_profile` and `.bashrc`. Three or four octal digits, 027 or more restrictive, in quotes (an unquoted `027` is the number 23). A stricter umask already set is kept. |
| `cis_tmout` | `900` | 5.4.3.2: the shell idle timeout in seconds, from 1 to 900, written readonly and exported to the role's `/etc/profile.d` file when no file sets `TMOUT`. |
| `cis_account_exceptions` | `[]` | 5.4.2.7, 5.4.2.8: login names of system accounts the role leaves alone (shell and lock state), reported as findings. Plain names; anything else stops the run at preflight. |

Values outside these ranges stop the run at preflight.

### Audit vs remediate

| Variable | Default | Meaning |
|---|---|---|
| `cis_audit_only` | `false` | `false` (remediate) checks and fixes each control. `true` (audit) checks and reports without changing the host. |
| `cis_fail_on_findings` | `false` | `true` fails each host that ends the run with findings, after the summary is printed. |

- Remediate (default): each control is checked and fixed.
- Audit: `-e cis_audit_only=true` checks each control and records a finding for every
  one that fails; nothing on the host changes, so the run reports `changed=0`.
- With `--check`, remediate mode shows which controls would change; audit mode never
  changes anything.
- Controls marked audit-only or manual in `docs/controls.md` only report, in either
  mode. Every one that is selected is listed as a finding, whether or not its check
  passes, so it is not forgotten. [docs/review-controls.md](docs/review-controls.md) says
  what each one reports.
- At the end of every run a summary lists, per host, the failing CIS IDs (in
  `docs/controls.md` order) and how many are audit-only or manual controls to review.
  With `cis_fail_on_findings: true` the host then fails, which suits a CI gate:
  `-e cis_audit_only=true -e cis_fail_on_findings=true`. The audit-only and manual
  controls selected for the run always count, so expect that gate to fail until you
  exclude them in `cis_exclusions`.
- The role never reboots a host. A control whose fix only takes effect after a reboot
  (1.1.2.1.1 enables `tmp.mount` for the next boot rather than mounting tmpfs over a live
  `/tmp`; 1.3.1.2 removes `selinux=0` or `enforcing=0` from the boot entries while the
  running kernel still has it; 1.3.1.4 and 1.3.1.5 configure SELinux on a host that is not
  running it; 1.3.1.3 changes the policy type while another policy is loaded; 1.4.2
  changes the `/boot/efi` mount options and the live mount keeps the old ones; 1.4.5
  removes `systemd.confirm_spawn` while the running kernel still has it; 1.6.1 to 1.6.4, 1.6.7 and
  5.1.5 to 5.1.7 change the crypto policy, which a service reads only when it starts; 1.8.6 and
  1.8.7 change `/etc/gdm/custom.conf`, which a running GDM reads only when it starts) sets
  `cis_reboot_required` to `true`, reports that a reboot is pending, and the
  summary prints `Reboot required`. The variable defaults to `false` and is an output:
  read it after the role runs (for example to schedule a reboot) rather than setting it.
  Audit mode sets it too, from the state it finds.
- Section 1 values below are the defaults of the variables in the tables above; the role
  enforces the configured value exactly (also on a host that is stricter) and the check still
  judges the benchmark value ("Overriding values").
- Mount controls (1.1.2): the `nodev`, `nosuid` and `noexec` controls act only when the
  mount exists, or for `/tmp`, will exist once `tmp.mount` is enabled. They add the option
  to `/etc/fstab` (adding a `/dev/shm` entry if there is none) or, for `/tmp` provided by
  `tmp.mount`, to a drop-in under `/etc/systemd/system/tmp.mount.d/`, and remount the live
  mount; an option left out of the site's list is removed the same way. The audit compares the live options. The separate-partition controls (1.1.2.x.1)
  only report.
- Boot loader and kernel controls (1.4, 1.5): 1.4.2 sets 0600 root:root (`cis_bootloader_file_*`)
  on `grub.cfg`, `grubenv` and `user.cfg` (also a stricter mode is set to it) and, on UEFI hosts,
  makes sure the `/boot/efi` fstab entry has `uid=0`, `gid=0` and `umask=0077`
  (`cis_bootloader_efi_*`, replacing any `fmask` and `dmask`). 1.4.3 and 1.4.4 (Level 2)
  add a drop-in to `rescue.service` or `emergency.service` when their effective
  command is not the configured one. The sysctl controls of section 1 (1.5.1 to 1.5.7) write
  `/etc/sysctl.d/99-zz-cis-benchmarks.conf`, named to sort after the vendor
  and admin files, whenever the configured or the running value is not the configured one, as
  do those of section 3. A value that a later file
  still overrides is a finding. 1.5.8 writes
  `/etc/security/limits.d/99-zz-cis-benchmarks.conf` (`* hard core 0`); entries for other
  users or groups are a finding. 1.5.9 and 1.5.10 write
  `/etc/systemd/coredump.conf.d/99-zz-cis-benchmarks.conf`.
- Crypto policy controls (1.6): compliance is judged on the effective policy
  (`/etc/crypto-policies/state/CURRENT.pol`) and, for the MAC and SSH controls, on the
  generated OpenSSH back-ends. A fix changes the policy string with
  `update-crypto-policies --set`, never a generated file: it keeps the base policy and every
  module already in the string and appends the missing module (`NO-SHA1` for 1.6.2, `PQ` for
  1.6.7). 1.6.1 replaces a base other than `cis_crypto_policy_base` (not a FIPS one) with it.
  The section 1 controls keep their module in the string even when the policy already passes.
  1.6.3 and 1.6.4 write the role's own modules `CIS-NO-WEAKMAC` and `CIS-NO-SSHCBC` to
  `/etc/crypto-policies/policies/modules/` and rewrite them when the variables change. 1.6.7 (Level 2) is a finding on a minor release without
  the `PQ` module. The role restarts no service and never touches FIPS mode; a reboot is
  flagged while the policy state is newer than the boot. 1.6.5 and 1.6.6 only report. A
  back-end edited by hand is a finding, as the role does not edit generated files.
- Package manager and SELinux controls (1.2, 1.3): 1.2.1.2 never edits `redhat.repo`
  (subscription-manager owns it); a repository there with `gpgcheck=0` is a finding.
  1.3.1.4 moves a disabled SELinux configuration to the running mode (permissive when it is
  not running), creates `/.autorelabel` when SELinux starts at the next boot, and never
  lowers an enforcing host. 1.3.1.5 (Level 2) enforces only a host that is running
  SELinux: on a host that is not, run the role again after the relabeling reboot. The
  SELinux changes need `python3-libselinux` on the managed node.
- Banner controls (1.7): a file is not compliant when it holds a login escape
  (`\m`, `\r`, `\s`, `\v`, any case) or the operating system name from `/etc/os-release`;
  `/etc/issue` and `/etc/issue.net` must also hold text, while an empty or missing
  `/etc/motd` is compliant (the check judges only these rules). The fix makes each file hold
  exactly `cis_banner_text` and a final newline whenever it differs, also when it is compliant, so
  a site's own banner is replaced. 1.7.4 to 1.7.6 require root:root and no write for
  group or other and no execute bit (0644 or stricter); the fix sets exactly the configured owner,
  group and mode, also on a stricter file. A
  symlink is a finding for all six and is never replaced or chmod-ed. `/etc/motd.d` and
  sshd's banner (section 5) are not touched.
- GDM controls (1.8): they run only when the `gdm` package is installed; otherwise they are
  skipped with no finding. 1.8.1 to 1.8.5 write system-wide dconf keys to
  `/etc/dconf/db/gdm.d/00-cis-benchmarks` (login screen) and
  `/etc/dconf/db/local.d/00-cis-benchmarks` (session, screen saver and media handling), lock
  each key in the matching `locks/00-cis-benchmarks` file so users cannot override it, and run
  `dconf update`. A key is compliant when its effective value, read from the compiled
  databases with `dconf read` under the GDM or user profile with an empty home folder, is
  accepted and the key is locked; a correct but unlocked key only gets the lock. A site file
  that sorts later and overrides a key stays a finding, as does a `user` profile without
  `system-db:local`; the role creates `/etc/dconf/profile/user` only when it is missing.
  The configured value is written whenever the effective one differs, also when it already
  passes (a screen lock delay of 0 becomes 5 with the defaults); the banner text too (exactly `cis_banner_text`). 1.8.4 sets `automount` and `automount-open` to false (Level 1 for Server, Level 2 for
  Workstation). 1.8.6 sets `Enable=false` in the `[xdmcp]` section of `/etc/gdm/custom.conf`
  when it is true, and 1.8.7 removes an active `WaylandEnable=false` from `[daemon]`. GDM
  reads `custom.conf` only when it starts, so while GDM is running and the file is newer
  than its start these two set `cis_reboot_required` (in both modes, not a finding).
  dconf changes apply to sessions started afterwards. The role never restarts GDM.
- Service controls (2.1.1 to 2.1.18): for each service the role decides on the host. A
  package of the service that no other installed package needs is removed with dnf (decided
  with an `rpm -e --test` of the control's installed packages together). A package that
  another package needs stays installed and its units (services, sockets, paths) are
  stopped and masked instead, and the same happens to a unit that exists with no listed
  package installed. Masked and inactive units are compliant. Dependents are never
  removed. Audit mode only reports. `cis_services_keep` lists the controls to skip for a
  service the site needs. A package whose `cis_<name>_installed` variable is `true` is
  installed when missing, never removed, and its units are left alone; the control reports
  a finding while it is installed.
- Mail transfer agents (2.1.19): a host with no MTA, or whose MTA listens only on loopback
  for the mail ports (25, 465, 587), passes. The check reads the listening sockets (`ss`)
  and, for postfix, `inet_interfaces`. A postfix whose `inet_interfaces` is not exactly
  `cis_postfix_inet_interfaces` (`loopback-only` by default; `localhost` becomes
  `loopback-only`) gets it (`postconf -e`) and is restarted only when it is running. Any other
  MTA that listens beyond loopback is a finding and is never edited.
- Desktop and X server (2.1.20 to 2.1.22, Level 2 Server, skipped by default): 2.1.20 fails
  while the "Server with GUI" environment group is installed, or while the default target is `graphical.target`. To fix it the role first
  marks the minimal and Server environments as installed (so `openssh-server` and the other
  packages shared with a plain server stay wanted; nothing is installed, so packages other
  controls removed do not come back), removes the GUI group, and points the default target at
  `cis_default_target` (`multi-user.target`) whenever it is another one. With
  `cis_gui_installed: true` it installs the group instead and removes nothing. It records a finding if `openssh-server` is gone afterwards. 2.1.21
  and 2.1.22 remove `xorg-x11-server-common` and `xorg-x11-server-Xwayland` with dnf
  together with every installed package that depends on them. The role never stops the
  display manager or reboots: while the graphical target is still running on a compliant
  host, it sets `cis_reboot_required` (in audit mode too) and that is not a finding.
  `cis_services_keep` skips these controls.
- Listening sockets (2.1.23, manual): the role prints `ss -plntu` for review, never changes
  anything, and records no finding.
- Client controls (2.2.1 to 2.2.4: ftp, openldap-clients, telnet, tftp): the package is removed
  when no other installed package needs it (an `rpm -e --test` decides); one that is needed
  stays installed, dependents are never removed, and that is a finding. A client whose
  `cis_<name>_client_installed` is `true` is installed when missing and reported as a finding.
- Network devices and kernel modules (3.1, 3.2): 3.1.1 (manual) prints whether IPv6 is
  disabled, from the `ipv6` module parameter and the `all` and `default` `disable_ipv6`
  sysctls, and changes nothing. 3.1.2 (Level 1 Server) finds each wireless interface
  (`/sys/class/net/*/wireless`), takes its driver module and makes it unavailable the way
  the kernel module controls do (modprobe.d drop-in with an `install ... /bin/false` line
  and a blacklist, then unloaded). A host with no wireless interface passes. A driver that
  cannot be unloaded, or an interface whose driver module cannot be found (built in), is a
  finding. With `cis_module_wireless_blocked: false` it blocks and unloads nothing and removes
  the role's own drop-ins for wireless drivers. 3.1.3 (Level 1 Server, Level 2 Workstation)
  works like the service controls above for `bluez` and `bluetooth.service`
  (`cis_bluez_installed`): the package is removed when nothing else needs it, otherwise the unit
  is stopped and masked, and a host without `bluez` passes; `cis_services_keep` skips it.
  3.2.1 to 3.2.6 block, blacklist and unload `dccp`, `tipc`, `rds`, `sctp`, `atm` and `can`
  like 1.1.1.1 (`cis_module_<name>_blocked`); a module the kernel does not ship passes.
- IPv4 kernel parameters (3.3.1): each control holds one parameter at the value of its variable
  (`cis_sysctl_net_ipv4_*`, default the benchmark value) through the shared sysctl logic
  described under the boot loader and kernel controls above: forwarding, send, accept and secure
  redirects, source routing and `route_localnet` default to 0; bogus ICMP error and broadcast
  echo ignoring, `rp_filter`, `log_martians` and `tcp_syncookies` default to 1. The check accepts
  only the benchmark value. 3.3.1.1 is Level 1 on a workstation and Level 2 on a server.
  3.3.1.1 to 3.3.1.3 turn IPv4 forwarding off by default. A host that routes, or runs rootful
  containers or libvirt NAT, needs forwarding: list 3.3.1.1, 3.3.1.2 and 3.3.1.3 in
  `cis_exclusions` (or set their variables to 1 and accept the finding). Likewise a host that
  relies on `route_localnet` or asymmetric routing (`rp_filter`) excludes those IDs.
- IPv6 kernel parameters (3.3.2): each control holds one parameter (forwarding, accept
  redirects, accept source route, accept router advertisements, each for `all` and
  `default`) at the value of its variable (`cis_sysctl_net_ipv6_*`, default 0) through the
  shared sysctl logic described above. The controls are
  skipped, with no finding, when IPv6 is disabled: when the `ipv6` module parameter
  `disable` is missing or not 0, or when both the `all` and `default` `disable_ipv6`
  sysctls are 1. 3.3.2.1 and 3.3.2.2 turn IPv6 forwarding off, so a host that routes IPv6,
  or runs containers or libvirt with IPv6 networking, lists them in `cis_exclusions`. A host
  that relies on the kernel's own router-advertisement handling for its IPv6 address or
  default route (not NetworkManager, which processes router advertisements itself) lists
  3.3.2.7 and 3.3.2.8 in `cis_exclusions`.
- Firewall (4.1): 4.1.1 installs `firewalld`. 4.1.2 changes `FirewallBackend` in
  `/etc/firewalld/firewalld.conf` only when it is explicitly `iptables` (a missing line
  already means `nftables`), and restarts `firewalld` only when it is running. 4.1.3
  unmasks, enables and starts `firewalld.service`. 4.1.4 checks every active zone bound to
  an interface other than `lo` or `virbr*`: its target must not be `ACCEPT` or empty, and
  the runtime and permanent targets must match. A zone with such a target gets
  `cis_firewalld_zone_target` as its permanent target, then `firewalld` is reloaded; a
  runtime and permanent mismatch with an acceptable permanent target is fixed by the reload
  alone (which also drops runtime-only changes). No active zone is a finding with nothing
  to change. 4.1.9 requires `nftables.service` to be neither enabled nor active (disabled,
  masked or absent all pass) and `iptables-services` and `ufw` (or the packages that provide them, such as
  `iptables-nft-services`) not to be installed; it
  stops, disables and masks the service and removes each package that nothing else needs,
  keeping the `nftables` package itself, then reloads `firewalld` if it is running. A package
  something else needs is kept and the control is a finding.
- Firewall, Level 2 (4.1.10, 4.1.11): 4.1.10 fails only when `LogDenied` is `off`, read with
  `firewall-cmd --get-log-denied` when `firewalld` runs and from
  `/etc/firewalld/firewalld.conf` otherwise (a missing line means `off`). It sets
  `cis_firewalld_log_denied` with `firewall-cmd --set-log-denied` when `firewalld` runs, else in
  `firewalld.conf`; any other value is kept. 4.1.11 applies to each active zone bound to an
  interface other than `lo` or `virbr*` whose target is `default`; zones with an `ACCEPT`,
  `DROP` or `REJECT` target are not applicable. For such a zone the ICMP types
  `timestamp-request` and `timestamp-reply` must be blocked in the permanent and the runtime
  configuration: listed as ICMP blocks when icmp-block-inversion is off, not listed when it
  is on. The fix adds (or, with inversion on, removes) the blocks permanently and reloads
  `firewalld` once; a runtime-only difference is fixed by the reload alone. `firewalld` not
  running is a finding with nothing to change; no applicable zone passes. Neither control
  restricts SSH, so neither uses the SSH guard. 4.1.5 to 4.1.7 and 4.1.8 (Level 2) are manual:
  the role prints the loopback interface rules, the loopback address rules, the zones'
  services and ports, and the default zone, and changes nothing. Review them as described in
  [docs/review-controls.md](docs/review-controls.md); setting the default zone to `drop`
  (4.1.8) can lock you out, so allow SSH in the zone that carries your connection first.
- SSH guard (4.1.3, 4.1.4): starting `firewalld` and replacing an `ACCEPT` target can begin
  filtering and cut the role's own SSH connection, so the role makes these two changes only
  when SSH is already allowed in the zone that applies to that connection. The role reads
  the connection from `SSH_CONNECTION`. The zone is the one whose sources match the
  controller address; else the zone of the interface that carries the server address
  (NetworkManager `connection.zone`, then the firewalld binding); else the default zone.
  SSH is allowed there when its permanent configuration has the `ssh` service and the
  connection is on port 22, or a TCP port or range containing the connection port, which
  must be one that `sshd -T` reports; rich rules are not read. For 4.1.3 a zone target of
  `ACCEPT` also counts as allowed, and enabling a `firewalld` that already runs needs no
  guard. A connection that is not SSH (for example `local`) passes. When anything cannot be
  determined (an `ipset:` or `mac:` zone source, two zones matching the controller, an
  unknown interface), the guard fails. In every failing case the host is left unchanged, a
  message says so, and the control is a finding to fix by hand: allow SSH in the zone, then
  run the role again.
- Time synchronization (2.3): 2.3.1 installs `chrony` (or removes it when
  `cis_chrony_installed` is `false` and nothing needs it; if something does, it stops and masks
  `chronyd` instead) 2.3.2 looks for a `server` or `pool`
  line in `/etc/chrony.conf` and in the files its `include`, `confdir` and `sourcedir`
  directives pull in; `sourcedir /run/chrony-dhcp` is ignored because DHCP sources exist
  only at run time. A non-empty `cis_time_sources` is enforced exactly (see its table row) and
  `chronyd` restarts only on a change and if it is running; with chrony not installed, or no
  source at all and an empty list, it is a finding and nothing is installed or guessed. 2.3.3 removes only the `-u root` option
  from the `OPTIONS` value in `/etc/sysconfig/chronyd` (restarting `chronyd` only if it is
  running); a missing file is compliant. With `cis_chronyd_run_as_root: true` it sets `-u root`
  instead, and that is a finding.
- Job schedulers (2.4): the controls apply only when `cronie` (2.4.1) or `at` (2.4.2.1) is
  installed; otherwise they pass and nothing is installed. 2.4.1.1 unmasks, enables and
  starts `crond` (or stops and disables it, per `cis_crond_enabled` and `cis_crond_active`).
  2.4.1.2 to 2.4.1.8 require `/etc/crontab` and the `/etc/cron.*` directories to be root:root
  with no group or other permissions (mode 0600 or stricter for the file, 0700 or stricter for
  the directories); the role sets exactly `cis_cron_owner`, `cis_cron_group` and
  `cis_cron_file_mode` or `cis_cron_dir_mode`, also over a stricter mode.
  A missing path is compliant and never created (RHEL 9 has no `/etc/cron.yearly`); a symlink
  or a path of the wrong type is a finding and is never changed. 2.4.1.9 and 2.4.2.1 require
  the allow file (`/etc/cron.allow`, `/etc/at.allow`) to exist, owned by root with group root
  or `crontab` (`daemon` for `at`) and mode 0640 or stricter, and the deny file, if present,
  the same; the fix creates a missing allow file empty, sets the owner, group (the configured
  group when it exists, else root) and mode of `cis_cron_allow_*` or `cis_at_allow_*` exactly,
  also over a stricter mode, and adds the users listed in `cis_cron_allow_users` or
  `cis_at_allow_users`. It never removes a user or deletes a deny file.
- SSH server (5.1): the role writes its settings to one drop-in,
  `/etc/ssh/sshd_config.d/00-cis-rhel9.conf` (mode 0600), whose name sorts before
  `50-redhat.conf` because sshd uses the first value it reads for most keywords (`MaxStartups` takes the last). Every control judges the
  effective configuration with `sshd -T` (and `sshd -T -C` for the account the role is
  connected as, so a Match block for it is seen), never one file, and writes a line only
  when the effective value is not compliant. A line is validated with `sshd -t -f` before
  it is written; after any change a handler checks the whole configuration with `sshd -t`
  and reloads (never restarts) sshd, only when it is running. A value set before the drop-in
  is read (a file that sorts earlier, or the main file above its `Include`; for `MaxStartups`,
  any file read after it) still wins: the
  control is a finding, and the role edits no file it does not own. A host without
  `openssh-server` passes. 5.1.1 to 5.1.4 set owner and mode on `sshd_config`, the `.conf`
  drop-ins, the drop-in folder (0700) and the host keys (found from `sshd -T` and a glob; a
  private key keeps the `ssh_keys` group it has); only the default drop-in folder is read, not
  one named by another `Include`. 5.1.5 to 5.1.7 are fixed through the crypto policy, the
  route of 1.6, not through `Ciphers`, `KexAlgorithms` or `MACs` lines: on RHEL 9 sshd takes
  those lists from the policy, so the role removes only the weak algorithms (CBC and arcfour
  ciphers, SHA-1 key exchange, 64-bit and MD5 MACs) and cannot leave a client with none in
  common; chacha20 and EtM are the manual 1.6.5 and 1.6.6. 5.1.9 sets `Banner /etc/issue.net`
  (1.7.3 manages the text). 5.1.11 (`DisableForwarding`, Level 1 Workstation and Level 2
  Server) turns off all forwarding, so a host used as an SSH jump host or tunnel endpoint
  lists it in `cis_exclusions`. 5.1.12 turns off GSSAPI, which Kerberos single sign-on over
  SSH needs. 5.1.21 sets `PermitRootLogin no`, except when the role is itself connected as
  root over SSH (a message says so and the control is a finding). 5.1.8 writes the lists
  in `cis_sshd_allow_users`, `cis_sshd_allow_groups`, `cis_sshd_deny_users` and
  `cis_sshd_deny_groups` only when the account the role is connected as (read with
  `id -un`, become off) is still allowed by the result, counting the effective lists for any
  list not set here; an entry it cannot evaluate (`user@host`, a negation) counts as not
  allowed. A connection that is not SSH (for example `local`) passes the guard. An empty
  list is left alone, and a line written by an earlier run stays when its variable is later
  emptied. See [docs/review-controls.md](docs/review-controls.md).
- sudo and su (5.2): the role writes its sudo `Defaults` lines (5.2.4, 5.2.5, 5.2.8 to
  5.2.11) to one file, `/etc/sudoers.d/zz-cis-rhel9` (mode 0440). sudo applies the last
  `Defaults` line it reads and reads `/etc/sudoers.d` in name order (skipping names with a dot or
  a trailing `~`), so the name sorts after the usual ones and the role's lines win over the
  files that sort before it. Each control judges every sudoers file sudo reads
  (`/etc/sudoers` and its `@include`, `#include`, `@includedir` and `#includedir` targets, in
  sudo's order), not one file, and writes a line only when the effective value is not
  compliant, so a stricter value is never loosened. Every write is validated with
  `visudo -cf` before it lands, and the whole configuration is checked with `visudo -c`
  afterwards. A non-compliant `Defaults` line that still wins (in a file that sorts after the
  role's, after the `#includedir` line of `/etc/sudoers`, or scoped to a user, host, command
  or runas list, which beats the global lines) is not edited: the control is a finding with
  the file and line. 5.2.1 installs sudo; 5.2.2 and 5.2.3 set owner, group and only the mode
  bits that are too open on the sudoers files and `/etc/sudoers.d`. 5.2.8, 5.2.9 and 5.2.11
  pass on a host with no line (the defaults are compliant). 5.2.6 (Level 2, in
  `cis_default_exclusions`) and 5.2.7 remove the `NOPASSWD:` tag, or the `!authenticate` item
  of a `Defaults` line, from files the role does not own, validating each edit with
  `visudo -cf`. **Lockout guard:** the account the role is connected as (read with become
  off) usually gets its sudo from exactly such a line. When no become password is set for
  the run (`ansible_become_password` and `ansible_become_pass` undefined or empty), a line
  that reaches that account, or might (a rule for the account, a group it is in, `ALL` or an
  alias, a line with several rules, a global `Defaults` line), is left alone, a message says
  so and the control is a finding; lines for other accounts are fixed. With a become password
  set nothing is guarded. A line that continues over several lines is not edited. 5.2.12 adds
  `auth required pam_wheel.so use_uid group=<cis_su_group>` to `/etc/pam.d/su` (in place of
  the commented line, else right after `pam_rootok`, so root can still use `su`) and creates
  the group empty when missing; a line the site already set is kept. `/etc/pam.d/su` is not
  managed by authselect. Members of the group are reported (a finding), never removed. The
  scanner is `files/sudoers_scan.py`, run with the managed node's Python. See
  [docs/review-controls.md](docs/review-controls.md).
- PAM and authselect (5.3): the role changes PAM only through authselect, never by editing
  `/etc/pam.d`. 5.3.1.1 to 5.3.1.3 check `pam`, `authselect` and `libpwquality` against the
  minimum version-release the benchmark names (1.5.1-14, 1.2.6-1, 1.4.4-8; rpm's own comparison)
  and upgrade a package with dnf only when it is missing or below that; a newer one is left
  alone and audit mode never upgrades. 5.3.2.1: on a host authselect does not manage (RHEL 9's
  default install, whose `system-auth` and `password-auth` are plain files) the role creates a
  custom profile, `cis_authselect_profile`, as a copy of `sssd` and selects it with
  `authselect select custom/<name> <features> --force --backup=<name>-pre-<time>`, enabling
  `with-faillock` (5.3.2.2), `with-pwhistory` (5.3.2.4) and `without-nullok` (5.3.3.4.1) for the
  selected controls. The `sssd` profile lets local accounts through before `pam_sss`, so sssd
  need not be configured. `--force` is needed because the files were not made by authselect;
  authselect backs up what it replaces. **To go back:** `authselect backup-list` shows the
  backups and `authselect backup-restore <name>` restores the earlier `system-auth`,
  `password-auth`, `postlogin`, `smartcard-auth`, `fingerprint-auth` and `nsswitch.conf`. A host
  already on a valid authselect profile keeps its profile (stock or the site's own) and the
  role only enables the features it needs (`authselect enable-feature`); a profile authselect
  finds not valid is selected again, the same way. **Lockout guard:** a broken PAM stack cuts
  off SSH logins and become, so before anything is selected the role renders what authselect
  would write (`authselect test`, which writes nothing) and refuses, with a message and a
  finding, when a line of `system-auth` or `password-auth` names a PAM module that is not
  installed, when `nsswitch.conf` would use a name service whose library is missing, when
  the stacks or `nsswitch.conf` in place now use a module or name service the profile would
  drop (a site's `pam_krb5`, `pam_ldap`, `pam_tally2`, `ldap`), or when authselect cannot render
  it. After a change it runs `authselect check` and `authselect current`, opens a new
  connection and runs a become task, so a stack that does not work fails the run at once.
  The settings go in the module configuration files, not on the PAM lines: `deny`,
  `unlock_time` (and for Level 2 `even_deny_root`) in `/etc/security/faillock.conf`;
  `difok`, `minlen`, `maxrepeat`, `maxsequence`, `dictcheck` and `enforce_for_root` in the
  role's own `/etc/security/pwquality.conf.d/zz-cis-rhel9.conf`; `remember` and
  `enforce_for_root` in `/etc/security/pwhistory.conf`. A setting that is already compliant,
  wherever it comes from, is never touched, so a stricter value is kept. libpwquality reads
  `pwquality.conf` and then `pwquality.conf.d/*.conf` in name order and the last value wins, so
  compliance is judged on the value in effect; a non-compliant value in a file the role does
  not own that still wins (one that sorts after `zz-cis-rhel9.conf`) is a finding with its file
  and line, and the role edits no such file. An argument on a PAM line (`deny=`, `minlen=`,
  `remember=`, `nullok`, a weak hash, a missing `use_authtok`) overrides the files and is
  judged from the active `system-auth` and `password-auth`. On the role's own profile it is
  removed or added in the templates in `/etc/authselect/custom/<name>/` and applied with
  `authselect apply-changes`; on any other profile only the features can fix it and the rest is
  a finding. The password hash is `sha512` (also accepted: `yescrypt`). 5.3.3.2.3 only
  reports the complexity settings in effect. The scanner is `files/pam_scan.py`, run with the
  managed node's Python. See [docs/review-controls.md](docs/review-controls.md).
- User accounts and environment (5.4): the scan is `files/accounts_scan.py`, run with the managed
  node's Python (read-only; the tasks make the changes). **Password aging** (5.4.1.1, 5.4.1.3,
  5.4.1.5) sets the defaults (`PASS_MAX_DAYS` and `PASS_WARN_AGE` in `login.defs`, `useradd -D -f`)
  and also the maximum, warning and inactive days of every existing account that has a password
  hash (field 2 of `/etc/shadow` starts with `$`), with `chage`. An account without a hash
  (locked, `*`, `!`, `!!`, empty) is left alone and is not a finding. Before changing an account the
  role works out whether the new value would make its password already expired or inactive today:
  a last change date of 0, no last change date (which `pam_unix` reads as day -1, so any maximum
  expires it at once), or a password older than the new maximum. Such an account is skipped, named
  in a message, and the control is a finding; the role never changes it. A stricter value already
  set is never loosened. 5.4.1.4 sets `ENCRYPT_METHOD` in `login.defs` to `SHA512` (or `YESCRYPT`
  when the `pam_unix` line already uses it); the PAM side is 5.3.3.4.3 and is not repeated.
  5.4.1.2 (manual, Level 2), 5.4.1.6 and 5.4.2.1 to 5.4.2.5 (audit-only) only report; the
  [review page](docs/review-controls.md) lists what. **Lockout guard:** 5.4.2.7 (nologin shell)
  and 5.4.2.8 (`usermod -L`) change only system accounts (UID below `UID_MIN`, or 65534), never
  root, never the benchmark's exceptions for 5.4.2.7 (halt, sync, shutdown, nfsnobody), and never
  the account the role is connected as (read with `id -un`, become off), `ansible_user`,
  `ansible_ssh_user` or the account become runs through, an account with a running process, or
  an account in `cis_account_exceptions`; each skipped account is named with the reason and the
  control is a finding. 5.4.2.6 edits only root's `.bash_profile` and `.bashrc` (a looser umask
  statement is rewritten, a file with none gets `umask 027` at its end), judged on what
  `su - root` reports and the statements in those files. **Shell environment:** 5.4.3.2 (`TMOUT`,
  readonly and exported) and 5.4.3.4 (`umask`) keep a marked block each in one role-owned file,
  `/etc/profile.d/zz-cis-rhel9.sh`. Every file the shells read (`/etc/profile`,
  `/etc/profile.d/*.sh`, `/etc/bashrc`) is judged; a weaker setting in a file the role does not
  own is a finding with its file and line and is never edited. The `TMOUT` block runs only in
  interactive shells, and `umask 027` is what `pam_umask` already gives every SSH session from
  `UMASK` (5.4.3.3), so the role's own connections and become are not affected. 5.4.3.1 (Level 2)
  removes the `nologin` lines from `/etc/shells`. See
  [docs/review-controls.md](docs/review-controls.md).
- The summary is tagged `summary` and `always`, and lists every selected audit-only and
  manual control even on a run limited by tags.

## Development

Every push and pull request runs [ansible-lint](https://ansible.readthedocs.io/projects/lint/)
(`production` profile, configured in `.ansible-lint`) and an
`ansible-playbook --syntax-check` of `tests/syntax.yml`, plus the consistency checks
`tests/check_controls.py` and `tests/check_benchmark_version.py` and the scanner tests
`tests/check_sudoers_scan.py`, `tests/check_pam_scan.py` and `tests/check_accounts_scan.py`, on Python 3.9 with Ansible 8.7
(ansible-core 2.15), the supported control node. To run the same locally:

```sh
python3.9 -m venv .venv && . .venv/bin/activate
pip install -r tests/requirements.txt
mkdir -p /tmp/roles && ln -sfn "$PWD" /tmp/roles/rhel9_cis_benchmarks
export ANSIBLE_ROLES_PATH=/tmp/roles
ansible-lint
ansible-playbook -i localhost, -e target=localhost --syntax-check tests/syntax.yml
python3 tests/check_controls.py
python3 tests/check_benchmark_version.py
python3 tests/check_sudoers_scan.py
python3 tests/check_pam_scan.py
python3 tests/check_accounts_scan.py
```

`tests/requirements.txt` pins ansible-lint 6.22.2, the newest release that installs with
ansible-core 2.15 on Python 3.9. Later releases need Python 3.10 or newer.

## Versioning

Versions are `<benchmark>_<major>.<minor>.<iterative>`. The part before the underscore is
the CIS benchmark version the role implements; the part after is the role's own version.
`3.0.0_0.0.8` is role version 0.0.8 for benchmark v3.0.0. See
[CHANGELOG.md](CHANGELOG.md).

The benchmark identity lives in three places that must agree: `cis_benchmark` (title,
version, date) in `vars/main.yml`, the header of `docs/controls.md`, and the version
prefix of the newest released CHANGELOG entry. `python3 tests/check_benchmark_version.py`
checks them and CI runs it, so changing one without the others fails the build.

## License

MIT, see [LICENSE](LICENSE). The benchmark is published by the Center for Internet
Security under its own terms and is not part of this repository.

# Control inventory

- Benchmark: CIS Red Hat Enterprise Linux 9 Benchmark
- Version: 3.0.0
- Date: 2026-08-28

Every recommendation in that benchmark, with the disposition in this project and whether it is implemented yet.
Only CIS IDs and short titles appear here. Read the benchmark itself for descriptions, audit and remediation steps.
[review-controls.md](review-controls.md) says what each implemented audit-only and manual control reports and what is left to decide.

## Dispositions

- **implement**: the role checks the control and remediates it, unless audit-only mode is on.
- **audit-only**: the role checks and reports, and never changes the host, because a safe fix depends on the site.
- **manual**: the benchmark marks it Manual. The role reports what it can for review.
- **skip**: not applied, with the reason given.

The Status column says whether the role's code exists yet. `planned`: no task file
yet. `implemented`: the control has its task file at
`tasks/section-<N>/level-<L>/<cis-id>.yml`. `tests/check_controls.py` enforces both.

## Summary

| Section | implement | audit-only | manual | skip | Total |
|---|---|---|---|---|---|
| 1 Initial Setup | 72 | 7 | 7 | 0 | 86 |
| 2 Services | 39 | 0 | 1 | 0 | 40 |
| 3 Network | 36 | 0 | 1 | 0 | 37 |
| 4 Host Based Firewall | 7 | 0 | 4 | 0 | 11 |
| 5 Access Control | 70 | 6 | 2 | 0 | 78 |
| 6 Logging and Auditing | 71 | 0 | 7 | 0 | 78 |
| 7 System Maintenance | 11 | 10 | 1 | 0 | 22 |
| **Total** | **306** | **23** | **23** | **0** | **352** |

## 1 Initial Setup

| CIS ID | Title | Profile | Type | Disposition | Status | Notes |
|---|---|---|---|---|---|---|
| 1.1.1.1 | Ensure cramfs kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.1.1.2 | Ensure freevxfs kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.1.1.3 | Ensure hfs kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.1.1.4 | Ensure hfsplus kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.1.1.5 | Ensure jffs2 kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.1.1.6 | Ensure overlay kernel module is not available | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 1.1.1.7 | Ensure squashfs kernel module is not available | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 1.1.1.8 | Ensure udf kernel module is not available | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 1.1.1.9 | Ensure firewire-core kernel module is not available | L1 Server, L2 Workstation | Automated | implement | implemented | Profile differs: L1 Server, L2 Workstation |
| 1.1.1.10 | Ensure usb-storage kernel module is not available | L1 Server, L2 Workstation | Automated | implement | implemented | Profile differs: L1 Server, L2 Workstation |
| 1.1.1.11 | Ensure unused filesystems kernel modules are not available | L1 Server, L1 Workstation | Manual | manual | implemented | Report loaded filesystem modules for review |
| 1.1.2.1.1 | Ensure /tmp is tmpfs or a separate partition | L1 Server, L1 Workstation | Automated | implement | implemented | Enable the systemd tmp.mount unit when /tmp is not already separate |
| 1.1.2.1.2 | Ensure nodev option set on /tmp partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.1.3 | Ensure nosuid option set on /tmp partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.1.4 | Ensure noexec option set on /tmp partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.2.1 | Ensure /dev/shm is tmpfs or a separate partition | L1 Server, L1 Workstation | Automated | audit-only | implemented | RHEL 9 mounts /dev/shm as tmpfs by default; report only |
| 1.1.2.2.2 | Ensure nodev option set on /dev/shm partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.2.3 | Ensure nosuid option set on /dev/shm partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.2.4 | Ensure noexec option set on /dev/shm partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.3.1 | Ensure separate partition exists for /home | L2 Server, L2 Workstation | Automated | audit-only | implemented | Partitioning is decided at install time; report only |
| 1.1.2.3.2 | Ensure nodev option set on /home partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.3.3 | Ensure nosuid option set on /home partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.4.1 | Ensure separate partition exists for /var | L2 Server, L2 Workstation | Automated | audit-only | implemented | Partitioning is decided at install time; report only |
| 1.1.2.4.2 | Ensure nodev option set on /var partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.4.3 | Ensure nosuid option set on /var partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.5.1 | Ensure separate partition exists for /var/tmp | L2 Server, L2 Workstation | Automated | audit-only | implemented | Partitioning is decided at install time; report only |
| 1.1.2.5.2 | Ensure nodev option set on /var/tmp partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.5.3 | Ensure nosuid option set on /var/tmp partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.5.4 | Ensure noexec option set on /var/tmp partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.6.1 | Ensure separate partition exists for /var/log | L2 Server, L2 Workstation | Automated | audit-only | implemented | Partitioning is decided at install time; report only |
| 1.1.2.6.2 | Ensure nodev option set on /var/log partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.6.3 | Ensure nosuid option set on /var/log partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.6.4 | Ensure noexec option set on /var/log partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.7.1 | Ensure separate partition exists for /var/log/audit | L2 Server, L2 Workstation | Automated | audit-only | implemented | Partitioning is decided at install time; report only |
| 1.1.2.7.2 | Ensure nodev option set on /var/log/audit partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.7.3 | Ensure nosuid option set on /var/log/audit partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.1.2.7.4 | Ensure noexec option set on /var/log/audit partition | L1 Server, L1 Workstation | Automated | implement | implemented | Only when the mount exists |
| 1.2.1.1 | Ensure GPG keys are configured | L1 Server, L1 Workstation | Manual | manual | implemented |  |
| 1.2.1.2 | Ensure gpgcheck is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.2.1.3 | Ensure repo_gpgcheck is configured | L2 Server, L2 Workstation | Automated | audit-only | implemented | Red Hat CDN repositories do not sign repository metadata; enabling breaks dnf |
| 1.2.1.4 | Ensure package manager repositories are configured | L1 Server, L1 Workstation | Manual | manual | implemented |  |
| 1.2.1.5 | Ensure weak dependencies are configured | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 1.2.2.1 | Ensure updates, patches, and additional security software are installed | L1 Server, L1 Workstation | Manual | manual | implemented |  |
| 1.3.1.1 | Ensure SELinux is installed | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.3.1.2 | Ensure SELinux is not disabled in bootloader configuration | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.3.1.3 | Ensure SELinux policy is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.3.1.4 | Ensure the SELinux mode is not disabled | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.3.1.5 | Ensure the SELinux mode is enforcing | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 1.3.1.6 | Ensure no unconfined services exist | L2 Server, L2 Workstation | Manual | manual | implemented |  |
| 1.3.1.7 | Ensure the MCS Translation Service (mcstrans) is not installed | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.3.1.8 | Ensure SETroubleshoot is not installed | L1 Server | Automated | implement | implemented |  |
| 1.4.1 | Ensure bootloader password is set | L1 Server, L1 Workstation | Automated | implement | implemented | Needs a site-supplied password hash; report only when unset |
| 1.4.2 | Ensure access to bootloader config is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.4.3 | Ensure authentication is required when booting into rescue mode | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 1.4.4 | Ensure authentication is required when booting into emergency mode | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 1.4.5 | Ensure systemd ability to spawn an interactive boot process is disabled | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.1 | Ensure fs.protected_hardlinks is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.2 | Ensure fs.protected_symlinks is configured | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 1.5.3 | Ensure fs.suid_dumpable is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.4 | Ensure kernel.dmesg_restrict is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.5 | Ensure kernel.kptr_restrict is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.6 | Ensure kernel.randomize_va_space is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.7 | Ensure kernel.yama.ptrace_scope is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.8 | Ensure core file size is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.9 | Ensure systemd-coredump ProcessSizeMax is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.5.10 | Ensure systemd-coredump Storage is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.6.1 | Ensure system wide crypto policy is not legacy | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.6.2 | Ensure system wide crypto policy disables sha1 hash and signature support | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.6.3 | Ensure system wide crypto policy macs are configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.6.4 | Ensure system wide crypto policy disables cbc for ssh | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 1.6.5 | Ensure system wide crypto policy disables chacha20-poly1305 for ssh | L1 Server, L1 Workstation | Manual | manual | implemented |  |
| 1.6.6 | Ensure system wide crypto policy disables EtM for ssh | L1 Server, L1 Workstation | Manual | manual | implemented |  |
| 1.6.7 | Ensure system wide crypto policy enables post-quantum algorithms | L2 Server, L2 Workstation | Automated | implement | implemented | Appends the shipped PQ module when this minor release has it; otherwise a finding |
| 1.7.1 | Ensure /etc/motd is configured | L1 Server, L1 Workstation | Automated | implement | implemented | An empty file is compliant; a symlink is a finding |
| 1.7.2 | Ensure /etc/issue is configured | L1 Server, L1 Workstation | Automated | implement | implemented | A symlink is a finding |
| 1.7.3 | Ensure /etc/issue.net is configured | L1 Server, L1 Workstation | Automated | implement | implemented | A symlink is a finding |
| 1.7.4 | Ensure access to /etc/motd is configured | L1 Server, L1 Workstation | Automated | implement | implemented | A symlink is a finding, never changed |
| 1.7.5 | Ensure access to /etc/issue is configured | L1 Server, L1 Workstation | Automated | implement | implemented | A symlink is a finding, never changed |
| 1.7.6 | Ensure access to /etc/issue.net is configured | L1 Server, L1 Workstation | Automated | implement | implemented | A symlink is a finding, never changed |
| 1.8.1 | Ensure GDM login banner is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only when GDM is installed |
| 1.8.2 | Ensure GDM disable-user-list is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only when GDM is installed |
| 1.8.3 | Ensure GDM screen lock is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only when GDM is installed |
| 1.8.4 | Ensure GDM automount is configured | L1 Server, L2 Workstation | Automated | implement | implemented | Only when GDM is installed; sets automount and automount-open |
| 1.8.5 | Ensure GDM autorun-never is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only when GDM is installed |
| 1.8.6 | Ensure XDMCP is not enabled | L1 Server, L1 Workstation | Automated | implement | implemented | Only when GDM is installed; the reboot flag is set while GDM predates custom.conf |
| 1.8.7 | Ensure Wayland is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only when GDM is installed; the reboot flag is set while GDM predates custom.conf |

## 2 Services

| CIS ID | Title | Profile | Type | Disposition | Status | Notes |
|---|---|---|---|---|---|---|
| 2.1.1 | Ensure autofs services are not in use | L1 Server, L2 Workstation | Automated | implement | implemented | Applies to 2.1.1 to 2.1.18: remove the package when nothing else needs it, otherwise stop and mask its units; `cis_services_keep` keeps a service the site needs |
| 2.1.2 | Ensure avahi daemon services are not in use | L1 Server, L2 Workstation | Automated | implement | implemented |  |
| 2.1.3 | Ensure cockpit web services are not in use | L2 Server, L2 Workstation | Automated | implement | implemented |  |
| 2.1.4 | Ensure dhcp server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.5 | Ensure dns server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.6 | Ensure dnsmasq services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.7 | Ensure samba file server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.8 | Ensure ftp server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.9 | Ensure message access server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.10 | Ensure network file system services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.11 | Ensure print server services are not in use | L1 Server | Automated | implement | implemented |  |
| 2.1.12 | Ensure rpcbind services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.13 | Ensure rsync services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.14 | Ensure snmp services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.15 | Ensure telnet server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.16 | Ensure tftp server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.17 | Ensure web proxy server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.18 | Ensure web server services are not in use | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 2.1.19 | Ensure mail transfer agents are configured for local-only mode | L1 Server, L1 Workstation | Automated | implement | implemented | Postfix is set to loopback-only; any other MTA that listens beyond loopback is a finding; `cis_services_keep` skips it |
| 2.1.20 | Ensure a graphical user interface is not in use | L2 Server | Automated | implement | implemented | Server only; excluded by default because it removes the desktop and what depends on it; sets the default target to multi-user and a pending reboot |
| 2.1.21 | Ensure X window server services are not in use | L2 Server | Automated | implement | implemented | Server only; excluded by default because it removes the desktop and what depends on it |
| 2.1.22 | Ensure Xwayland is not in use | L2 Server | Automated | implement | implemented | Server only; excluded by default because it removes the desktop and what depends on it |
| 2.1.23 | Ensure only approved services are listening on a network interface | L1 Server, L1 Workstation | Manual | manual | implemented | Report listening sockets for review |
| 2.2.1 | Ensure ftp client is not installed | L1 Server, L1 Workstation | Automated | implement | implemented | Removed when nothing else installed needs it, otherwise a finding |
| 2.2.2 | Ensure ldap client is not installed | L2 Server, L2 Workstation | Automated | implement | implemented | As for 2.2.1 |
| 2.2.3 | Ensure telnet client is not installed | L1 Server, L1 Workstation | Automated | implement | implemented | As for 2.2.1 |
| 2.2.4 | Ensure tftp client is not installed | L1 Server, L1 Workstation | Automated | implement | implemented | As for 2.2.1 |
| 2.3.1 | Ensure time synchronization is in use | L1 Server, L1 Workstation | Automated | implement | implemented | Installs chrony |
| 2.3.2 | Ensure chrony is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Adds cis_time_sources only when no source is configured; DHCP sources ignored |
| 2.3.3 | Ensure chrony is not run as the root user | L1 Server, L1 Workstation | Automated | implement | implemented | Removes only the -u root option; missing file is compliant |
| 2.4.1.1 | Ensure cron daemon is enabled and active | L1 Server, L1 Workstation | Automated | implement | implemented | Only when cronie is installed |
| 2.4.1.2 | Ensure access to /etc/crontab is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only when cronie is installed; shared logic in tasks/lib/cron_access.yml |
| 2.4.1.3 | Ensure access to /etc/cron.hourly is configured | L1 Server, L1 Workstation | Automated | implement | implemented | As for 2.4.1.2 |
| 2.4.1.4 | Ensure access to /etc/cron.daily is configured | L1 Server, L1 Workstation | Automated | implement | implemented | As for 2.4.1.2 |
| 2.4.1.5 | Ensure access to /etc/cron.weekly is configured | L1 Server, L1 Workstation | Automated | implement | implemented | As for 2.4.1.2 |
| 2.4.1.6 | Ensure access to /etc/cron.monthly is configured | L1 Server, L1 Workstation | Automated | implement | implemented | As for 2.4.1.2 |
| 2.4.1.7 | Ensure access to /etc/cron.yearly is configured | L1 Server, L1 Workstation | Automated | implement | implemented | As for 2.4.1.2 |
| 2.4.1.8 | Ensure access to /etc/cron.d is configured | L1 Server, L1 Workstation | Automated | implement | implemented | As for 2.4.1.2 |
| 2.4.1.9 | Ensure access to crontab is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only when cronie is installed; adds cis_cron_allow_users, an empty cron.allow leaves only root |
| 2.4.2.1 | Ensure access to at is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only when at is installed; adds cis_at_allow_users, an empty at.allow leaves only root |

## 3 Network

| CIS ID | Title | Profile | Type | Disposition | Status | Notes |
|---|---|---|---|---|---|---|
| 3.1.1 | Ensure IPv6 status is identified | L1 Server, L1 Workstation | Manual | manual | implemented | Report IPv6 state for review |
| 3.1.2 | Ensure wireless interfaces are not available | L1 Server | Automated | implement | implemented |  |
| 3.1.3 | Ensure bluetooth services are not in use | L1 Server, L2 Workstation | Automated | implement | implemented | Profile differs: L1 Server, L2 Workstation |
| 3.2.1 | Ensure dccp kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.2.2 | Ensure tipc kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.2.3 | Ensure rds kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.2.4 | Ensure sctp kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.2.5 | Ensure atm kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.2.6 | Ensure can kernel module is not available | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.1 | Ensure net.ipv4.ip_forward is configured | L1 Workstation, L2 Server | Automated | implement | implemented | Profile differs: L1 Workstation, L2 Server |
| 3.3.1.2 | Ensure net.ipv4.conf.all.forwarding is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.3 | Ensure net.ipv4.conf.default.forwarding is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.4 | Ensure net.ipv4.conf.all.send_redirects is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.5 | Ensure net.ipv4.conf.default.send_redirects is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.6 | Ensure net.ipv4.icmp_ignore_bogus_error_responses is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.7 | Ensure net.ipv4.icmp_echo_ignore_broadcasts is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.8 | Ensure net.ipv4.conf.all.accept_redirects is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.9 | Ensure net.ipv4.conf.default.accept_redirects is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.10 | Ensure net.ipv4.conf.all.secure_redirects is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.11 | Ensure net.ipv4.conf.default.secure_redirects is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.12 | Ensure net.ipv4.conf.all.rp_filter is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.13 | Ensure net.ipv4.conf.default.rp_filter is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.14 | Ensure net.ipv4.conf.all.accept_source_route is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.15 | Ensure net.ipv4.conf.default.accept_source_route is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.16 | Ensure net.ipv4.conf.all.log_martians is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.17 | Ensure net.ipv4.conf.default.log_martians is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.18 | Ensure net.ipv4.tcp_syncookies is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.19 | Ensure net.ipv4.conf.all.route_localnet is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.1.20 | Ensure net.ipv4.conf.default.route_localnet is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 3.3.2.1 | Ensure net.ipv6.conf.all.forwarding is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Skipped when IPv6 is disabled |
| 3.3.2.2 | Ensure net.ipv6.conf.default.forwarding is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Skipped when IPv6 is disabled |
| 3.3.2.3 | Ensure net.ipv6.conf.all.accept_redirects is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Skipped when IPv6 is disabled |
| 3.3.2.4 | Ensure net.ipv6.conf.default.accept_redirects is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Skipped when IPv6 is disabled |
| 3.3.2.5 | Ensure net.ipv6.conf.all.accept_source_route is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Skipped when IPv6 is disabled |
| 3.3.2.6 | Ensure net.ipv6.conf.default.accept_source_route is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Skipped when IPv6 is disabled |
| 3.3.2.7 | Ensure net.ipv6.conf.all.accept_ra is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Skipped when IPv6 is disabled |
| 3.3.2.8 | Ensure net.ipv6.conf.default.accept_ra is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Skipped when IPv6 is disabled |

## 4 Host Based Firewall

| CIS ID | Title | Profile | Type | Disposition | Status | Notes |
|---|---|---|---|---|---|---|
| 4.1.1 | Ensure firewalld is installed | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 4.1.2 | Ensure firewalld backend is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Only an explicit iptables backend is changed; restarts firewalld only when it is running |
| 4.1.3 | Ensure firewalld.service is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Starts firewalld only when SSH is already allowed in the zone that applies to the role's connection; shared guard in tasks/lib/firewalld_ssh_guard.yml |
| 4.1.4 | Ensure firewalld active zone target is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Changes an ACCEPT target only when SSH is already allowed in the zone that applies to the role's connection; adds cis_firewalld_zone_target |
| 4.1.5 | Ensure firewalld loopback traffic is configured | L1 Server, L1 Workstation | Manual | manual | implemented | Listed for review; the role reports it and changes nothing |
| 4.1.6 | Ensure firewalld loopback source address traffic is configured | L1 Server, L1 Workstation | Manual | manual | implemented | Listed for review; the role reports it and changes nothing |
| 4.1.7 | Ensure firewalld services and ports are configured | L1 Server, L1 Workstation | Manual | manual | implemented | Listed for review; the role reports it and changes nothing |
| 4.1.8 | Ensure firewalld default zone is set to drop | L2 Server, L2 Workstation | Manual | manual | implemented | Listed for review; lockout risk, so the role never changes it |
| 4.1.9 | Ensure conflicting firewall utilities are not in use with firewalld | L1 Server, L1 Workstation | Automated | implement | implemented | Stops and masks nftables.service; removes the packages providing iptables-services and ufw only when nothing else needs them |
| 4.1.10 | Ensure firewalld logs denied packets | L2 Server, L2 Workstation | Automated | implement | implemented | Sets LogDenied only when it is off; adds cis_firewalld_log_denied |
| 4.1.11 | Ensure firewalld blocks ICMP timestamp requests and replies | L2 Server, L2 Workstation | Automated | implement | implemented | Only zones with the default target; blocks both types permanently, then reloads firewalld |

## 5 Access Control

| CIS ID | Title | Profile | Type | Disposition | Status | Notes |
|---|---|---|---|---|---|---|
| 5.1.1 | Ensure access to /etc/ssh/sshd_config is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.2 | Ensure access to /etc/ssh/sshd_config.d/ directory is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.3 | Ensure access to SSH private host key files is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.4 | Ensure access to SSH public host key files is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.5 | Ensure sshd Ciphers are configured | L1 Server, L1 Workstation | Automated | implement | implemented | Fixed through the crypto policy (CIS-NO-SSHCBC), not a Ciphers line |
| 5.1.6 | Ensure sshd KexAlgorithms is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Fixed through the crypto policy (NO-SHA1), not a KexAlgorithms line |
| 5.1.7 | Ensure sshd MACs are configured | L1 Server, L1 Workstation | Automated | implement | implemented | Fixed through the crypto policy (CIS-NO-WEAKMAC), not a MACs line |
| 5.1.8 | Ensure sshd access is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Needs site-supplied allow or deny lists (`cis_sshd_*`); report only when unset; lockout guard on the role's own account |
| 5.1.9 | Ensure sshd Banner is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Banner is /etc/issue.net, whose text 1.7.3 manages |
| 5.1.10 | Ensure sshd ClientAliveInterval and ClientAliveCountMax are configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.11 | Ensure sshd DisableForwarding is enabled | L1 Workstation, L2 Server | Automated | implement | implemented | Profile differs: L1 Workstation, L2 Server |
| 5.1.12 | Ensure sshd GSSAPIAuthentication is disabled | L1 Workstation, L2 Server | Automated | implement | implemented | Profile differs: L1 Workstation, L2 Server |
| 5.1.13 | Ensure sshd HostbasedAuthentication is disabled | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.14 | Ensure sshd IgnoreRhosts is enabled | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.15 | Ensure sshd LoginGraceTime is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.16 | Ensure sshd LogLevel is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.17 | Ensure sshd MaxAuthTries is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.18 | Ensure sshd MaxStartups is configured | L1 Server, L1 Workstation | Automated | implement | implemented | sshd takes the last MaxStartups value, so a later file can override it (a finding) |
| 5.1.19 | Ensure sshd MaxSessions is configured | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.20 | Ensure sshd PermitEmptyPasswords is disabled | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.21 | Ensure sshd PermitRootLogin is disabled | L1 Server, L1 Workstation | Automated | implement | implemented | Lockout risk: confirm another admin login first; not changed while the role is connected as root |
| 5.1.22 | Ensure sshd PermitUserEnvironment is disabled | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.1.23 | Ensure sshd UsePAM is enabled | L1 Server, L1 Workstation | Automated | implement | implemented |  |
| 5.2.1 | Ensure sudo is installed | L1 Server, L1 Workstation | Automated | implement | implemented | |
| 5.2.2 | Ensure access on sudoers configuration files is configured | L1 Server | Automated | implement | implemented | |
| 5.2.3 | Ensure access on the /etc/sudoers.d directory is configured | L1 Server | Automated | implement | implemented | |
| 5.2.4 | Ensure sudo commands use pty | L1 Server, L1 Workstation | Automated | implement | implemented | Writes `Defaults use_pty` to the role's sudoers file; last Defaults line wins |
| 5.2.5 | Ensure sudo log file exists | L1 Server, L1 Workstation | Automated | implement | implemented | Path from `cis_sudo_logfile`; a log file the site set is kept |
| 5.2.6 | Ensure users must provide password for escalation | L2 Server, L2 Workstation | Automated | implement | implemented | Excluded by default: breaks passwordless become for Ansible; lockout guard on the role's own account |
| 5.2.7 | Ensure re-authentication for privilege escalation is not disabled globally | L1 Server, L1 Workstation | Automated | implement | implemented | Lockout guard on the role's own account |
| 5.2.8 | Ensure sudo pwfeedback is configured | L1 Server | Automated | implement | implemented | |
| 5.2.9 | Ensure sudo visiblepw is configured | L1 Server | Automated | implement | implemented | |
| 5.2.10 | Ensure sudo timestamp_timeout is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Value from `cis_sudo_timestamp_timeout`; a stricter value is kept |
| 5.2.11 | Ensure sudo timestamp_type is configured | L1 Server | Automated | implement | implemented | |
| 5.2.12 | Ensure access to the su command is restricted | L1 Server, L1 Workstation | Automated | implement | implemented | Group from `cis_su_group`; reports members, never removes them |
| 5.3.1.1 | Ensure latest version of pam is installed | L1 Server, L1 Workstation | Automated | implement | implemented | Upgraded with dnf only when below the benchmark's minimum version |
| 5.3.1.2 | Ensure latest version of authselect is installed | L1 Server, L1 Workstation | Automated | implement | implemented | Upgraded with dnf only when below the benchmark's minimum version |
| 5.3.1.3 | Ensure latest version of libpwquality is installed | L1 Server, L1 Workstation | Automated | implement | implemented | Upgraded with dnf only when below the benchmark's minimum version |
| 5.3.2.1 | Ensure PAM is managed by an active authselect profile | L1 Server, L1 Workstation | Automated | implement | implemented | Converts a host without authselect to a role-owned custom profile based on sssd (`cis_authselect_profile`), with a backup; lockout guard |
| 5.3.2.2 | Ensure pam_faillock module is enabled | L1 Server, L1 Workstation | Automated | implement | implemented | Enables the `with-faillock` feature on an authselect-managed host |
| 5.3.2.3 | Ensure pam_pwquality module is enabled | L1 Server, L1 Workstation | Automated | implement | implemented | Reports a stack without it; no feature to enable |
| 5.3.2.4 | Ensure pam_pwhistory module is enabled | L1 Server, L1 Workstation | Automated | implement | implemented | Enables the `with-pwhistory` feature on an authselect-managed host |
| 5.3.2.5 | Ensure pam_unix module is enabled | L1 Server, L1 Workstation | Automated | implement | implemented | Reports a stack without it; no feature to enable |
| 5.3.3.1.1 | Ensure password failed attempts lockout is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Value from `cis_faillock_deny` in `faillock.conf` |
| 5.3.3.1.2 | Ensure password unlock time is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Value from `cis_faillock_unlock_time` in `faillock.conf` |
| 5.3.3.1.3 | Ensure password failed attempts lockout includes root account | L2 Server, L2 Workstation | Automated | implement | implemented | Adds `even_deny_root` to `faillock.conf`; root can be locked out of password logins |
| 5.3.3.2.1 | Ensure password number of changed characters is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Value from `cis_pwquality_difok` in the role's pwquality drop-in |
| 5.3.3.2.2 | Ensure password length is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Value from `cis_pwquality_minlen` in the role's pwquality drop-in |
| 5.3.3.2.3 | Ensure password complexity is configured | L1 Server, L1 Workstation | Manual | manual | implemented | Reports `minclass` and the credit settings in effect; the role never sets them |
| 5.3.3.2.4 | Ensure password same consecutive characters is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Value from `cis_pwquality_maxrepeat` in the role's pwquality drop-in |
| 5.3.3.2.5 | Ensure password maximum sequential characters is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Value from `cis_pwquality_maxsequence` in the role's pwquality drop-in |
| 5.3.3.2.6 | Ensure password dictionary check is enabled | L1 Server, L1 Workstation | Automated | implement | implemented | Overrides a `dictcheck = 0` in the role's pwquality drop-in |
| 5.3.3.2.7 | Ensure password quality is enforced for the root user | L1 Server, L1 Workstation | Automated | implement | implemented | Adds `enforce_for_root` to the role's pwquality drop-in |
| 5.3.3.3.1 | Ensure password history remember is configured | L1 Server, L1 Workstation | Automated | implement | implemented | Value from `cis_pwhistory_remember` in `pwhistory.conf` |
| 5.3.3.3.2 | Ensure password history is enforced for the root user | L1 Server, L1 Workstation | Automated | implement | implemented | Adds `enforce_for_root` to `pwhistory.conf` |
| 5.3.3.3.3 | Ensure pam_pwhistory includes use_authtok | L1 Server, L1 Workstation | Automated | implement | implemented | Fixed in the templates of the role's own authselect profile; a finding on another profile |
| 5.3.3.4.1 | Ensure pam_unix does not include nullok | L1 Server, L1 Workstation | Automated | implement | implemented | Enables the `without-nullok` feature; a finding where a profile the role does not own hard-codes it |
| 5.3.3.4.2 | Ensure pam_unix does not include remember | L1 Server, L1 Workstation | Automated | implement | implemented | Fixed in the templates of the role's own authselect profile; a finding on another profile |
| 5.3.3.4.3 | Ensure pam_unix includes a strong password hashing algorithm | L1 Server, L1 Workstation | Automated | implement | implemented | Adds `sha512` in the templates of the role's own authselect profile; a finding on another profile |
| 5.3.3.4.4 | Ensure pam_unix includes use_authtok | L1 Server, L1 Workstation | Automated | implement | implemented | Fixed in the templates of the role's own authselect profile; a finding on another profile |
| 5.4.1.1 | Ensure password expiration is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.1.2 | Ensure minimum password days is configured | L2 Server, L2 Workstation | Manual | manual | planned |  |
| 5.4.1.3 | Ensure password expiration warning days is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.1.4 | Ensure strong password hashing algorithm is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.1.5 | Ensure inactive password lock is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.1.6 | Ensure all users last password change date is in the past | L1 Server, L1 Workstation | Automated | audit-only | planned | Future change dates need a person to decide the fix |
| 5.4.2.1 | Ensure root is the only UID 0 account | L1 Server, L1 Workstation | Automated | audit-only | planned | Never modify accounts automatically; report only |
| 5.4.2.2 | Ensure root is the only GID 0 account | L1 Server, L1 Workstation | Automated | audit-only | planned | Never modify accounts automatically; report only |
| 5.4.2.3 | Ensure group root is the only GID 0 group | L1 Server, L1 Workstation | Automated | audit-only | planned | Never modify groups automatically; report only |
| 5.4.2.4 | Ensure root account access is controlled | L1 Server, L1 Workstation | Automated | audit-only | planned | Root password versus locked root is a site decision; report only |
| 5.4.2.5 | Ensure root path integrity | L1 Server, L1 Workstation | Automated | audit-only | planned | PATH fixes depend on the site; report only |
| 5.4.2.6 | Ensure root user umask is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.2.7 | Ensure system accounts do not have a valid login shell | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.2.8 | Ensure accounts without a valid login shell are locked | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.3.1 | Ensure nologin is not listed in /etc/shells | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 5.4.3.2 | Ensure default user shell timeout is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.3.3 | Ensure default user umask is configured in /etc/login.defs | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 5.4.3.4 | Ensure default user umask is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |

## 6 Logging and Auditing

| CIS ID | Title | Profile | Type | Disposition | Status | Notes |
|---|---|---|---|---|---|---|
| 6.1.1.1 | Ensure journald service is active | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.1.2 | Ensure systemd-journal-remote is not in use | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.1.3 | Ensure journald is configured to send logs to rsyslog | L1 Server, L1 Workstation | Automated | implement | planned | Only when rsyslog is the chosen logger |
| 6.1.1.4 | Ensure journald log file rotation is configured | L1 Server, L1 Workstation | Manual | manual | planned |  |
| 6.1.1.5 | Ensure journald log file access is configured | L1 Server, L1 Workstation | Manual | manual | planned |  |
| 6.1.2.1 | Ensure rsyslog is installed | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.2.2 | Ensure rsyslog service is enabled and active | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.2.3 | Ensure rsyslog log file creation mode is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.2.4 | Ensure access to rsyslog configuration files is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.2.5 | Ensure access to the /etc/rsyslog.d directory is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.2.6 | Ensure access to the rsyslog work directory is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.2.7 | Ensure rsyslog is not configured as a log server | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.1.2.8 | Ensure rsyslog logging rules are configured | L1 Server, L1 Workstation | Manual | manual | planned |  |
| 6.1.2.9 | Ensure rsyslog is configured to send logs to a remote log host | L1 Server, L1 Workstation | Manual | manual | planned |  |
| 6.1.2.10 | Ensure a rsyslog TLS network stream driver is installed | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.1.2.11 | Ensure rsyslog network forwarding uses TLS | L2 Server, L2 Workstation | Automated | implement | planned | Only when a remote log host is configured |
| 6.1.2.12 | Ensure rsyslog TLS CA certificate is configured | L2 Server, L2 Workstation | Manual | manual | planned |  |
| 6.1.2.13 | Ensure rsyslog TLS client certificate is configured | L2 Server, L2 Workstation | Manual | manual | planned |  |
| 6.1.2.14 | Ensure logrotate is configured | L1 Server, L1 Workstation | Manual | manual | planned |  |
| 6.1.3.1 | Ensure access to all logfiles has been configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.2.1.1 | Ensure auditd packages are installed | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.1.2 | Ensure auditing for processes that start prior to auditd is enabled | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.1.3 | Ensure audit_backlog_limit is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.1.4 | Ensure auditd service is enabled and active | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.2.1 | Ensure audit log storage size is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.2.2 | Ensure audit logs are not automatically deleted | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.2.3 | Ensure system is disabled when audit logs are full | L2 Server, L2 Workstation | Automated | implement | planned | Halts the host when the audit disk fills; action is a variable |
| 6.2.2.4 | Ensure system warns when audit logs are low on space | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.1 | Ensure modification of the /etc/sudoers file is collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.2 | Ensure actions as another user are always logged | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.3 | Ensure events that modify the sudo log file are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.4 | Ensure events that modify date and time information are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.5 | Ensure events that modify sethostname and setdomainname are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.6 | Ensure events that modify /etc/issue and /etc/issue.net are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.7 | Ensure events that modify /etc/hosts and /etc/hostname are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.8 | Ensure events that modify /etc/sysconfig/network and /etc/NetworkManager/system-connections/ are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.9 | Ensure events that modify /etc/NetworkManager directory are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.10 | Ensure use of privileged commands are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.11 | Ensure unsuccessful file access attempts are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.12 | Ensure events that modify /etc/group information are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.13 | Ensure events that modify /etc/passwd information are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.14 | Ensure events that modify /etc/shadow and /etc/gshadow are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.15 | Ensure events that modify /etc/security/opasswd are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.16 | Ensure events that modify /etc/nsswitch.conf file are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.17 | Ensure events that modify /etc/pam.conf and /etc/pam.d/ information are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.18 | Ensure discretionary access control permission modification events chmod,fchmod,fchmodat are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.19 | Ensure discretionary access control permission modification events chown,fchown,lchown,fchownat are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.20 | Ensure discretionary access control permission modification events setxattr,lsetxattr,fsetxattr,removexattr,lremovexattr,fremovexattr collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.21 | Ensure successful file system mounts are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.22 | Ensure session initiation information is collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.23 | Ensure login and logout events are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.24 | Ensure unlink file deletion events by users are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.25 | Ensure rename file deletion events by users are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.26 | Ensure events that modify the system's Mandatory Access Controls are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.27 | Ensure successful and unsuccessful attempts to use the chcon command are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.28 | Ensure successful and unsuccessful attempts to use the setfacl command are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.29 | Ensure successful and unsuccessful attempts to use the chacl command are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.30 | Ensure successful and unsuccessful attempts to use the usermod command are collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.31 | Ensure kernel module loading unloading and modification is collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.32 | Ensure kernel "init_module" and "finit_module" loading unloading and modification is collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.33 | Ensure kernel "delete_module" loading unloading and modification is collected | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.34 | Ensure the audit configuration is loaded regardless of errors | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.3.35 | Ensure the audit configuration is immutable | L2 Server, L2 Workstation | Automated | implement | planned | Rule changes need a reboot afterwards |
| 6.2.3.36 | Ensure the running and on disk configuration is the same | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.1 | Ensure the audit log file directory mode is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.2 | Ensure audit log files mode is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.3 | Ensure audit log files owner is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.4 | Ensure audit log files group owner is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.5 | Ensure audit configuration files mode is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.6 | Ensure audit configuration files owner is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.7 | Ensure audit configuration files group owner is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.8 | Ensure audit tools mode is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.9 | Ensure audit tools owner is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.2.4.10 | Ensure audit tools group owner is configured | L2 Server, L2 Workstation | Automated | implement | planned |  |
| 6.3.1 | Ensure AIDE is installed | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.3.2 | Ensure filesystem integrity is regularly checked | L1 Server, L1 Workstation | Automated | implement | planned | Initial AIDE database build is slow |
| 6.3.3 | Ensure cryptographic mechanisms are used to protect the integrity of audit tools | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 6.3.4 | Ensure report_url is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |

## 7 System Maintenance

| CIS ID | Title | Profile | Type | Disposition | Status | Notes |
|---|---|---|---|---|---|---|
| 7.1.1 | Ensure access to /etc/passwd is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.2 | Ensure access to /etc/passwd- is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.3 | Ensure access to /etc/group is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.4 | Ensure access to /etc/group- is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.5 | Ensure access to /etc/shadow is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.6 | Ensure access to /etc/shadow- is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.7 | Ensure access to /etc/gshadow is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.8 | Ensure access to /etc/gshadow- is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.9 | Ensure access to /etc/shells is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.10 | Ensure access to /etc/security/opasswd is configured | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.1.11 | Ensure world writable files and directories are secured | L1 Server, L1 Workstation | Automated | audit-only | planned | Changing arbitrary files is unsafe; report only |
| 7.1.12 | Ensure no files or directories without an owner and a group exist | L1 Server, L1 Workstation | Automated | audit-only | planned | Ownership of orphaned files needs a person; report only |
| 7.1.13 | Ensure SUID and SGID files are reviewed | L1 Server, L1 Workstation | Manual | manual | planned |  |
| 7.2.1 | Ensure accounts in /etc/passwd use shadowed passwords | L1 Server, L1 Workstation | Automated | implement | planned |  |
| 7.2.2 | Ensure /etc/shadow password fields are not empty | L1 Server, L1 Workstation | Automated | audit-only | planned | Locking accounts needs a person; report only |
| 7.2.3 | Ensure all groups in /etc/passwd exist in /etc/group | L1 Server, L1 Workstation | Automated | audit-only | planned | Account database repairs need a person; report only |
| 7.2.4 | Ensure no duplicate UIDs exist | L1 Server, L1 Workstation | Automated | audit-only | planned | Account database repairs need a person; report only |
| 7.2.5 | Ensure no duplicate GIDs exist | L1 Server, L1 Workstation | Automated | audit-only | planned | Account database repairs need a person; report only |
| 7.2.6 | Ensure no duplicate user names exist | L1 Server, L1 Workstation | Automated | audit-only | planned | Account database repairs need a person; report only |
| 7.2.7 | Ensure no duplicate group names exist | L1 Server, L1 Workstation | Automated | audit-only | planned | Account database repairs need a person; report only |
| 7.2.8 | Ensure local interactive user home directories are configured | L1 Server, L1 Workstation | Automated | audit-only | planned | Home directory fixes touch user data; report only |
| 7.2.9 | Ensure local interactive user dot files access is configured | L1 Server, L1 Workstation | Automated | audit-only | planned | Dot file fixes touch user data; report only |

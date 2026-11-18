# rhel9_cis_benchmarks

Ansible role that applies the
[CIS Red Hat Enterprise Linux 9 Benchmark](https://www.cisecurity.org/benchmark/red_hat_linux)
(v3.0.0) to RHEL 9 hosts.

**Status: pre-alpha (3.0.0_0.0.18).** The role skeleton, preflight check, profile
selection, audit mode and lint CI exist, and the kernel module controls 1.1.1.1 to
1.1.1.11, the mount controls 1.1.2.1.1 to 1.1.2.7.4, the package manager controls 1.2.1.1
to 1.2.2.1 the SELinux controls 1.3.1.1 to 1.3.1.8, the boot loader controls 1.4.1 to 1.4.5 the kernel and process hardening controls 1.5.1 to 1.5.10 and the crypto policy controls 1.6.1 to 1.6.7, the banner controls 1.7.1 to 1.7.6 the GDM controls 1.8.1 to 1.8.7 and the service controls 2.1.1 to 2.1.18 are implemented; every other
control is still planned. Do not run this against hosts you care about.

## Relationship to the RHEL 7 and RHEL 8 projects

This role follows the structure and approach of
[ansible-rhel7_cis_benchmarks](https://github.com/cyvaquero/ansible-rhel7_cis_benchmarks) and
[ansible-rhel8_cis_benchmarks](https://github.com/cyvaquero/ansible-rhel8_cis_benchmarks),
which build on [ansible-role-cis-amazon-linux](https://github.com/anthcourtney/ansible-role-cis-amazon-linux)
by Anth Courtney. It is a new implementation for RHEL 9: control IDs follow the RHEL 9
benchmark, it uses current RHEL 9 tooling, and it adds Server and Workstation profiles and
an audit mode.

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
that is not true or false, or a CIS ID in `cis_exclusions` that is not in the benchmark.

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

### Boot loader password (1.4.1)

| Variable | Default | Meaning |
|---|---|---|
| `cis_grub_password_hash` | `""` | A `grub.pbkdf2.sha512...` hash from `grub2-mkpasswd-pbkdf2`. Empty: 1.4.1 only reports a missing boot loader password and changes nothing. Set: the role writes it to `/boot/grub2/user.cfg` (mode 0600). The hash is a secret: keep it in Ansible Vault. A value that is not in the hash format is a finding and is not written. |

### Banners and GDM (1.7, 1.8)

| Variable | Default | Meaning |
|---|---|---|
| `cis_banner_text` | a short notice that the computer is for approved users and use may be logged | The text 1.7.1 to 1.7.3 write to `/etc/motd`, `/etc/issue` and `/etc/issue.net`, and 1.8.1 sets as the GDM login banner, when the current content is not compliant. Keep it free of the escapes `\m`, `\r`, `\s`, `\v` and of the operating system name, or the controls cannot pass. |
| `cis_gdm_idle_delay` | `900` | 1.8.3: the longest idle time in seconds before the GDM session blanks. Any idle-delay from 1 to this value is accepted (0, never, is not); the role sets this value otherwise. |
| `cis_gdm_lock_delay` | `5` | 1.8.3: the longest delay in seconds between blanking and locking. Any lock-delay from 0 to this value is accepted; the role sets this value otherwise. |

### Services (2.1.1 to 2.1.18)

| Variable | Default | Meaning |
|---|---|---|
| `cis_services_keep` | `[]` | CIS IDs of service controls whose service the site needs, for example `["2.1.1", "2.1.10"]`. A listed control is skipped with no change and no finding. |

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
  removes `systemd.confirm_spawn` while the running kernel still has it; 1.6.1 to 1.6.4 and
  1.6.7 change the crypto policy, which a service reads only when it starts; 1.8.6 and
  1.8.7 change `/etc/gdm/custom.conf`, which a running GDM reads only when it starts) sets
  `cis_reboot_required` to `true`, reports that a reboot is pending, and the
  summary prints `Reboot required`. The variable defaults to `false` and is an output:
  read it after the role runs (for example to schedule a reboot) rather than setting it.
  Audit mode sets it too, from the state it finds.
- Mount controls (1.1.2): the `nodev`, `nosuid` and `noexec` controls act only when the
  mount exists, or for `/tmp`, will exist once `tmp.mount` is enabled. They add the option
  to `/etc/fstab` (adding a `/dev/shm` entry if there is none) or, for `/tmp` provided by
  `tmp.mount`, to a drop-in under `/etc/systemd/system/tmp.mount.d/`, and remount the live
  mount. The audit compares the live options. The separate-partition controls (1.1.2.x.1)
  only report.
- Boot loader and kernel controls (1.4, 1.5): 1.4.2 sets 0600 root:root on `grub.cfg`,
  `grubenv` and `user.cfg` (stricter modes stay) and, on UEFI hosts, makes sure the
  `/boot/efi` fstab entry has `uid=0`, `gid=0` and `umask=0077`. 1.4.3 and 1.4.4 (Level 2)
  add a drop-in to `rescue.service` or `emergency.service` only when their effective
  command no longer asks for the root password. The sysctl controls (1.5.1 to 1.5.7) write
  `/etc/sysctl.d/99-zz-cis-benchmarks.conf`, named to sort after the vendor and admin
  files, only when the configured value is not accepted, and also set the running value;
  a value that a later file still overrides is a finding. 1.5.8 writes
  `/etc/security/limits.d/99-zz-cis-benchmarks.conf` (`* hard core 0`); entries for other
  users or groups are a finding. 1.5.9 and 1.5.10 write
  `/etc/systemd/coredump.conf.d/99-zz-cis-benchmarks.conf`.
- Crypto policy controls (1.6): compliance is judged on the effective policy
  (`/etc/crypto-policies/state/CURRENT.pol`) and, for the MAC and SSH controls, on the
  generated OpenSSH back-ends. A fix changes the policy string with
  `update-crypto-policies --set`, never a generated file: it keeps the base policy and every
  module already in the string and appends the missing module (`NO-SHA1` for 1.6.2, `PQ` for
  1.6.7). 1.6.1 replaces a LEGACY base with DEFAULT. 1.6.3 and 1.6.4 write the role's own
  modules `CIS-NO-WEAKMAC` and `CIS-NO-SSHCBC` to `/etc/crypto-policies/policies/modules/`,
  only on a host that needs them. 1.6.7 (Level 2) is a finding on a minor release without
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
  `/etc/motd` is compliant. The fix writes `cis_banner_text` only to a non-compliant file,
  so a site's own compliant banner stays. 1.7.4 to 1.7.6 require root:root and no write for
  group or other and no execute bit (0644 or stricter); the fix keeps stricter modes. A
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
  1.8.4 sets `automount` and `automount-open` to false (Level 1 for Server, Level 2 for
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
  service the site needs.
- The summary is tagged `summary` and `always`, and lists every selected audit-only and
  manual control even on a run limited by tags.

## Development

Every push and pull request runs [ansible-lint](https://ansible.readthedocs.io/projects/lint/)
(`production` profile, configured in `.ansible-lint`) and an
`ansible-playbook --syntax-check` of `tests/syntax.yml`, plus the consistency checks
`tests/check_controls.py` and `tests/check_benchmark_version.py`, on Python 3.9 with Ansible 8.7
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

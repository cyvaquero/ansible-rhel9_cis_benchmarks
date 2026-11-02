# rhel9_cis_benchmarks

Ansible role that applies the
[CIS Red Hat Enterprise Linux 9 Benchmark](https://www.cisecurity.org/benchmark/red_hat_linux)
(v3.0.0) to RHEL 9 hosts.

**Status: pre-alpha (0.0.2).** The role skeleton and preflight check exist; no controls are
implemented yet. Do not run this against hosts you care about.

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
its profile and whether this role implements it, only audits it, or leaves it for manual
review. The benchmark text itself is not reproduced here; get the benchmark from
[CIS](https://www.cisecurity.org/cis-benchmarks).

## Preflight

The role first checks that the host is Red Hat Enterprise Linux 9 and fails with a clear
message otherwise. It sets `cis_rhel_minor_release` (for example `4` on RHEL 9.4) for
tasks that differ between minor releases.

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

- Level: Level 1 runs by default. Set `cis_apply_level_2: true` to add Level 2.
- Profile: `cis_profile: server` (default) or `cis_profile: workstation`.
- Exclusions: list CIS IDs in `cis_exclusions` to skip them.
- Tags: run a section, level or single control, for example `-t section-5` or
  `-t 5.1.21`.

### Audit vs remediate

- Remediate (default): each control is checked and fixed.
- Audit: `-e cis_audit_only=true` checks and reports each control without changing the
  host.

Controls marked audit-only or manual in `docs/controls.md` only report, in either mode.
Variable names are provisional until the profile-selection work lands.

## License

MIT, see [LICENSE](LICENSE). The benchmark is published by the Center for Internet
Security under its own terms and is not part of this repository.

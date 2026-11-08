# rhel9_cis_benchmarks

Ansible role that applies the
[CIS Red Hat Enterprise Linux 9 Benchmark](https://www.cisecurity.org/benchmark/red_hat_linux)
(v3.0.0) to RHEL 9 hosts.

**Status: pre-alpha (3.0.0_0.0.8).** The role skeleton, preflight check, profile
selection, audit mode and lint CI exist, and the kernel module controls 1.1.1.1 to
1.1.1.11 are implemented; every other control is still planned. Do not run this against
hosts you care about.

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
review, and its status: `implemented` (the task file exists) or `planned`. The benchmark text itself is not reproduced here; get the benchmark from
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
  passes, so it is not forgotten.
- At the end of every run a summary lists, per host, the failing CIS IDs (in
  `docs/controls.md` order) and how many are audit-only or manual controls to review.
  With `cis_fail_on_findings: true` the host then fails, which suits a CI gate:
  `-e cis_audit_only=true -e cis_fail_on_findings=true`. The audit-only and manual
  controls selected for the run always count, so expect that gate to fail until you
  exclude them in `cis_exclusions`.
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

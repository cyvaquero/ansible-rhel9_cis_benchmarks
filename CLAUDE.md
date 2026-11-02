# rhel9_cis_benchmarks

Ansible role that applies the CIS Red Hat Enterprise Linux 9 Benchmark (v3.0.0).
The global rules in `~/.claude/CLAUDE.md` apply; this file adds what is repo-specific.
Scope is the role only: test harnesses, inventories and hosts live outside this repo;
never reference any outside project, path or host. `tests/` needs no managed host.

## Target platform

- Managed nodes: RHEL 9, all minor releases; branch on `ansible_distribution_version`
  only where a control differs, with a comment. Preflight fails on anything else.
- Control node: ansible-core 2.15 (Ansible 8.7), the newest that runs on RHEL 9's default
  Python 3.9. Use no module, option, keyword or filter added after ansible-core 2.15.
- Collections: `ansible.builtin`, `ansible.posix` 1.5.4 and `community.general` 7.5.2, the
  versions bundled with Ansible 8.7. Ask before adding any other.

## Structure

- Mirror the structure and naming of the rhel8 project
  ([cyvaquero/ansible-rhel8_cis_benchmarks](https://github.com/cyvaquero/ansible-rhel8_cis_benchmarks)),
  with the role at the repo root, unless this file says otherwise. Deviations:
  - Control IDs follow the RHEL 9 numbering, not the RHEL 7 numbering rhel8 kept.
  - One file per control at `tasks/section-<N>/level-<L>/<cis-id>.yml`, included from
    `tasks/section-<N>/level-<L>.yml`; `<L>` is its lowest level in any profile (the
    exact level per profile is in `vars/controls.yml`).
  - `import_tasks` / `include_tasks`, never the removed bare `include`; fully qualified
    module names (`ansible.builtin.*`, `ansible.posix.*`, `community.general.*`).
  - No `# Standards:` headers, `templates/old/` or `ansible-review` files. Adds Server
    and Workstation profiles and an audit mode.
- Use the current RHEL 9 mechanism unless the benchmark specifies otherwise: `dnf` not
  `yum`, `ss` not `netstat`, chrony not ntpd, authselect not authconfig, firewalld not
  iptables, systemd units not xinetd, `sysctl.d` and `sshd_config.d` drop-ins,
  crypto-policies subpolicies.
- Variables use the `cis_` prefix; every default lives in `defaults/main.yml` with a
  comment naming its CIS ID. No real hostnames: use `example.com` names and RFC 5737
  addresses (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).
- `docs/controls.md` is the control inventory; change a disposition there with the code.

## Selection and modes

- Level 1 runs by default; Level 2 only when `cis_apply_level_2: true` (it includes
  Level 1). `cis_profile` is `server` (default) or `workstation`. `cis_exclusions` lists
  CIS IDs to skip; `cis_default_exclusions` (2.1.20 to 2.1.22, 5.2.6) are skipped by
  default because they can lock out or disrupt a host.
- `vars/controls.yml` maps every CIS ID to its level per profile (null: no such profile)
  and to its disposition. It must match `docs/controls.md`; change both in the same
  branch and run `python3 tests/check_controls.py` (needs PyYAML, bundled with Ansible).
- Preflight computes `cis_selected_controls` once. Every control task or include carries
  `when: "'<cis-id>' in cis_selected_controls"`; never repeat level, profile or exclusion
  logic. Level 2 task files are imported only when `cis_apply_level_2` is true.
- Two modes: remediate (default) checks and fixes; audit (`cis_audit_only: true`) checks
  and reports without changing the host. Controls with disposition audit-only or manual
  only ever report. Test booleans as `cis_audit_only | bool`: `-e` passes strings.

## Task rules

- Every task name starts with the CIS ID: `"1.1.1.1 - Disable the cramfs module"`.
- Every task carries tags: the CIS ID (`"1.1.1.1"`), its section (`section-1`), its
  level (`level-1` / `level-2`) and profiles (`server` / `workstation`).
- A second run must report `changed=0`. Control pattern (annotated example in
  `tasks/finding.yml`): a read-only check (`changed_when: false`, `check_mode: false`);
  fixes gated on `not (cis_audit_only | bool)`; in audit mode a failed check includes
  `tasks/finding.yml` with `cis_finding_id`. Audit-only and manual controls need no
  finding task: `tasks/summary.yml` lists them from `cis_control_dispositions`.

## Benchmark text

- CIS-licensed: never copy its descriptions, rationale, audit or remediation text into
  code, comments, docs, commits or issues. CIS IDs and short titles only; write our own
  task names and comments. Never commit the PDF (gitignored).

## Playbook format

Example and test playbooks target `target` (tests: `{{ target | default('localhost') }}`,
as ansible-lint needs) and use these section comments, in order, ending with `...`:

```yaml
---
# Hosts
- name: Apply the CIS RHEL 9 benchmark
  hosts: "{{ target }}"
  become: true
  gather_facts: true

# Vars
  vars:
    cis_apply_level_2: false

# Tasks
  tasks: []

# Handlers
  handlers: []

# Roles
  roles:
    - rhel9_cis_benchmarks
...
```

## Conventions

- American English. No output formats to verify; regression gates are `--check` and a
  second-run `changed=0` on RHEL 9 test hosts, under ansible-core 2.15.
- Versions are `<benchmark>_<major>.<minor>.<iterative>`, for example `3.0.0_0.0.2`: the
  CIS benchmark version, an underscore, then the role's own version under the global
  rules (hotfixes: `3.0.0_1.4.0.1`). CHANGELOG headings, the README status line, release
  branches and tags use the full string. The prefix changes only on a new benchmark
  version; the role's own number keeps counting (`3.0.0_0.9.4` → `3.1.0_0.10.0`) and never
  resets. Older benchmarks live on `support/<benchmark>` branches.
- Benchmark identity: `cis_benchmark` (title, version, date) in `vars/main.yml`, the
  `docs/controls.md` header and the CHANGELOG version prefix must agree
  (`python3 tests/check_benchmark_version.py`). Change them together, with the version.
- `CHANGELOG.md` is Keep a Changelog. Release steps: `RELEASING.md`.
- Lint: in a Python 3.9 venv, `pip install -r tests/requirements.txt`, then run
  `ansible-lint` from the repo root with `ANSIBLE_ROLES_PATH` set to a folder holding a
  `rhel9_cis_benchmarks` link to this repo. CI (`.github/workflows/lint.yml`) also runs
  `--syntax-check tests/syntax.yml` and the `tests/check_*.py` scripts. Pin actions to
  commit SHAs, tools to versions.

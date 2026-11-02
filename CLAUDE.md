# rhel9_cis_benchmarks

Ansible role that applies the CIS Red Hat Enterprise Linux 9 Benchmark (v3.0.0).
The global rules in `~/.claude/CLAUDE.md` apply; this file adds what is specific to this repo.

## Scope of this repo

- The role only: tasks, defaults, vars, handlers, templates, files, meta and role docs.
- Test harnesses, playbooks, inventories and test-host setup live outside this repo.
  Never reference any particular outside project, path or host from here.

## Target platform

- Managed nodes: RHEL 9, all minor releases. Detect the minor release from facts
  (`ansible_distribution_version`) and branch on it only where a control differs between
  minor releases; note the reason in a comment. Preflight fails on anything else.
- Control node: ansible-core 2.15 (Ansible 8.7), the newest that runs on RHEL 9's default
  Python 3.9. Use no module, option, keyword or filter added after ansible-core 2.15.
- Collections: `ansible.builtin`, `ansible.posix` and `community.general`, at the versions
  bundled with Ansible 8.7 (`ansible.posix` 1.5.4, `community.general` 7.5.2). Ask before
  adding any other.

## Structure

- Mirror the structure and naming of the rhel8 project
  ([cyvaquero/ansible-rhel8_cis_benchmarks](https://github.com/cyvaquero/ansible-rhel8_cis_benchmarks)),
  with the role at the repo root, unless this file says otherwise. Deviations:
  - Control IDs follow the RHEL 9 benchmark numbering, not the RHEL 7 numbering the rhel8
    project kept.
  - Task files are grouped by section, then level: one file per control at
    `tasks/section-<N>/level-<L>/<cis-id>.yml`, included from
    `tasks/section-<N>/level-<L>.yml`. `<L>` is the lowest level the control has in any
    profile; the exact level per profile comes from the control metadata in `vars/`.
  - `import_tasks` / `include_tasks`, never the removed bare `include`.
  - Fully qualified module names (`ansible.builtin.*`, `ansible.posix.*`,
    `community.general.*`).
  - No `# Standards:` headers, no `templates/old/`, no `ansible-review` files.
  - Server and Workstation profiles and an audit mode, which the rhel8 project lacks.
- Use the current RHEL 9 mechanism instead of a legacy one unless the benchmark specifies
  otherwise: `dnf` not `yum`, `ss` not `netstat`, chrony not ntpd, authselect not
  authconfig, firewalld not iptables, systemd units not xinetd, `sysctl.d` drop-ins,
  `sshd_config.d` drop-ins, crypto-policies subpolicies.
- Variables use the `cis_` prefix. Every default lives in `defaults/main.yml` with a
  comment naming the CIS ID it serves. No real hostnames: use `example.com` names and
  RFC 5737 addresses (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).
- `docs/controls.md` is the control inventory. Change a control's disposition there in
  the same branch as the code.

## Selection and modes

- Level 1 runs by default; Level 2 only when `cis_apply_level_2: true` (Level 2 includes
  Level 1). `cis_profile` is `server` (default) or `workstation`. `cis_exclusions` lists
  CIS IDs to skip; `cis_default_exclusions` (2.1.20 to 2.1.22, 5.2.6) holds the controls
  skipped by default because they can lock out or disrupt a host.
- `vars/controls.yml` maps every CIS ID to its level per profile (null: no such profile).
  It must match the Profile column of `docs/controls.md`; change both in the same branch.
- Preflight computes `cis_selected_controls` once. Every control task or include carries
  `when: "'<cis-id>' in cis_selected_controls"`; never repeat level, profile or exclusion
  logic in tasks. Level 2 task files are imported only when `cis_apply_level_2` is true.
- Two modes: remediate (default) checks and fixes; audit (`cis_audit_only: true`) checks
  and reports without changing the host. Controls with disposition audit-only or manual
  only ever report.

## Task rules

- Every task name starts with the CIS ID: `"1.1.1.1 - Disable the cramfs module"`.
- Every task carries tags: the CIS ID (`"1.1.1.1"`), its section (`section-1`), its
  level (`level-1` / `level-2`) and profiles (`server` / `workstation`).
- Idempotency is required: a second run must report `changed=0`. Read-only checks use
  `changed_when: false` and `check_mode: false`.

## Benchmark text

- The benchmark is CIS-licensed. Never copy its descriptions, rationale, audit or
  remediation text into code, comments, docs, commits or issues. CIS IDs and short
  titles only; write our own task names and comments.
- Never commit the benchmark PDF (`*.pdf` is gitignored).

## Playbook format

Example playbooks in the docs target hosts with the `target` extra var and use these
section comments, in this order, ending with `...`:

```yaml
---
# Hosts
- hosts: "{{ target }}"
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

- American English.
- Verified output formats: not applicable. The regression gates are
  `ansible-playbook --check` and a second-run idempotency check (`changed=0`) against
  RHEL 9 test hosts, under ansible-core 2.15.
- Versions are `<benchmark>_<major>.<minor>.<iterative>`, for example `3.0.0_0.0.2`: the
  CIS benchmark version the role implements, an underscore, then the role's own version,
  which follows the global versioning rules (hotfixes: `3.0.0_1.4.0.1`). CHANGELOG
  headings, the README status line, release branches and tags all use the full string.
  The prefix changes only when the role moves to a new benchmark version, and the role's
  own number keeps counting across that change (`3.0.0_0.9.4` → `3.1.0_0.10.0`); it never
  resets. Older benchmarks are maintained on `support/<benchmark>` branches.
- Versions: `CHANGELOG.md` (Keep a Changelog). Release steps: `RELEASING.md`.

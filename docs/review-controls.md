# Controls that need a person

Some controls the role never fixes on its own. This page lists them with what the role
reports and what is left for you to decide. Only CIS IDs and our own wording appear here;
read the benchmark for the full recommendation.

The [control inventory](controls.md) gives every control's disposition and status. This
page covers the controls that are implemented; a control joins it when its task file is
added. `tests/check_controls.py` checks that the two agree.

## Report-only controls

Audit-only and manual controls only read the host, in remediate and audit mode alike, and
never change it. Each one prints what it found. The end-of-run summary always lists every
selected audit-only and manual control under "to review", whether or not its check passes,
so with `cis_fail_on_findings: true` they always count. Leave one out with
`cis_exclusions` once you have reviewed it for that host.

| CIS ID | Disposition | What the role reports | What you decide |
|---|---|---|---|
| 1.1.1.11 | manual | The filesystem kernel modules that are loaded | Which of them the host needs; disable the rest the way 1.1.1.1 to 1.1.1.10 do |
| 1.1.2.2.1 | audit-only | Whether `/dev/shm` is a mount point | Usually nothing: RHEL 9 mounts it as tmpfs |
| 1.1.2.3.1 | audit-only | Whether `/home` is a separate mount | Whether to repartition, which means a rebuild or a storage change outside the role |
| 1.1.2.4.1 | audit-only | Whether `/var` is a separate mount | As for 1.1.2.3.1 |
| 1.1.2.5.1 | audit-only | Whether `/var/tmp` is a separate mount | As for 1.1.2.3.1 |
| 1.1.2.6.1 | audit-only | Whether `/var/log` is a separate mount | As for 1.1.2.3.1 |
| 1.1.2.7.1 | audit-only | Whether `/var/log/audit` is a separate mount | As for 1.1.2.3.1 |
| 1.2.1.1 | manual | The GPG public keys imported into the rpm database | Whether each key belongs to a source you trust; remove any that does not |
| 1.2.1.3 | audit-only | The `repo_gpgcheck` settings in `dnf.conf` and the repository files | Whether to turn it on for repositories whose metadata is signed; the Red Hat CDN's is not, so turning it on there breaks dnf |
| 1.2.1.4 | manual | The enabled package repositories | Whether each one is approved for the host |
| 1.2.2.1 | manual | How many package updates are pending, or "unknown" when dnf cannot reach its repositories | When to apply them |
| 1.3.1.6 | manual | The processes running in the `unconfined_service_t` SELinux domain; none when SELinux is off | Whether each service needs a confined policy |
| 1.6.5 | manual | Whether the SSH server crypto policy offers the chacha20-poly1305 cipher | Whether the cipher is acceptable at your site; if not, add a policy module that drops it |
| 1.6.6 | manual | How the effective crypto policy treats encrypt-then-MAC for SSH | Whether that is acceptable; if not, add a policy module for it |
| 2.1.23 | manual | The listening TCP and UDP sockets with their processes (`ss -plntu`) | Whether each listener is approved for the host; stop or remove the rest |
| 3.1.1 | manual | Whether IPv6 is disabled: the `ipv6` module parameter and the `all` and `default` `disable_ipv6` sysctls | Whether the host should use IPv6; disable it only if no service needs it |

## Excluded by default

These controls change the host when they run, so `cis_default_exclusions` skips them: they
can disrupt a host or lock Ansible out. The inventory gives each one's status. Set `cis_default_exclusions` to `[]`, or to a
shorter list, to run them; `cis_exclusions` is separate and unaffected.

| CIS ID | Why it is skipped |
|---|---|
| 2.1.20 | Removes the graphical desktop and what depends on it from a server, and sets the default target to multi-user |
| 2.1.21 | Removes the X window server and what depends on it, which includes the desktop |
| 2.1.22 | Removes Xwayland and what depends on it, which includes the desktop |
| 5.2.6 | Makes `sudo` ask for a password, which breaks passwordless become for Ansible |

## Controls that depend on the RHEL 9 minor release

Preflight records the minor release in `cis_rhel_minor_release`.

| CIS ID | What changes between releases |
|---|---|
| 1.6.7 | The role adds the `PQ` crypto policy module only when the release ships it. On a release without it there is nothing to add, so the control is a finding. |

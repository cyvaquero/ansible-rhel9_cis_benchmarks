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
| 4.1.5 | manual | The nftables rules that match the loopback interface | Whether loopback traffic is accepted and traffic to loopback addresses from other interfaces is denied, the way your policy requires |
| 4.1.6 | manual | The nftables rules that match the loopback addresses | Whether traffic from the loopback addresses is accepted only on the loopback interface and denied elsewhere |
| 4.1.7 | manual | The full configuration of each active zone, with its services, ports and rich rules | Whether each allowed service and port is needed on the host; remove the rest |
| 4.1.8 | manual | The firewalld default zone | Whether it should be `drop`. Lockout risk: `drop` blocks SSH unless SSH is allowed in the zone that carries your connection, so allow SSH there first and change the zone by hand |
| 5.3.3.2.3 | manual | The password complexity settings in effect: `minclass`, `dcredit`, `ucredit`, `lcredit` and `ocredit` from the pwquality files, and any such argument on the `pam_pwquality` lines of `system-auth` and `password-auth` | What complexity your policy needs. The role never sets these; set them in a file of `/etc/security/pwquality.conf.d`, after the role's `zz-cis-rhel9.conf` if they must win |
| 5.4.1.2 | manual | (Level 2) `PASS_MIN_DAYS` in `/etc/login.defs`, and the accounts with a password hash whose minimum age is below 1 day | Whether a minimum age fits your policy; set it in `login.defs` and with `chage --mindays` for the accounts, as the role never does |
| 5.4.1.6 | audit-only | The accounts with a password hash whose last change date is in the future | Which date is right for each; reset it (`chage -d`) or expire the password. Such a password never expires until that date |
| 5.4.2.1 | audit-only | The accounts with UID 0 | Move any account other than root to another UID, and its files with it |
| 5.4.2.2 | audit-only | The accounts with primary GID 0 other than root, sync, shutdown, halt and operator | Which group each belongs in |
| 5.4.2.3 | audit-only | The groups with GID 0 other than root | Move the group to another GID, and the files it owns with it |
| 5.4.2.4 | audit-only | What `passwd -S` says about root: password set (`P`), locked (`L`) or neither | Whether root has a password or is locked. Locking root can remove emergency login, so keep a sudo account first |
| 5.4.2.5 | audit-only | The problems of root's `PATH` as `su - root` sets it: an empty, trailing or `.` entry, and a directory that is missing, not owned by root or writable by group or other | Fix the profile file that builds the `PATH`, or create the directory. A default `PATH` lists `/root/bin` and `/root/.local/bin`, which may not exist |

## Controls with a lockout guard

These controls change who can log in over SSH, who can use sudo, the PAM stack that decides
both, or which accounts can authenticate and expire. The role changes nothing when the change would cut its own connection, and says so.

| CIS ID | What the role does | What you decide |
|---|---|---|
| 5.1.8 | Writes `cis_sshd_allow_users`, `cis_sshd_allow_groups`, `cis_sshd_deny_users` and `cis_sshd_deny_groups` to its sshd drop-in, but only when the account it is connected as (the SSH login, read with `id -un`) is still allowed by the result, counting the effective lists for any list not set. With all four empty it writes nothing and, when no such line is in effect, it is a finding | Who may log in. An allow list locks out every account not in it (or in no listed group), a deny list every account in it, so list every account that needs SSH, including the one Ansible uses, and keep a console or out-of-band way in. Entries the guard cannot evaluate (`user@host`, `!` negations) are refused. An emptied variable does not remove a line an earlier run wrote |
| 5.1.21 | Sets `PermitRootLogin no`, but not when the role is connected as root over SSH (or the account cannot be read): it prints a message and the control is a finding | Connect as a named account with sudo, then run the role again; make sure that account can log in first |
| 5.2.6, 5.2.7 | Remove the `NOPASSWD:` tag (5.2.6, Level 2) or the `!authenticate` item (5.2.7) from sudoers lines in files it does not own, each edit validated with `visudo -cf`. When no become password is set for the run (`ansible_become_password` and `ansible_become_pass` undefined or empty), it leaves alone every line that reaches the account it is connected as (read with `id -un`, become off), or might: a rule for that account, a group it is in, `ALL` or an alias, a line with several rules, a global or host, command or runas scoped `Defaults` line. It prints the file and line and the control is a finding. Lines for other accounts are fixed | Whether Ansible should keep passwordless sudo. Either set a become password for the run (`ansible_become_password`, kept in Ansible Vault) so the role may remove the tag, or leave those lines and accept the finding, or list the control in `cis_exclusions`. A line that continues over several lines, or a file that does not pass `visudo -cf` on its own (it uses an alias another file defines), is left alone and reported |
| 5.3.2.1 | Moves a host that authselect does not manage to a custom authselect profile of its own (`cis_authselect_profile`, based on `sssd`) with `authselect select custom/<name> <features> --force --backup=<name>-pre-<time>`, enabling `with-faillock`, `with-pwhistory` and `without-nullok` as the selected controls need. Before anything is selected it renders what authselect would write (`authselect test`, which writes nothing) and refuses, with a message and a finding, when a line of `system-auth` or `password-auth` names a PAM module that is not installed, when `nsswitch.conf` would use a name service whose library is not installed, when the stacks or `nsswitch.conf` now in place use a module or name service the profile would drop (a site's `pam_krb5`, `pam_ldap`, `pam_tally2`, `ldap`), or when authselect cannot render it. Optional lines (a leading `-`) are not counted. A host already on a valid authselect profile keeps it; a profile `authselect check` finds not valid is selected again, behind the same guard. After a change it runs `authselect check` and `authselect current`, opens a new connection and runs a become task, so a stack that does not work fails the run | Whether the host may move to authselect. Authselect replaces `system-auth`, `password-auth`, `postlogin`, `smartcard-auth`, `fingerprint-auth` and `nsswitch.conf`, so local edits to them are lost (the backup keeps them: `authselect backup-list`, `authselect backup-restore <name>`). A host whose stack carries a site module the guard names must put that module into an authselect profile you maintain, or list 5.3.2.1 and the other controls of 5.3 in `cis_exclusions`. Keep a console or out-of-band way in |
| 5.3.2.2 to 5.3.3.4.4 | Change PAM only through authselect: a feature (`with-faillock`, `with-pwhistory`, `without-nullok`) on the active profile, or the templates in `/etc/authselect/custom/<name>/` of the role's own profile followed by `authselect apply-changes`, never `/etc/pam.d`. Each change runs the same checks as 5.3.2.1 afterwards. On a profile the role does not own, what a feature cannot fix (a `deny=` or `minlen=` argument, a missing `use_authtok`, a weak hash) is a finding, as is a value that a pwquality file sorting after `zz-cis-rhel9.conf` or a line in another file still overrides, with its file and line | Whether to bring the profile under the role (select `custom/<cis_authselect_profile>`) or fix the lines in your own profile |
| 5.3.3.1.3 | (Level 2) Adds `even_deny_root` to `/etc/security/faillock.conf`, so root is locked after `deny` failed password logins for `unlock_time`; it replaces a `root_unlock_time` below 60. Lockout risk: root can lock itself out of password logins | Keep a console, or a sudo account with an SSH key, that does not depend on root's password. Set a finite `cis_faillock_root_unlock_time` |
| 5.4.1.1, 5.4.1.3, 5.4.1.5 | Set the defaults (`login.defs`, `useradd -D -f`) and also the maximum, warning and inactive days of each existing account that has a password hash (field 2 of `/etc/shadow` starts with `$`), with `chage`. Accounts without a hash are left alone and are not findings. Before changing an account the role works out whether the new value would make its password already expired or inactive today (a last change date of 0, no last change date, or a password older than the new maximum): such an account is skipped, named in a message, and the control is a finding. A stricter value already set is kept. The account the role is connected as falls under the same rule | Fix a skipped account's password by hand (set a new one, or `chage -d`), then run again. Lower values are never raised by the role |
| 5.4.2.6 | Edits only root's own `/root/.bash_profile` and `/root/.bashrc`: a statement looser than 027 is rewritten, a file with no umask statement gets one at its end. It judges the umask root's login shell reports (`su - root`) and the statements in those files. A looser setting in `/etc/profile`, `/etc/profile.d` or `/etc/bashrc` is not edited (5.4.3.4 reports it) | Whether root's login umask should be that strict. Files you maintain that set a looser umask for root need their own fix |
| 5.4.2.7, 5.4.2.8 | Give a nologin shell (5.4.2.7) and lock (5.4.2.8, `usermod -L`) system accounts only (UID below `UID_MIN` of `login.defs`, or 65534), never root and never the benchmark's exceptions for 5.4.2.7 (halt, sync, shutdown, nfsnobody). Left alone, with a message naming the account and the reason, and a finding: the account the role is connected as (read with `id -un`, become off), `ansible_user`, `ansible_ssh_user` and the account become runs through; an account with a running process; the accounts in `cis_account_exceptions`. An unlocked account that is not a system account and has no valid shell is reported and left alone | Which service accounts may log in, and so go in `cis_account_exceptions`. Keep a console or out-of-band way in. The role never touches the account it connects with, even when its UID is below `UID_MIN` |
| 5.4.3.2, 5.4.3.4 | Keep one role-owned file, `/etc/profile.d/zz-cis-rhel9.sh`: `TMOUT` (readonly, exported, in an interactive-shell test) and `umask`. Every file the shells read is judged; a weaker or non-readonly `TMOUT`, a `TMOUT` set twice, or a looser umask in a file the role does not own is reported with its file and line, left alone, and a finding. The role's own SSH connection and become are not interactive shells: `TMOUT` does not apply to them (the block is guarded), and the umask 027 they already get from `UMASK` through `pam_umask` (5.4.3.3) is not changed by the file | Whether sessions that rely on a looser umask (shared directories, deployment accounts) can live with 027. Set `cis_umask` to a stricter value, never a looser one |

5.2.12 closes `su` to everyone but the members of `cis_su_group` (empty by default), so use
sudo. A group that already has members is reported, and the role never removes them. The
`Defaults` controls of 5.2 (5.2.4, 5.2.5, 5.2.8 to 5.2.11) never edit a file they do not own: a
conflicting line that would still win is a finding with its file and line.

Other 5.1 controls can break a site's own use without locking Ansible out: 5.1.11 turns off
all forwarding (jump hosts, tunnels, X11), 5.1.12 turns off GSSAPI (Kerberos single sign-on),
and 5.1.17 to 5.1.19 lower the connection limits that busy automation or many parallel
sessions may reach. Raise the matching `cis_sshd_*` value within the benchmark's limit, or
list the ID in `cis_exclusions`, when a site needs it. 5.1.1 to 5.1.4 read only the default
`/etc/ssh/sshd_config.d` folder; a folder named by another `Include` is for you to check.

## Excluded by default

These controls change the host when they run, so `cis_default_exclusions` skips them: they
can disrupt a host or lock Ansible out. The inventory gives each one's status. Set `cis_default_exclusions` to `[]`, or to a
shorter list, to run them; `cis_exclusions` is separate and unaffected.

| CIS ID | Why it is skipped |
|---|---|
| 2.1.20 | Removes the graphical desktop and what depends on it from a server, and sets the default target to multi-user |
| 2.1.21 | Removes the X window server and what depends on it, which includes the desktop |
| 2.1.22 | Removes Xwayland and what depends on it, which includes the desktop |
| 5.2.6 | Removes the `NOPASSWD:` tag from sudoers rules, which breaks passwordless become for Ansible (see the lockout guard above) |

## Controls that depend on the RHEL 9 minor release

Preflight records the minor release in `cis_rhel_minor_release`.

| CIS ID | What changes between releases |
|---|---|
| 1.6.7 | The role adds the `PQ` crypto policy module only when the release ships it. On a release without it there is nothing to add, so the control is a finding. |

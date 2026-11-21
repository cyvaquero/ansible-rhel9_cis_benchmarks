#!/usr/bin/env python3
"""Checks files/accounts_scan.py against sample account and shell trees. Needs no managed host."""
import importlib.util
import os
import stat
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("accounts_scan", os.path.join(HERE, "..", "files", "accounts_scan.py"))
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

failures = []


def check(name, got, want):
    if got != want:
        failures.append("%s: got %r, want %r" % (name, got, want))


TODAY = 20000

# The accounts of a clean guest, as the role finds them: no account has a password hash.
PASSWD = """root:x:0:0:root:/root:/bin/bash
bin:x:1:1:bin:/bin:/usr/sbin/nologin
daemon:x:2:2:daemon:/sbin:/usr/sbin/nologin
sync:x:5:0:sync:/sbin:/bin/sync
shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown
halt:x:7:0:halt:/sbin:/sbin/halt
svc:x:300:300:svc:/var/svc:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/:/sbin/nologin
ansible:x:1000:1000:ansible:/home/ansible:/bin/bash
"""
SHADOW = """root:!::0:99999:7:::
bin:*:19000:0:99999:7:::
daemon:*:19000:0:99999:7:::
sync:*:19000:0:99999:7:::
shutdown:*:19000:0:99999:7:::
halt:*:19000:0:99999:7:::
svc:!!:19000:0:99999:7:::
nobody:*:19000:0:99999:7:::
ansible:!::0:99999:7:::
"""
GROUP = "root:x:0:\nbin:x:1:\nwheel:x:10:ansible\n"
LOGIN_DEFS = """# comment
MAIL_DIR /var/spool/mail
PASS_MAX_DAYS 99999
PASS_MIN_DAYS 0
PASS_WARN_AGE 7
UID_MIN 1000
UMASK 022
ENCRYPT_METHOD SHA512
"""
SHELLS = "/bin/sh\n/bin/bash\n/usr/bin/sh\n/usr/bin/bash\n"
BASHRC = """# /etc/bashrc
if ! shopt -q login_shell ; then
    # Set default umask for non-login shell only if it is set to 0
    [ `umask` -eq 0 ] && umask 022
fi
"""
PARAMS = {"max_days": 365, "warn_age": 7, "inactive_days": 45, "tmout": 900, "today": TODAY,
          "guard": ["ansible"], "exceptions": [], "lock": True,
          "owned_profile": "/etc/profile.d/zz-cis-rhel9.sh", "effective_umask": "", "root_path": ""}


def tree(files):
    root = tempfile.mkdtemp()
    base = {"/etc/passwd": PASSWD, "/etc/shadow": SHADOW, "/etc/group": GROUP, "/etc/login.defs": LOGIN_DEFS,
            "/etc/shells": SHELLS, "/etc/bashrc": BASHRC, "/etc/profile": "# profile\n",
            "/etc/default/useradd": "GROUP=100\nINACTIVE=-1\n"}
    base.update(files)
    for path, text in base.items():
        if text is None:
            continue
        full = root + path
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)
    return root


def run(files, params=None, busy=(), locked=None):
    scan.ROOT = tree(files)
    scan.running_uids = lambda: set(busy)
    # passwd -S: accounts whose field starts with ! or * are L, as on RHEL.
    scan.passwd_status = lambda name: ("L" if (locked is None or name in locked) else "P")
    merged = dict(PARAMS)
    merged.update(params or {})
    return scan.state(merged)


# ---- clean guest: nothing to fix, nothing to report
s = run({})
check("clean aging max", s["aging"]["max"], {"fix": [], "skip": []})
check("clean aging warn", s["aging"]["warn"], {"fix": [], "skip": []})
check("clean aging inactive", s["aging"]["inactive"], {"fix": [], "skip": []})
check("clean sysshell", s["sysshell"], {"fix": [], "skip": []})

# ---- system accounts with a login shell, guard, process, exception
BASH_SVC = {"/etc/passwd": PASSWD.replace("svc:/usr/sbin/nologin", "svc:/bin/bash")}
s = run(BASH_SVC, busy=[300])
check("busy account skipped", s["sysshell"]["skip"],
      [{"user": "svc", "shell": "/bin/bash", "reason": "it has a running process"}])
check("busy account not fixed", s["sysshell"]["fix"], [])
s = run(BASH_SVC, params={"exceptions": ["svc"]})
check("exception skipped", [x["reason"] for x in s["sysshell"]["skip"]], ["listed in cis_account_exceptions"])
s = run(BASH_SVC, params={"guard": ["svc"]})
check("guard skipped", [x["reason"] for x in s["sysshell"]["skip"]],
      ["the role is connected as this account or becomes it"])
s = run(BASH_SVC)
check("fix names the shell account", s["sysshell"]["fix"], [{"user": "svc", "shell": "/bin/bash"}])
check("root and the connecting account are not in scope",
      [x["user"] for x in s["sysshell"]["fix"] + s["sysshell"]["skip"]], ["svc"])

# ---- locking: only accounts without a valid shell that are not locked
s = run({}, locked=["bin", "daemon", "nobody", "svc", "ansible"])
check("unlocked sync, shutdown, halt are fixed", sorted(x["user"] for x in s["lock"]["fix"]),
      ["halt", "shutdown", "sync"])
s = run({}, locked=["bin", "daemon", "nobody", "svc", "ansible"], busy=[5])
check("locking skips a busy account", [x["user"] for x in s["lock"]["skip"]], ["sync"])
s = run({"/etc/passwd": PASSWD + "joe:x:1500:1500:joe:/home/joe:/sbin/nologin\n",
         "/etc/shadow": SHADOW + "joe:$6$x$y:19000:0:99999:7:::\n"},
        locked=["bin", "daemon", "nobody", "svc", "ansible", "sync", "shutdown", "halt"])
check("non-system account is reported, not fixed", s["lock"]["other"],
      [{"user": "joe", "reason": "not a system account (UID 1500)"}])
check("non-system account not in fix", s["lock"]["fix"], [])
s = run({}, params={"lock": False})
check("no lock query", s["lock"], {"fix": [], "skip": [], "other": []})

# ---- password aging
HASHED = SHADOW + "".join([
    "alice:$6$s$h:%d:0:99999:7:::\n" % (TODAY - 100),     # fine age, max loose -> fix max and inactive
    "bob:$6$s$h:%d:0:60:5:10::\n" % (TODAY - 10),          # max stricter kept, warn low, inactive 10 ok
    "carl:$6$s$h:%d:0:99999:7:::\n" % (TODAY - 400),       # too old: a max of 365 expires it
    "dina:$6$s$h:0:0:99999:7:::\n",                         # must change at next login
    "eve:$6$s$h::0:99999:7:::\n",                           # no last change date
    "fred:!:%d:0:99999:7:::\n" % (TODAY - 400),            # locked: left alone
    "gus:$6$s$h:%d:1:365:7:45::\n" % (TODAY - 10),          # compliant
    "hank:$6$s$h:%d:0:60:7:::\n" % (TODAY - 70),            # stricter max, already expired: no inactive period
])
PW = PASSWD + "".join("%s:x:%d:%d::/home/%s:/bin/bash\n" % (n, 1100 + i, 1100 + i, n)
                      for i, n in enumerate(["alice", "bob", "carl", "dina", "eve", "fred", "gus", "hank"]))
s = run({"/etc/shadow": HASHED, "/etc/passwd": PW})
check("max fix", [x["user"] for x in s["aging"]["max"]["fix"]], ["alice"])
check("max skip", sorted(x["user"] for x in s["aging"]["max"]["skip"]), ["carl", "dina", "eve"])
check("max skip reasons mention the cause",
      all(x["reason"] for x in s["aging"]["max"]["skip"]), True)
check("max value", s["aging"]["max"]["fix"][0]["value"], 365)
check("warn fix", [x["user"] for x in s["aging"]["warn"]["fix"]], ["bob"])
check("warn skip", s["aging"]["warn"]["skip"], [])
# carl and eve keep their unlimited maximum (a 365 maximum would expire them), and an
# inactivity period after no expiry changes nothing, so it is set; dina must change at login.
check("inactive fix", sorted(x["user"] for x in s["aging"]["inactive"]["fix"]), ["alice", "carl", "eve"])
check("inactive skip", sorted(x["user"] for x in s["aging"]["inactive"]["skip"]), ["dina", "hank"])
check("locked account untouched", [u for k in ("max", "warn", "inactive") for u in
                                    [x["user"] for x in s["aging"][k]["fix"] + s["aging"][k]["skip"]]
                                    if u == "fred"], [])
check("min below", sorted(s["min_below"]), ["alice", "bob", "carl", "dina", "eve", "hank"])
s = run({"/etc/shadow": HASHED.replace("gus:$6$s$h:%d" % (TODAY - 10), "gus:$6$s$h:%d" % (TODAY + 30)),
         "/etc/passwd": PW})
check("future change date", s["future"], ["gus"])

# the status function: the rules the plan rests on
check("state ok", scan.password_state(TODAY - 10, 365, 45, TODAY), "ok")
check("state expired", scan.password_state(TODAY - 365, 365, 45, TODAY), "expired")
check("state inactive", scan.password_state(TODAY - 410, 365, 45, TODAY), "inactive")
check("state zero", scan.password_state(0, 365, 45, TODAY), "must-change")
check("state empty with max", scan.password_state(None, 365, None, TODAY), "expired")
check("state empty unlimited", scan.password_state(None, 99999, None, TODAY), "ok")
check("state unlimited", scan.password_state(TODAY - 9000, 99999, 45, TODAY), "ok")

# ---- login.defs and useradd defaults
s = run({"/etc/login.defs": LOGIN_DEFS.replace("99999\nPASS_MIN", "90\nPASS_MIN").replace("UMASK 022", "UMASK 0027")
         .replace("SHA512", "MD5"), "/etc/default/useradd": "INACTIVE=30\n"})
check("stricter max ok", s["defaults"]["max"], {"value": "90", "ok": True})
check("umask 0027 ok", s["defaults"]["umask"]["ok"], True)
check("md5 not ok", s["defaults"]["encrypt"]["ok"], False)
check("inactive 30 ok", s["defaults"]["inactive"], {"value": 30, "ok": True})
s = run({"/etc/pam.d/system-auth": "password sufficient pam_unix.so yescrypt shadow use_authtok\n",
         "/etc/login.defs": LOGIN_DEFS.replace("SHA512", "DES")})
check("hash follows pam yescrypt", s["defaults"]["encrypt"]["want"], "YESCRYPT")
s = run({"/etc/login.defs": LOGIN_DEFS + "PASS_MAX_DAYS 90\nENCRYPT_METHOD yescrypt\n"})
check("last line wins", (s["defaults"]["max"]["value"], s["defaults"]["encrypt"]["ok"]), ("90", True))

# ---- root and group checks
s = run({"/etc/passwd": PASSWD + "toor:x:0:0::/:/bin/sh\nops:x:1200:0::/home/ops:/bin/bash\n",
         "/etc/group": GROUP + "wheel2:x:0:\n"})
check("second uid 0", s["uid0"], ["root", "toor"])
check("gid 0 accounts", s["gid0_accounts"], ["toor", "ops"])
check("gid 0 groups", s["gid0_groups"], ["wheel2"])

# ---- /etc/shells
s = run({"/etc/shells": SHELLS + "/sbin/nologin\n/usr/sbin/nologin\n# /sbin/nologin\n"})
check("nologin lines", [x["text"] for x in s["nologin_lines"]], ["/sbin/nologin", "/usr/sbin/nologin"])

# ---- TMOUT
OWN = "/etc/profile.d/zz-cis-rhel9.sh"
s = run({"/etc/profile.d/a.sh": "TMOUT=600\nreadonly TMOUT\nexport TMOUT\n"})
check("tmout compliant elsewhere", (s["tmout"]["state"], s["tmout"]["need_block"]), ("ok", False))
s = run({"/etc/profile.d/a.sh": "typeset -xr TMOUT=900\n"})
check("tmout typeset form", s["tmout"]["state"], "ok")
s = run({"/etc/profile.d/a.sh": "TMOUT=1800\n"})
check("tmout bad elsewhere is external", [p["message"] for p in s["tmout"]["external_problems"]],
      ["TMOUT=1800 is not between 1 and 900", "TMOUT is not marked readonly", "TMOUT is not exported"])
check("tmout bad elsewhere no block", s["tmout"]["need_block"], False)
s = run({OWN: "TMOUT=1800\nreadonly TMOUT\nexport TMOUT\n"})
check("tmout own bad needs the block", (s["tmout"]["state"], s["tmout"]["need_block"],
                                         s["tmout"]["external_problems"]), ("bad", True, []))
s = run({OWN: "if [ -n \"$PS1\" ]; then\n  typeset -xr TMOUT=900\nfi\n"})
check("tmout own guarded form", (s["tmout"]["state"], s["tmout"]["need_block"]), ("ok", False))
s = run({OWN: "typeset -xr TMOUT=900\n", "/etc/profile.d/a.sh": "typeset -xr TMOUT=900\n"})
check("tmout set twice", (s["tmout"]["state"], s["tmout"]["need_block"]), ("bad", False))
s = run({"/etc/profile.d/a.sh": "# TMOUT=900\nTMOUT=$X\n"})
check("tmout comment and variable ignored", (s["tmout"]["state"], s["tmout"]["assigned"]), ("bad", []))

# ---- umask in the shell files
check("benchmark conditional default is not a setting", s["umask"]["problems"], [])
s = run({"/etc/profile.d/a.sh": "umask 022\n"})
check("umask 022 is a problem", [(p["file"], p["line"]) for p in s["umask"]["problems"]],
      [("/etc/profile.d/a.sh", 1)])
check("umask need block", s["umask"]["need_block"], True)
s = run({"/etc/profile.d/a.sh": "umask 027\n  umask 0077\nif x; then umask u=rwx,g=rx,o=\nfi\n"})
check("umask 027, 0077 and symbolic are fine", s["umask"]["problems"], [])
s = run({"/etc/profile.d/a.sh": "umask u=rwx,g=rwx,o=rx\n",
         "/etc/profile": "if [ $UID -gt 199 ]; then\n    umask 002\nelse\n    umask 022\nfi\n"})
check("symbolic and branches", sorted((p["file"], p["line"]) for p in s["umask"]["problems"]),
      [("/etc/profile", 2), ("/etc/profile", 4), ("/etc/profile.d/a.sh", 1)])
s = run({"/etc/profile.d/a.sh": "umask $X\numask +w\numask -S\numask 0027 # tighten\n"})
check("unevaluable is a problem, flags and comments are not", [p["line"] for p in s["umask"]["problems"]], [1, 2])
s = run({OWN: "umask 027\n"})
check("own umask", (s["umask"]["state"], s["umask"]["own_ok"], s["umask"]["need_block"]), ("ok", True, False))
check("symbolic value", (scan.umask_value("u=rwx,g=rx,o="), scan.umask_value("0022"), scan.umask_value("a+r")),
      (0o027, 0o022, None))

# ---- root's umask
s = run({"/root/.bash_profile": "# x\n", "/root/.bashrc": "umask 022\n"}, params={"effective_umask": "0022"})
r = s["root_umask"]
check("root umask bad", r["state"], "bad")
check("root replace", [(x["path"], x["new"]) for x in r["replace"]], [("/root/.bashrc", "umask 027")])
check("root append", r["append"], [{"path": "/root/.bash_profile", "exists": True}])
s = run({"/root/.bash_profile": "umask 027\n", "/root/.bashrc": "umask 027\n"}, params={"effective_umask": "0027"})
check("root umask ok", (s["root_umask"]["state"], s["root_umask"]["replace"], s["root_umask"]["append"]),
      ("ok", [], []))
s = run({"/root/.bash_profile": "umask 027\n", "/root/.bashrc": "umask 027\n"}, params={"effective_umask": "0022"})
check("root effective bad, files fine: unfixable", (s["root_umask"]["state"], s["root_umask"]["unfixable"]),
      ("bad", True))
s = run({"/root/.bash_profile": "umask 077\n", "/root/.bashrc": "umask 027\n"})
check("root unknown effective, files compliant", s["root_umask"]["state"], "ok")
s = run({"/root/.bash_profile": "# x\n"})
check("root unknown effective, one file missing: append to both", s["root_umask"]["append"],
      [{"path": "/root/.bash_profile", "exists": True}, {"path": "/root/.bashrc", "exists": False}])
s = run({"/root/.bash_profile": "if true; then umask 002; fi # c\n"}, params={"effective_umask": "0002"})
check("root replace keeps the rest of the line", [x["new"] for x in s["root_umask"]["replace"]],
      ["if true; then umask 027; fi # c"])

# ---- root's PATH
d = tempfile.mkdtemp()
os.chmod(d, 0o755)
loose = tempfile.mkdtemp()
os.chmod(loose, 0o777)
scan.ROOT = ""
fake = type("S", (), {})


def fake_stat(path):
    real = os.stat(path)
    out = fake()
    out.st_mode, out.st_uid = real.st_mode, 0
    return out


check("good path", scan.path_problems(d, fake_stat), [])
check("empty entry", scan.path_problems(d + "::" + d, fake_stat), ["PATH contains an empty entry"])
check("trailing colon", scan.path_problems(d + ":", fake_stat), ["PATH ends with a colon"])
check("dot entry", "PATH contains the current directory (.)" in scan.path_problems(".:" + d, fake_stat), True)
check("missing directory", scan.path_problems(d + "/nope", fake_stat), [d + "/nope is not an existing directory"])
check("writable directory", scan.path_problems(loose, fake_stat),
      ["%s is writable by group or other (mode %04o)" % (loose, stat.S_IMODE(os.stat(loose).st_mode))])
check("not owned by root", scan.path_problems(d), [d + " is not owned by root"] if os.getuid() != 0 else [])

if failures:
    print("\n".join(failures))
    print("%d failure(s)" % len(failures))
    sys.exit(1)
print("accounts_scan: all checks passed")

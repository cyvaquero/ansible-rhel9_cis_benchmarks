#!/usr/bin/env python3
"""Checks files/pam_scan.py against sample PAM trees and a stand-in authselect. Needs no managed host."""
import importlib.util
import os
import stat
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("pam_scan", os.path.join(HERE, "..", "files", "pam_scan.py"))
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

failures = []


def check(name, got, want):
    if got != want:
        failures.append("%s: got %r, want %r" % (name, got, want))


# A stock, non-authselect stack, as a fresh RHEL 9 install has it.
PLAIN = """auth        required                                     pam_env.so
auth        sufficient                                   pam_unix.so try_first_pass nullok
auth        required                                     pam_deny.so
account     required                                     pam_unix.so
password    requisite                                    pam_pwquality.so try_first_pass local_users_only retry=3 authtok_type=
password    sufficient                                   pam_unix.so try_first_pass use_authtok nullok sha512 shadow
password    required                                     pam_deny.so
session     optional                                     pam_keyinit.so revoke
session     required                                     pam_limits.so
session     required                                     pam_unix.so
"""

# What the role's profile renders with its features on.
GOOD = """auth        required                                     pam_env.so
auth        required                                     pam_faillock.so preauth silent
auth        sufficient                                   pam_unix.so try_first_pass
auth        required                                     pam_faillock.so authfail
auth        required                                     pam_deny.so
account     required                                     pam_faillock.so
account     required                                     pam_unix.so
password    requisite                                    pam_pwquality.so try_first_pass local_users_only retry=3
password    requisite                                    pam_pwhistory.so use_authtok
password    sufficient                                   pam_unix.so sha512 shadow use_authtok
password    required                                     pam_deny.so
session     optional                                     pam_keyinit.so revoke
session     required                                     pam_limits.so
session     required                                     pam_unix.so
"""

CONF_GOOD = {
    "faillock.conf": "# comment\ndeny = 5\nunlock_time = 900\neven_deny_root\n",
    "pwhistory.conf": "remember = 24\nenforce_for_root\n",
}
PWQ_GOOD = "difok = 2\nminlen = 14\nmaxrepeat = 3\nmaxsequence = 3\ndictcheck = 1\nenforce_for_root\n"


def tree(system_auth, password_auth=None, faillock="", pwhistory="", pwq_main="", pwq_d=None):
    root = tempfile.mkdtemp()
    pam = os.path.join(root, "pam.d")
    sec = os.path.join(root, "security")
    os.makedirs(pam)
    os.makedirs(os.path.join(sec, "pwquality.conf.d"))
    for name, text in (("system-auth", system_auth), ("password-auth", password_auth or system_auth)):
        if text is not None:
            with open(os.path.join(pam, name), "w") as fh:
                fh.write(text)
    for name, text in (("faillock.conf", faillock), ("pwhistory.conf", pwhistory), ("pwquality.conf", pwq_main)):
        with open(os.path.join(sec, name), "w") as fh:
            fh.write(text)
    for name, text in (pwq_d or {}).items():
        with open(os.path.join(sec, "pwquality.conf.d", name), "w") as fh:
            fh.write(text)
    scan.PAM_DIR = pam
    scan.FAILLOCK_CONF = os.path.join(sec, "faillock.conf")
    scan.PWHISTORY_CONF = os.path.join(sec, "pwhistory.conf")
    scan.PWQUALITY_CONF = os.path.join(sec, "pwquality.conf")
    scan.PWQUALITY_DIR = os.path.join(sec, "pwquality.conf.d")
    scan.CUSTOM_DIR = os.path.join(root, "custom")
    scan.NSSWITCH = os.path.join(root, "nsswitch.conf")
    scan.MODULE_DIRS = (os.path.join(root, "modules"),)
    scan.LIB_DIRS = (os.path.join(root, "lib"),)
    os.makedirs(scan.MODULE_DIRS[0])
    os.makedirs(scan.LIB_DIRS[0])
    return root


def fake_authselect(root, current=None, check_rc=0, renders=None):
    """A stand-in authselect: `current --raw`, `check` and `test PROFILE -s|-p|-n ...`."""
    data = os.path.join(root, "as")
    os.makedirs(data, exist_ok=True)
    for old in os.listdir(data):
        os.remove(os.path.join(data, old))
    if current is not None:
        with open(os.path.join(data, "current"), "w") as fh:
            fh.write(current + "\n")
    with open(os.path.join(data, "check_rc"), "w") as fh:
        fh.write(str(check_rc))
    for opt, text in (renders or {}).items():
        with open(os.path.join(data, "render" + opt), "w") as fh:
            fh.write(text)
    path = os.path.join(root, "authselect")
    with open(path, "w") as fh:
        fh.write("""#!/bin/sh
d=%s
case "$1" in
  current) [ -f "$d/current" ] || { echo "No existing configuration detected."; exit 2; }; cat "$d/current" ;;
  check) exit "$(cat "$d/check_rc")" ;;
  test) f="$d/render$3"; [ -f "$f" ] || exit 1; cat "$f" ;;
  *) exit 1 ;;
esac
""" % data)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
    scan.AUTHSELECT = path


def modules(root, names):
    for name in names:
        open(os.path.join(root, "modules", name + ".so"), "w").close()


def states(res):
    return {k: v["state"] for k, v in res["verdict"].items()}


# 1. A clean guest: plain files, nothing configured.
root = tree(PLAIN)
fake_authselect(root)
res = scan.state("cis-rhel9")
s = states(res)
check("clean 5.3.2.1", s["5.3.2.1"], "bad")
check("clean managed", res["authselect"]["managed"], False)
for cid in ("5.3.2.2", "5.3.2.4", "5.3.3.1.1", "5.3.3.1.2", "5.3.3.1.3", "5.3.3.2.1", "5.3.3.2.2", "5.3.3.2.4",
            "5.3.3.2.5", "5.3.3.2.7", "5.3.3.3.1", "5.3.3.3.2", "5.3.3.3.3", "5.3.3.4.1"):
    check("clean " + cid, s[cid], "bad")
for cid in ("5.3.2.3", "5.3.2.5", "5.3.3.2.6", "5.3.3.4.2", "5.3.3.4.3", "5.3.3.4.4", "5.3.3.2.3"):
    check("clean " + cid, s[cid], "ok")
check("clean nullok is pam_bad", res["verdict"]["5.3.3.4.1"]["pam_bad"], True)
check("clean deny is conf_bad", res["verdict"]["5.3.3.1.1"]["conf_bad"], True)

# 2. Everything configured, on the role's own profile.
root = tree(GOOD, faillock=CONF_GOOD["faillock.conf"], pwhistory=CONF_GOOD["pwhistory.conf"],
            pwq_d={"zz-cis-rhel9.conf": PWQ_GOOD})
fake_authselect(root, current="custom/cis-rhel9 with-faillock with-pwhistory without-nullok")
os.makedirs(os.path.join(scan.CUSTOM_DIR, "cis-rhel9"))
res = scan.state("cis-rhel9")
check("good all ok", {k: v for k, v in states(res).items() if v != "ok"}, {})
check("good owned", res["owned"], True)
check("good owned dir", res["owned_dir_exists"], True)

# 3. authselect check fails: drift.
fake_authselect(root, current="sssd", check_rc=1)
res = scan.state("cis-rhel9")
check("drift 5.3.2.1", states(res)["5.3.2.1"], "bad")
check("drift owned", res["owned"], False)

# 4. Values: stricter values stay compliant, weaker ones fail, the last file wins.
root = tree(GOOD, faillock="deny = 3\nunlock_time = 0\nroot_unlock_time = 30\n", pwhistory="remember = 30\n",
            pwq_main="minlen = 8\ndictcheck = 0\n",
            pwq_d={"50-site.conf": "minlen = 20\nmaxrepeat = 2\ndifok=5\nmaxsequence = 2\nenforce_for_root\n",
                   "zz-cis-rhel9.conf": "dictcheck = 1\n"})
res = scan.state("x")
s = states(res)
check("strict deny", s["5.3.3.1.1"], "ok")
check("unlock_time 0", s["5.3.3.1.2"], "ok")
check("root_unlock_time 30", s["5.3.3.1.3"], "bad")
check("minlen later file wins", s["5.3.3.2.2"], "ok")
check("dictcheck later file wins", s["5.3.3.2.6"], "ok")
check("remember 30", s["5.3.3.3.1"], "ok")
check("maxrepeat 2", s["5.3.3.2.4"], "ok")
# A site file after the role's file wins and is reported with its path.
root = tree(GOOD, pwq_d={"50-a.conf": "minlen = 14\n", "zz-cis-rhel9.conf": "minlen = 14\n", "zzz-site.conf": "minlen = 9\n"})
res = scan.state("x")
check("later site file", res["verdict"]["5.3.3.2.2"]["conf_bad"], True)
check("later site file path", "zzz-site.conf:1" in res["verdict"]["5.3.3.2.2"]["detail"][0], True)
# Files that do not end in .conf are not read.
root = tree(GOOD, pwq_d={"50-a.conf": "minlen = 14\n", "zz.conf.bak": "minlen = 3\n"})
check("only .conf files", states(scan.state("x"))["5.3.3.2.2"], "ok")
# 5.3.3.1.3: even_deny_root alone, or a root_unlock_time of 60 or more.
root = tree(GOOD, faillock="even_deny_root\n")
check("even_deny_root", states(scan.state("x"))["5.3.3.1.3"], "ok")
root = tree(GOOD, faillock="root_unlock_time = 60\n")
check("root_unlock_time 60", states(scan.state("x"))["5.3.3.1.3"], "ok")
root = tree(GOOD, faillock="deny = 5\n")
check("root not covered", states(scan.state("x"))["5.3.3.1.3"], "bad")

# 5. PAM arguments override the files and are judged.
bad = GOOD.replace("pam_faillock.so preauth silent", "pam_faillock.so preauth silent deny=9 unlock_time=60")
bad = bad.replace("pam_pwquality.so try_first_pass", "pam_pwquality.so minlen=8 difok=1 dictcheck=0 maxrepeat=0 maxsequence=9")
bad = bad.replace("pam_pwhistory.so use_authtok", "pam_pwhistory.so remember=5")
bad = bad.replace("pam_unix.so sha512 shadow use_authtok", "pam_unix.so md5 shadow nullok remember=3")
root = tree(bad, faillock=CONF_GOOD["faillock.conf"], pwhistory=CONF_GOOD["pwhistory.conf"], pwq_d={"zz.conf": PWQ_GOOD})
res = scan.state("x")
for cid in ("5.3.3.1.1", "5.3.3.1.2", "5.3.3.2.1", "5.3.3.2.2", "5.3.3.2.4", "5.3.3.2.5", "5.3.3.2.6", "5.3.3.3.1"):
    check("pam arg " + cid, (res["verdict"][cid]["pam_bad"], res["verdict"][cid]["conf_bad"]), (True, False))
for cid in ("5.3.3.3.3", "5.3.3.4.1", "5.3.3.4.2", "5.3.3.4.3", "5.3.3.4.4"):
    check("pam line " + cid, res["verdict"][cid]["state"], "bad")
# Hash arguments: sha512 and yescrypt pass, the others do not; a bracketed control and a continuation work.
root = tree(GOOD.replace("sha512", "yescrypt"))
check("yescrypt", states(scan.state("x"))["5.3.3.4.3"], "ok")
root = tree(GOOD.replace("password    sufficient", "-password   [success=done default=ignore]").replace(
    "pam_unix.so sha512 shadow use_authtok", "pam_unix.so sha512 \\\n shadow use_authtok"))
check("odd control is not a password line", states(scan.state("x"))["5.3.3.4.3"], "bad")
# A missing stack file fails everything that reads it.
root = tree(GOOD, password_auth=None)
os.remove(os.path.join(scan.PAM_DIR, "password-auth"))
res = scan.state("x")
check("missing stack", (res["stacks_present"], states(res)["5.3.2.2"]), (False, "bad"))
# Optional lines (a leading minus) still count as lines of the module.
root = tree(GOOD.replace("password    requisite                                    pam_pwhistory.so", "-password   requisite                                    pam_pwhistory.so"))
check("optional pwhistory line", states(scan.state("x"))["5.3.2.4"], "ok")

# 6. The manual control reports the complexity settings.
root = tree(GOOD, pwq_main="minclass = 3\n", pwq_d={"a.conf": "dcredit = -1\n"})
vals = scan.state("x")["verdict"]["5.3.3.2.3"]["values"]
check("manual minclass", vals["minclass"]["conf"], "3")
check("manual dcredit", vals["dcredit"]["conf"], "-1")

# 7. The lockout guard.
NSS = "passwd: sss files systemd\ngroup: sss files systemd\nshadow: files systemd\n"
root = tree(PLAIN)
modules(root, ["pam_env", "pam_unix", "pam_deny", "pam_pwquality", "pam_keyinit", "pam_limits", "pam_faillock",
               "pam_pwhistory"])
open(os.path.join(root, "lib", "libnss_sss.so.2"), "w").close()
open(os.path.join(root, "lib", "libnss_systemd.so.2"), "w").close()
with open(scan.NSSWITCH, "w") as fh:
    fh.write("passwd: files sss systemd\ngroup: files sss systemd\nshadow: files\n")
fake_authselect(root, renders={"-s": GOOD, "-p": GOOD, "-n": NSS})
res = scan.guard("custom/cis-rhel9", ["with-faillock"])
check("guard ok", res, {"ok": True, "problems": []})
# A module that is not installed.
os.remove(os.path.join(root, "modules", "pam_pwhistory.so"))
res = scan.guard("custom/cis-rhel9", ["with-faillock"])
check("guard missing module", (res["ok"], any("pam_pwhistory" in p for p in res["problems"])), (False, True))
open(os.path.join(root, "modules", "pam_pwhistory.so"), "w").close()
# A module the host uses now that the profile would drop.
with open(os.path.join(scan.PAM_DIR, "system-auth"), "w") as fh:
    fh.write(PLAIN + "auth sufficient pam_krb5.so\n")
res = scan.guard("custom/cis-rhel9", [])
check("guard dropped module", (res["ok"], [p for p in res["problems"] if "pam_krb5" in p] != []), (False, True))
# An optional line the host has is not a loss.
with open(os.path.join(scan.PAM_DIR, "system-auth"), "w") as fh:
    fh.write(PLAIN + "-auth sufficient pam_krb5.so\n")
check("guard optional line", scan.guard("custom/cis-rhel9", [])["ok"], True)
# A name service the host uses now that the profile would drop, and one that is not installed.
with open(scan.NSSWITCH, "w") as fh:
    fh.write("passwd: files ldap\ngroup: files\n")
res = scan.guard("custom/cis-rhel9", [])
check("guard dropped nss", [p for p in res["problems"] if "ldap" in p] != [], True)
os.remove(os.path.join(root, "lib", "libnss_sss.so.2"))
res = scan.guard("custom/cis-rhel9", [])
check("guard missing nss library", [p for p in res["problems"] if "sss for passwd" in p and "not installed" in p] != [], True)
# authselect cannot render.
fake_authselect(root, renders={})
res = scan.guard("custom/none", [])
check("guard cannot render", (res["ok"], any("cannot render" in p for p in res["problems"])), (False, True))

if failures:
    print("\n".join(failures))
    sys.exit(1)
print("pam_scan: all checks passed")

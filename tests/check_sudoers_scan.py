#!/usr/bin/env python3
"""Checks files/sudoers_scan.py against sample sudoers trees. Needs no managed host."""
import contextlib
import importlib.util
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sudoers_scan", os.path.join(HERE, "..", "files", "sudoers_scan.py"))
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

failures = []

# The sample accounts do not exist on the machine running the test.
scan.account_groups = lambda account: None if account == "unknownuser" else {"ansible", "users"}


def check(name, got, want):
    if got != want:
        failures.append("%s: got %r, want %r" % (name, got, want))


def tree(main, extra):
    root = tempfile.mkdtemp()
    os.mkdir(os.path.join(root, "sudoers.d"))
    with open(os.path.join(root, "sudoers"), "w") as fh:
        fh.write(main.replace("@DIR@", os.path.join(root, "sudoers.d")))
    for name, text in extra.items():
        with open(os.path.join(root, "sudoers.d", name), "w") as fh:
            fh.write(text)
    scan.SUDOERS = os.path.join(root, "sudoers")
    return root


STOCK = """Defaults !visiblepw
Defaults always_set_home
Defaults env_reset
root ALL=(ALL) ALL
%wheel ALL=(ALL) ALL
#includedir @DIR@
"""

# Defaults: the last global line wins, and the role file name sorts last.
tree(STOCK, {"ansible": "ansible ALL=(ALL) NOPASSWD: ALL\n"})
check("pty absent", scan.scan_defaults("use_pty", 15)["global_bad"], True)
check("visiblepw stock", scan.scan_defaults("visiblepw", 15)["state"], "ok")
check("timeout default", scan.scan_defaults("timestamp_timeout", 15)["state"], "ok")
check("logfile absent", scan.scan_defaults("logfile", 15)["global_bad"], True)

tree(STOCK, {"zz-cis-rhel9": 'Defaults use_pty\nDefaults logfile="/var/log/sudo.log"\n', "50-x": "Defaults !use_pty\n"})
check("role file wins use_pty", scan.scan_defaults("use_pty", 15)["state"], "ok")
check("role file logfile", scan.scan_defaults("logfile", 15)["state"], "ok")

tree(STOCK, {"zz-cis-rhel9": "Defaults use_pty\n", "zzz-site": "Defaults !use_pty\n"})
r = scan.scan_defaults("use_pty", 15)
check("later file wins", r["state"], "bad")
check("later file named", r["winner"].endswith("zzz-site:1"), True)

tree(STOCK + "Defaults !use_pty\n", {"zz-cis-rhel9": "Defaults use_pty\n"})
check("line after includedir wins", scan.scan_defaults("use_pty", 15)["state"], "bad")

tree(STOCK, {"a": "Defaults env_reset, timestamp_timeout=30\n", "b.bak": "Defaults timestamp_timeout=-1\n"})
check("timeout 30 bad, dotted file ignored", scan.scan_defaults("timestamp_timeout", 15)["global_bad"], True)
tree(STOCK, {"a": "Defaults env_reset, timestamp_timeout=5\n", "zz-cis-rhel9": "Defaults timestamp_timeout=15\n"})
check("timeout 15 ok", scan.scan_defaults("timestamp_timeout", 15)["state"], "ok")
tree(STOCK, {"a": "Defaults timestamp_timeout=-1\n"})
check("timeout -1 bad", scan.scan_defaults("timestamp_timeout", 15)["global_bad"], True)
tree(STOCK, {"a": "Defaults timestamp_type=global\n"})
check("type global bad", scan.scan_defaults("timestamp_type", 15)["global_bad"], True)
tree(STOCK, {"a": "Defaults timestamp_type=global\n", "zz-cis-rhel9": "Defaults timestamp_type=tty\n"})
check("type tty fixes", scan.scan_defaults("timestamp_type", 15)["state"], "ok")
tree(STOCK, {"a": "Defaults pwfeedback\n"})
check("pwfeedback bad", scan.scan_defaults("pwfeedback", 15)["global_bad"], True)
tree(STOCK, {"a": "Defaults pwfeedback\n", "zz-cis-rhel9": "Defaults !pwfeedback\n"})
check("pwfeedback off", scan.scan_defaults("pwfeedback", 15)["state"], "ok")
tree(STOCK, {"a": "Defaults:bob !use_pty\n", "zz-cis-rhel9": "Defaults use_pty\n"})
r = scan.scan_defaults("use_pty", 15)
check("scoped !use_pty", (r["global_bad"], len(r["scoped_bad"])), (False, 1))
tree(STOCK, {"a": "Defaults  env_keep += \"X\", \\\n  pwfeedback\n"})
check("continuation", scan.scan_defaults("pwfeedback", 15)["global_bad"], True)
tree(STOCK, {"a": "# Defaults pwfeedback\n"})
check("comment", scan.scan_defaults("pwfeedback", 15)["state"], "ok")

# Rules.
me = os.environ.get("USER", "nobody")
tree(STOCK, {
    "ansible": "ansible ALL=(ALL) NOPASSWD: ALL\n",
    "bob": "bob ALL=(ALL) NOPASSWD: /usr/bin/id, /usr/bin/ls  # note\n",
    "ops": "%ops, carol ALL=(ALL) NOPASSWD:SETENV: ALL\n",
    "multi": "dave ALL=(ALL) ALL : erin ALL=(ALL) NOPASSWD: ALL\n",
    "dup1": "frank ALL=(ALL) NOPASSWD: ALL\n",
    "dup2": "frank ALL=(ALL) NOPASSWD: ALL\n",
    "none": "gina ALL=(ALL) ALL\n",
    "cont": "hank ALL=(ALL) \\\n  NOPASSWD: ALL\n",
})
r = scan.scan_rules("NOPASSWD", "ansible", True)
check("rules state", r["state"], "bad")
fixed = sorted(f["where"].split("/")[-1] for f in r["fixes"])
check("fixes with guard", fixed, ["bob:1", "dup1:1", "dup2:1", "ops:1"])
check("guarded", sorted(g["where"].split("/")[-1] for g in r["guarded"]), ["ansible:1", "multi:1"])
check("manual", [m["where"].split("/")[-1] for m in r["manual"]], ["cont:1"])
r = scan.scan_rules("NOPASSWD", "ansible", False)
check("fixes without guard", sorted(f["where"].split("/")[-1] for f in r["fixes"]), ["ansible:1", "bob:1", "dup1:1", "dup2:1", "multi:1", "ops:1"])
fx = {f["where"].split("/")[-1]: f for f in r["fixes"]}
check("repl bob", fx["bob:1"]["repl"], "bob ALL=(ALL) /usr/bin/id, /usr/bin/ls  # note")
check("repl ops", fx["ops:1"]["repl"], "%ops, carol ALL=(ALL) SETENV: ALL")
check("repl ansible", fx["ansible:1"]["repl"], "ansible ALL=(ALL) ALL")
r = scan.scan_rules("NOPASSWD", "unknownuser", True)
check("unknown account groups: all guarded or fixed", len(r["fixes"]), 0)

tree(STOCK + "Defaults !authenticate\n", {
    "a": "Defaults:ansible !authenticate\n",
    "b": "Defaults:bob !authenticate, env_reset\n",
    "c": "Defaults env_keep+=\"A\", !authenticate # c\n",
    "d": "Defaults:erin !authenticate\n",
})
r = scan.scan_rules("!authenticate", "ansible", True)
check("auth guarded", sorted(g["where"].split("/")[-1] for g in r["guarded"]), ["a:1", "c:1", "sudoers:7"])
check("auth fixes", sorted(f["where"].split("/")[-1] for f in r["fixes"]), ["b:1", "d:1"])
fx = {f["where"].split("/")[-1]: f for f in r["fixes"]}
check("auth repl b", fx["b:1"]["repl"], "Defaults:bob env_reset")
check("auth repl d", fx["d:1"]["repl"], "# disabled by the CIS RHEL 9 role (5.2.7): Defaults:erin !authenticate")
r = scan.scan_rules("!authenticate", "ansible", False)
fx = {f["where"].split("/")[-1]: f for f in r["fixes"]}
check("auth repl c", fx["c:1"]["repl"], 'Defaults env_keep+="A" # c')

# Missing sudoers.
scan.SUDOERS = "/nonexistent/sudoers"
with contextlib.redirect_stdout(io.StringIO()):
    check("missing", scan.main(["x", "defaults", "use_pty", "15"]), 0)

if failures:
    print("\n".join(failures))
    sys.exit(1)
print("sudoers_scan: all checks passed")

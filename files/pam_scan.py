# Read-only scanner for the PAM controls of section 5.3. It reads the effective PAM stacks
# (/etc/pam.d/system-auth and password-auth), the pam_faillock, pam_pwquality and
# pam_pwhistory configuration files and what authselect reports, and prints one JSON object.
# It never writes anything. The role passes it to the managed node's Python with
# `python -c`, so keep it standard library only and compatible with Python 3.9.
#
#   pam_scan.py state PROFILE
#       Judges every 5.3.2 and 5.3.3 control from the files PAM reads at run time. PROFILE
#       is the name of the role's own authselect profile (without "custom/"). Each verdict
#       has state ok|bad, conf_bad (a setting that belongs in a configuration file is
#       missing or not compliant there), pam_bad (a PAM line carries an argument, or lacks
#       one, that makes the control fail) and detail (messages naming file and line).
#   pam_scan.py guard PROFILE_ID [FEATURE ...]
#       The lockout guard: renders what authselect would write for that profile and
#       features (authselect test, nothing is written) and reports a problem when a stack
#       line names a PAM module that is not installed, when the PAM stacks or nsswitch.conf
#       now in place use a module or a name service the rendering would drop, or when
#       authselect cannot render it.
import json
import os
import re
import shutil
import subprocess
import sys

PAM_DIR = "/etc/pam.d"
STACKS = ("system-auth", "password-auth")
FAILLOCK_CONF = "/etc/security/faillock.conf"
PWQUALITY_CONF = "/etc/security/pwquality.conf"
PWQUALITY_DIR = "/etc/security/pwquality.conf.d"
PWHISTORY_CONF = "/etc/security/pwhistory.conf"
CUSTOM_DIR = "/etc/authselect/custom"
NSSWITCH = "/etc/nsswitch.conf"
MODULE_DIRS = ("/usr/lib64/security", "/lib64/security", "/usr/lib/security")
LIB_DIRS = ("/usr/lib64", "/lib64", "/usr/lib")
AUTHSELECT = "authselect"
TYPES = ("auth", "account", "password", "session")
# Name services nsswitch.conf handles without a separate library.
BUILTIN_NSS = ("files", "compat", "dns", "db", "nis", "nisplus")
NSS_DATABASES = ("passwd", "group", "shadow", "gshadow", "netgroup")
# Files authselect renders and the option of `authselect test` that prints each.
RENDER_OPTION = {"system-auth": "-s", "password-auth": "-p"}


def run(argv):
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    except OSError:
        return 127, "", ""
    return proc.returncode, proc.stdout, proc.stderr


def tokenize(text):
    return [m.group(0) for m in re.finditer(r"\[[^\]]*\]|\S+", text)]


def parse_pam_text(text):
    """Return the stack lines of a PAM file: type, control, module (name without .so), args."""
    lines = []
    buf = ""
    for raw in text.splitlines():
        if raw.rstrip().endswith("\\"):
            buf += raw.rstrip()[:-1] + " "
            continue
        line = buf + raw
        buf = ""
        stripped = re.sub(r"(^|\s)#.*$", "", line).strip()
        if not stripped:
            continue
        tokens = tokenize(stripped)
        if tokens[0] == "@include" and len(tokens) > 1:
            lines.append({"type": "@include", "optional": False, "control": "", "module": tokens[1],
                          "path": tokens[1], "args": []})
            continue
        optional = tokens[0].startswith("-")
        ltype = tokens[0].lstrip("-")
        if ltype not in TYPES or len(tokens) < 3:
            continue
        path = tokens[2]
        name = os.path.basename(path)
        if name.endswith(".so"):
            name = name[:-3]
        lines.append({"type": ltype, "optional": optional, "control": tokens[1], "module": name,
                      "path": path, "args": tokens[3:]})
    return lines


def read_text(path):
    try:
        with open(path, "r") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None


def read_pam(path):
    text = read_text(path)
    return None if text is None else parse_pam_text(text)


def split_arg(arg):
    if "=" in arg:
        key, value = arg.split("=", 1)
        return key.strip().lower(), value.strip()
    return arg.strip().lower(), None


def to_int(value):
    try:
        return int(str(value).strip(), 10)
    except (TypeError, ValueError):
        return None


def read_conf(path):
    """Active settings of a key = value file: list of (path, lineno, key, value or None)."""
    text = read_text(path)
    out = []
    if text is None:
        return out
    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*(.*?))?\s*$", stripped)
        if match:
            out.append((path, number, match.group(1).lower(), match.group(2)))
    return out


def pwquality_entries():
    """pwquality.conf, then pwquality.conf.d/*.conf in name order: libpwquality applies them in
    that order and the last value of a key wins."""
    entries = read_conf(PWQUALITY_CONF)
    try:
        names = sorted(n for n in os.listdir(PWQUALITY_DIR) if n.endswith(".conf"))
    except OSError:
        names = []
    for name in names:
        path = os.path.join(PWQUALITY_DIR, name)
        if os.path.isfile(path):
            entries += read_conf(path)
    return entries


def last(entries, key):
    found = [e for e in entries if e[2] == key]
    return found[-1] if found else None


def has_flag(entries, key):
    return any(e[2] == key for e in entries)


def where(entry):
    return "%s:%d" % (entry[0], entry[1])


def pam_args(stacks, module, ltypes, key):
    """Values of a key=value argument on lines of a module: list of (stack, value)."""
    found = []
    for name in STACKS:
        for line in stacks.get(name) or []:
            if line["module"] != module or line["type"] not in ltypes:
                continue
            for arg in line["args"]:
                k, v = split_arg(arg)
                if k == key:
                    found.append((name, v))
    return found


def pam_flag(stacks, module, ltypes, key):
    found = []
    for name in STACKS:
        for line in stacks.get(name) or []:
            if line["module"] == module and line["type"] in ltypes and any(split_arg(a)[0] == key for a in line["args"]):
                found.append(name)
    return found


def verdict(conf_bad=False, pam_bad=False, detail=None):
    return {"state": "bad" if (conf_bad or pam_bad) else "ok", "conf_bad": conf_bad, "pam_bad": pam_bad,
            "detail": detail or []}


def numeric(entries, stacks, key, ok, module, ltypes, need_value):
    """A numeric setting in a configuration file and as an argument of the PAM module.
    need_value: the file must set it (the benchmark's audit looks for the line); otherwise only
    a value that is set and not compliant fails."""
    detail = []
    conf_bad = False
    pam_bad = False
    entry = last(entries, key)
    if entry is None:
        conf_bad = need_value
        if need_value:
            detail.append("%s is not set" % key)
    else:
        number = to_int(entry[3])
        if number is None or not ok(number):
            conf_bad = True
            detail.append("%s = %s at %s is not compliant" % (key, entry[3], where(entry)))
    for stack, value in pam_args(stacks, module, ltypes, key):
        number = to_int(value)
        if number is None or not ok(number):
            pam_bad = True
            detail.append("%s=%s on the %s line of %s is not compliant" % (key, value, module, stack))
    return verdict(conf_bad, pam_bad, detail)


def module_verdict(missing):
    return verdict(False, bool(missing), ["missing: " + ", ".join(missing)] if missing else [])


def missing_lines(stacks, wanted):
    """wanted: list of (label, ltype, module, controls, arg). Returns the labels missing in a stack."""
    out = []
    for label, ltype, module, controls, arg in wanted:
        for name in STACKS:
            lines = stacks.get(name)
            found = False
            for line in lines or []:
                if line["type"] != ltype or line["module"] != module:
                    continue
                if controls and line["control"] not in controls:
                    continue
                if arg and not any(split_arg(a)[0] == arg for a in line["args"]):
                    continue
                found = True
            if not found:
                out.append("%s in %s" % (label, name))
    return out


def password_lines(stacks, module):
    """(stack, line) for each password line of the module; a stack with none is (stack, None)."""
    out = []
    for name in STACKS:
        found = [l for l in stacks.get(name) or [] if l["type"] == "password" and l["module"] == module]
        out += [(name, l) for l in found] or [(name, None)]
    return out


def authselect_info():
    info = {"present": False, "managed": False, "profile": "", "features": [], "check_ok": False,
            "check_message": "", "current_message": ""}
    if not shutil.which(AUTHSELECT):
        return info
    info["present"] = True
    rc, out, err = run([AUTHSELECT, "current", "--raw"])
    if rc == 0 and out.split():
        tokens = out.split()
        info["managed"] = True
        info["profile"] = tokens[0]
        info["features"] = tokens[1:]
        info["current_message"] = out.strip()
    else:
        info["current_message"] = (out + err).strip()
    if info["managed"]:
        rc, out, err = run([AUTHSELECT, "check"])
        info["check_ok"] = rc == 0
        info["check_message"] = (out + err).strip()
    return info


def state(profile_name):
    info = authselect_info()
    stacks = {name: read_pam(os.path.join(PAM_DIR, name)) for name in STACKS}
    faillock = read_conf(FAILLOCK_CONF)
    pwq = pwquality_entries()
    pwhist = read_conf(PWHISTORY_CONF)
    v = {}

    v["5.3.2.1"] = verdict(False, not (info["managed"] and info["check_ok"]),
                           [] if info["managed"] and info["check_ok"] else
                           ["PAM is not managed by an authselect profile" if not info["managed"]
                            else "authselect check: " + info["check_message"]])
    v["5.3.2.2"] = module_verdict(missing_lines(stacks, [
        ("auth preauth line", "auth", "pam_faillock", None, "preauth"),
        ("auth authfail line", "auth", "pam_faillock", None, "authfail"),
        ("account line", "account", "pam_faillock", None, None)]))
    v["5.3.2.3"] = module_verdict(missing_lines(stacks, [
        ("password line", "password", "pam_pwquality", ("requisite", "required"), None)]))
    v["5.3.2.4"] = module_verdict(missing_lines(stacks, [
        ("password line", "password", "pam_pwhistory", ("requisite", "required"), None)]))
    v["5.3.2.5"] = module_verdict(missing_lines(stacks, [
        ("auth line", "auth", "pam_unix", None, None), ("account line", "account", "pam_unix", None, None),
        ("password line", "password", "pam_unix", None, None), ("session line", "session", "pam_unix", None, None)]))

    v["5.3.3.1.1"] = numeric(faillock, stacks, "deny", lambda n: 1 <= n <= 5, "pam_faillock", ("auth",), True)
    v["5.3.3.1.2"] = numeric(faillock, stacks, "unlock_time", lambda n: n == 0 or n >= 900, "pam_faillock", ("auth",), True)

    # 5.3.3.1.3: root is subject to the lockout (even_deny_root, or a root_unlock_time that implies
    # it), and a root_unlock_time that is set is 0 or at least 60.
    root_ok = lambda n: n == 0 or n >= 60
    rut = numeric(faillock, stacks, "root_unlock_time", root_ok, "pam_faillock", ("auth",), False)
    if not (has_flag(faillock, "even_deny_root") or last(faillock, "root_unlock_time") is not None):
        rut["conf_bad"] = True
        rut["state"] = "bad"
        rut["detail"].append("even_deny_root is not set")
    v["5.3.3.1.3"] = rut

    v["5.3.3.2.1"] = numeric(pwq, stacks, "difok", lambda n: n >= 2, "pam_pwquality", ("password",), True)
    v["5.3.3.2.2"] = numeric(pwq, stacks, "minlen", lambda n: n >= 14, "pam_pwquality", ("password",), True)
    v["5.3.3.2.4"] = numeric(pwq, stacks, "maxrepeat", lambda n: 1 <= n <= 3, "pam_pwquality", ("password",), True)
    v["5.3.3.2.5"] = numeric(pwq, stacks, "maxsequence", lambda n: 1 <= n <= 3, "pam_pwquality", ("password",), True)
    v["5.3.3.2.6"] = numeric(pwq, stacks, "dictcheck", lambda n: n != 0, "pam_pwquality", ("password",), False)
    v["5.3.3.2.7"] = verdict(not has_flag(pwq, "enforce_for_root"), False,
                             [] if has_flag(pwq, "enforce_for_root") else ["enforce_for_root is not set"])

    # 5.3.3.2.3 is manual: the values in effect, for review.
    manual = {}
    for key in ("minclass", "dcredit", "ucredit", "lcredit", "ocredit"):
        entry = last(pwq, key)
        args = pam_args(stacks, "pam_pwquality", ("password",), key)
        manual[key] = {"conf": entry[3] if entry else None, "pam": ["%s:%s" % a for a in args]}
    v["5.3.3.2.3"] = verdict()
    v["5.3.3.2.3"]["values"] = manual

    v["5.3.3.3.1"] = numeric(pwhist, stacks, "remember", lambda n: n >= 24, "pam_pwhistory", ("password",), True)
    v["5.3.3.3.2"] = verdict(not has_flag(pwhist, "enforce_for_root"), False,
                             [] if has_flag(pwhist, "enforce_for_root") else ["enforce_for_root is not set"])
    hist = [(s, l) for s, l in password_lines(stacks, "pam_pwhistory")]
    bad = [s for s, l in hist if l is None or not any(split_arg(a)[0] == "use_authtok" for a in l["args"])]
    v["5.3.3.3.3"] = verdict(False, bool(bad), ["no use_authtok on the pam_pwhistory password line of " + ", ".join(bad)] if bad else [])

    unix_lines = [(n, l) for n in STACKS for l in stacks.get(n) or [] if l["module"] == "pam_unix"]
    nullok = sorted(set(n for n, l in unix_lines if any(split_arg(a)[0] == "nullok" for a in l["args"])))
    v["5.3.3.4.1"] = verdict(False, bool(nullok), ["nullok on a pam_unix line of " + ", ".join(nullok)] if nullok else [])
    remember = sorted(set(n for n, l in unix_lines if l["type"] == "password"
                          and any(split_arg(a)[0] == "remember" for a in l["args"])))
    v["5.3.3.4.2"] = verdict(False, bool(remember), ["remember on a pam_unix password line of " + ", ".join(remember)] if remember else [])
    weak = []
    for name, line in password_lines(stacks, "pam_unix"):
        if line is None or line["control"] not in ("requisite", "required", "sufficient") \
                or not any(split_arg(a)[0] in ("sha512", "yescrypt") for a in line["args"]):
            weak.append(name)
    v["5.3.3.4.3"] = verdict(False, bool(weak), ["no sha512 or yescrypt on the pam_unix password line of " + ", ".join(sorted(set(weak)))] if weak else [])
    noauth = [n for n, l in password_lines(stacks, "pam_unix")
              if l is None or not any(split_arg(a)[0] == "use_authtok" for a in l["args"])]
    v["5.3.3.4.4"] = verdict(False, bool(noauth), ["no use_authtok on the pam_unix password line of " + ", ".join(sorted(set(noauth)))] if noauth else [])

    owned_id = "custom/" + profile_name
    return {
        "authselect": info,
        "owned": info["managed"] and info["profile"] == owned_id,
        "owned_dir_exists": os.path.isdir(os.path.join(CUSTOM_DIR, profile_name)),
        "stacks_present": all(stacks[n] is not None for n in STACKS),
        "verdict": v,
    }


def module_exists(path):
    if os.path.isabs(path):
        return os.path.exists(path)
    name = path if path.endswith(".so") else path + ".so"
    return any(os.path.exists(os.path.join(d, name)) for d in MODULE_DIRS)


def nss_sources(text):
    """Name services of each database in the nsswitch.conf text, without [STATUS=action] items."""
    out = {}
    for raw in (text or "").splitlines():
        line = re.sub(r"#.*$", "", raw).strip()
        match = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if match:
            items = re.sub(r"\[[^\]]*\]", " ", match.group(2)).split()
            out[match.group(1)] = items
    return out


def nss_library_exists(source):
    return any(os.path.exists(os.path.join(d, "libnss_%s.so.2" % source)) for d in LIB_DIRS)


def guard(profile_id, features):
    problems = []
    for name in STACKS:
        rc, out, err = run([AUTHSELECT, "test", profile_id, RENDER_OPTION[name]] + features)
        if rc != 0 or not out.strip():
            problems.append("authselect cannot render %s for %s: %s" % (name, profile_id, (err or out).strip()[:200]))
            continue
        new = parse_pam_text(out)
        if not new:
            problems.append("the rendering of %s for %s has no PAM lines" % (name, profile_id))
            continue
        new_modules = set(l["module"] for l in new if l["type"] != "@include")
        for line in new:
            if line["type"] == "@include" or line["optional"]:
                continue
            if not module_exists(line["path"]):
                problems.append("%s for %s names %s, which is not installed" % (name, profile_id, line["path"]))
        current = read_pam(os.path.join(PAM_DIR, name))
        for line in current or []:
            if line["type"] == "@include" or line["optional"]:
                continue
            if line["module"] not in new_modules:
                problems.append("%s now uses %s, which %s would drop" % (name, line["module"], profile_id))
                new_modules.add(line["module"])
    rc, out, err = run([AUTHSELECT, "test", profile_id, "-n"] + features)
    if rc == 0 and out.strip():
        new_nss = nss_sources(out)
        old_nss = nss_sources(read_text(NSSWITCH))
        for db in NSS_DATABASES:
            for source in new_nss.get(db, []):
                if source not in BUILTIN_NSS and not nss_library_exists(source):
                    problems.append("nsswitch.conf for %s would use %s for %s, which is not installed" % (profile_id, source, db))
            for source in old_nss.get(db, []):
                if source not in new_nss.get(db, []):
                    problems.append("nsswitch.conf now uses %s for %s, which %s would drop" % (source, db, profile_id))
    else:
        problems.append("authselect cannot render nsswitch.conf for %s: %s" % (profile_id, (err or out).strip()[:200]))
    return {"ok": not problems, "problems": problems}


def main(argv):
    if len(argv) >= 3 and argv[1] == "state":
        print(json.dumps(state(argv[2])))
        return 0
    if len(argv) >= 3 and argv[1] == "guard":
        print(json.dumps(guard(argv[2], argv[3:])))
        return 0
    sys.stderr.write("usage: pam_scan.py state PROFILE | guard PROFILE_ID [FEATURE ...]\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

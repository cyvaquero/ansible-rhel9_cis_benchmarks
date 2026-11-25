# Read-only scanner for the account and environment controls of section 5.4. It reads the
# account databases (passwd, shadow, group, shells, login.defs, the useradd defaults), the
# shell initialization files and the running processes, and prints one JSON object. It never
# writes anything. The role passes it to the managed node's Python with `python -c`, so keep
# it standard library only and compatible with Python 3.9.
#
#   accounts_scan.py state PARAMS_JSON
#       Judges the 5.4 controls and plans the changes. PARAMS_JSON holds what the site
#       configured (max_days, warn_age, inactive_days, umask, tmout, encrypt_method), the
#       benchmark limits the checks judge against ("expect": max_days_max, warn_age_min,
#       min_days_min, inactive_max, umask, tmout_max, encrypt_methods; without it the built-in
#       benchmark limits below apply, which only the tests rely on, and the role always passes
#       its constants), the accounts the role must never touch (guard), the site's exceptions
#       (exceptions), the role's own profile.d file (owned_profile), what root's login shell
#       reported (effective_umask, root_path, may be empty) and whether to ask passwd for each
#       account's lock state (lock). A control's "ok" judges the benchmark; its "fix" says the
#       value has to be written, because it fails the benchmark or differs from what the site
#       configured (a stricter value included).
#   accounts_scan.py rootpath PATH
#       Prints the problems of one PATH value as a JSON list (5.4.2.5).
import glob
import json
import os
import re
import subprocess
import sys
import time

# Tests point this at a sample tree; every path the scanner reads goes through P().
ROOT = ""

LOGIN_DEFS = "/etc/login.defs"
USERADD_DEFAULTS = "/etc/default/useradd"
PASSWD = "/etc/passwd"
SHADOW = "/etc/shadow"
GROUP = "/etc/group"
SHELLS = "/etc/shells"
SYSTEM_AUTH = "/etc/pam.d/system-auth"
# The benchmark's limits, the defaults of state()'s "expect" parameter.
MAX_DAYS_LIMIT = 365
WARN_AGE_FLOOR = 7
MIN_DAYS_FLOOR = 1
INACTIVE_LIMIT = 45
UMASK_FLOOR = 0o027
TMOUT_LIMIT = 900
ENCRYPT_METHODS = ("SHA512", "YESCRYPT")
NO_EXPIRY = 99999
# 5.4.2.7 leaves these accounts a login shell; 5.4.2.2 allows these to have GID 0.
SHELL_EXEMPT = ("root", "halt", "sync", "shutdown", "nfsnobody")
GID0_ALLOWED = ("root", "sync", "shutdown", "halt", "operator")
NOLOGIN_SHELL_NAMES = ("nologin", "false")


def configure(params):
    """Takes the benchmark limits from the "expect" parameter, over the built-in ones."""
    global MAX_DAYS_LIMIT, WARN_AGE_FLOOR, MIN_DAYS_FLOOR, INACTIVE_LIMIT, UMASK_FLOOR, TMOUT_LIMIT, ENCRYPT_METHODS
    expect = params.get("expect") or {}
    MAX_DAYS_LIMIT = to_int(expect.get("max_days_max")) or MAX_DAYS_LIMIT
    WARN_AGE_FLOOR = to_int(expect.get("warn_age_min")) or WARN_AGE_FLOOR
    MIN_DAYS_FLOOR = to_int(expect.get("min_days_min")) or MIN_DAYS_FLOOR
    INACTIVE_LIMIT = to_int(expect.get("inactive_max")) or INACTIVE_LIMIT
    if expect.get("umask"):
        UMASK_FLOOR = int(str(expect["umask"]), 8) & 0o777
    TMOUT_LIMIT = to_int(expect.get("tmout_max")) or TMOUT_LIMIT
    if expect.get("encrypt_methods"):
        ENCRYPT_METHODS = tuple(str(m).upper() for m in expect["encrypt_methods"])


def want_mask(params):
    """The umask the site configured, as a mask, or None."""
    raw = params.get("umask")
    return umask_value(str(raw)) if raw not in (None, "") else None


def P(path):
    return ROOT + path


def read_text(path):
    try:
        with open(P(path), encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def where(path, number):
    return "%s:%d" % (path, number)


def login_defs():
    """The value of every key in login.defs; the last line of a key wins."""
    values = {}
    for line in (read_text(LOGIN_DEFS) or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) == 2:
            values[parts[0].upper()] = parts[1].strip()
    return values


def useradd_inactive():
    """INACTIVE from /etc/default/useradd (what `useradd -D` prints); None when unset."""
    value = None
    for line in (read_text(USERADD_DEFAULTS) or "").splitlines():
        match = re.match(r"^\s*INACTIVE\s*=\s*(\S*)", line)
        if match:
            value = match.group(1).strip("\"'")
    if value is None or value == "":
        return None
    return to_int(value)


# ---- accounts ----------------------------------------------------------------------------

def read_passwd():
    accounts = []
    for line in (read_text(PASSWD) or "").splitlines():
        parts = line.split(":")
        if len(parts) < 7 or not parts[0] or line.lstrip().startswith("#"):
            continue
        uid, gid = to_int(parts[2]), to_int(parts[3])
        if uid is None:
            continue
        accounts.append({"name": parts[0], "uid": uid, "gid": gid, "home": parts[5], "shell": parts[6]})
    return accounts


def read_shadow():
    shadow = {}
    for line in (read_text(SHADOW) or "").splitlines():
        parts = line.split(":")
        if len(parts) < 9 or not parts[0]:
            continue
        shadow[parts[0]] = {
            "field": parts[1],
            "lastchg": to_int(parts[2]),
            "min": to_int(parts[3]),
            "max": to_int(parts[4]),
            "warn": to_int(parts[5]),
            "inactive": to_int(parts[6]),
        }
    return shadow


def read_groups():
    groups = []
    for line in (read_text(GROUP) or "").splitlines():
        parts = line.split(":")
        if len(parts) >= 3 and parts[0]:
            gid = to_int(parts[2])
            if gid is not None:
                groups.append({"name": parts[0], "gid": gid})
    return groups


def valid_shells():
    """The shells of /etc/shells that are not nologin or false."""
    shells = set()
    for line in (read_text(SHELLS) or "").splitlines():
        entry = line.strip()
        if entry.startswith("/") and os.path.basename(entry) not in NOLOGIN_SHELL_NAMES:
            shells.add(entry.split()[0])
    return shells


def nologin_lines():
    found = []
    for number, line in enumerate((read_text(SHELLS) or "").splitlines(), 1):
        if re.match(r"^\s*[^#\n\r]*/nologin\b", line):
            found.append({"line": number, "text": line.strip()})
    return found


def running_uids():
    """Every UID (real or effective) that owns a process."""
    uids = set()
    for status in glob.glob(P("/proc/[0-9]*/status")):
        try:
            with open(status, encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.startswith("Uid:"):
                        for value in line.split()[1:3]:
                            number = to_int(value)
                            if number is not None:
                                uids.add(number)
                        break
        except OSError:
            continue
    return uids


def passwd_status(name):
    """The status letters of `passwd -S NAME` (P, L, NP), or None when it cannot be read."""
    try:
        proc = subprocess.run(["passwd", "-S", name], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
    except OSError:
        return None
    parts = proc.stdout.split()
    if proc.returncode != 0 or len(parts) < 2:
        return None
    return parts[1]


def is_locked(name, field):
    status = passwd_status(name)
    if status is not None:
        return status.startswith("L")
    return field.startswith("!") or field.startswith("*")


def today_days(params):
    value = to_int(params.get("today"))
    return value if value is not None else int(time.time() // 86400)


def password_state(lastchg, maximum, inactive, today):
    """What the password's age amounts to: ok, must-change, expired or inactive. Conservative:
    a password that expires today counts as expired."""
    if lastchg == 0:
        return "must-change"
    unlimited = maximum is None or maximum < 0 or maximum >= NO_EXPIRY
    if lastchg is None:
        # With no last change date pam_unix reads day -1, so any maximum age expires it at once.
        return "ok" if unlimited else "expired"
    if unlimited:
        return "ok"
    age = today - lastchg
    if inactive is not None and inactive >= 0 and age >= maximum + inactive:
        return "inactive"
    if age >= maximum:
        return "expired"
    return "ok"


def state_reason(state, lastchg, maximum, today):
    if state == "must-change":
        return "its last change date is 0, so it must change its password at the next login"
    if lastchg is None:
        return "it has no last change date, so a maximum age would expire its password at once"
    age = today - lastchg
    if state == "inactive":
        return "its password is %d days old, so the account would be inactive" % age
    return "its password is %d days old, so a maximum of %s days would expire it" % (age, maximum)


def aging(accounts, shadow, params, today):
    """Plans the password aging of 5.4.1.1, 5.4.1.3 and 5.4.1.5 for accounts with a hash. An
    account is planned when its value differs from the configured one (without one: when it fails
    the benchmark). The plan's entries say "bad": true when the account's current value fails the
    benchmark; a skipped account that is bad makes the control a finding. A configured value that is
    itself weaker than the benchmark is reported by target_ok, not here."""
    target = {"max": to_int(params.get("max_days")), "warn": to_int(params.get("warn_age")),
              "inactive": to_int(params.get("inactive_days"))}
    plan = {key: {"fix": [], "skip": []} for key in target}
    min_below, future = [], []
    for account in accounts:
        entry = shadow.get(account["name"])
        if entry is None or not re.match(r"^\$.+\$", entry["field"]):
            continue
        name, last = account["name"], entry["lastchg"]
        maximum, warn, inactive = entry["max"], entry["warn"], entry["inactive"]
        if entry["min"] is None or entry["min"] < MIN_DAYS_FLOOR:
            min_below.append(name)
        if last is not None and last > today:
            future.append(name)
        final_max = maximum
        max_bad = not (maximum is not None and 1 <= maximum <= MAX_DAYS_LIMIT)
        if (maximum != target["max"]) if target["max"] is not None else max_bad:
            state = password_state(last, target["max"], inactive, today)
            if state == "ok":
                plan["max"]["fix"].append({"user": name, "value": target["max"], "bad": max_bad})
                final_max = target["max"]
            else:
                plan["max"]["skip"].append({"user": name, "bad": max_bad,
                                            "reason": state_reason(state, last, target["max"], today)})
        warn_bad = warn is None or warn < WARN_AGE_FLOOR
        if (warn != target["warn"]) if target["warn"] is not None else warn_bad:
            state = password_state(last, final_max, inactive, today)
            if state == "ok":
                plan["warn"]["fix"].append({"user": name, "value": target["warn"], "bad": warn_bad})
            else:
                plan["warn"]["skip"].append({"user": name, "bad": warn_bad,
                                             "reason": state_reason(state, last, final_max, today)})
        inactive_bad = inactive is None or inactive < 0 or inactive > INACTIVE_LIMIT
        if (inactive != target["inactive"]) if target["inactive"] is not None else inactive_bad:
            state = password_state(last, final_max, target["inactive"], today)
            if state == "ok":
                plan["inactive"]["fix"].append({"user": name, "value": target["inactive"], "bad": inactive_bad})
            else:
                plan["inactive"]["skip"].append({"user": name, "bad": inactive_bad,
                                                 "reason": state_reason(state, last, final_max, today)})
    return plan, min_below, future


def account_state(params, defs):
    today = today_days(params)
    accounts = read_passwd()
    shadow = read_shadow()
    groups = read_groups()
    out = {}

    maximum, warn = to_int(defs.get("PASS_MAX_DAYS")), to_int(defs.get("PASS_WARN_AGE"))
    minimum = to_int(defs.get("PASS_MIN_DAYS"))
    encrypt = defs.get("ENCRYPT_METHOD", "")
    inactive_default = useradd_inactive()
    want_max, want_warn = to_int(params.get("max_days")), to_int(params.get("warn_age"))
    want_inactive = to_int(params.get("inactive_days"))
    want_encrypt = str(params.get("encrypt_method") or "").upper() or want_hash()
    max_ok = maximum is not None and 1 <= maximum <= MAX_DAYS_LIMIT
    warn_ok = warn is not None and warn >= WARN_AGE_FLOOR
    inactive_ok = inactive_default is not None and 0 <= inactive_default <= INACTIVE_LIMIT
    encrypt_ok = encrypt.upper() in ENCRYPT_METHODS
    out["defaults"] = {
        "max": {"value": defs.get("PASS_MAX_DAYS"), "ok": max_ok,
                "fix": (maximum != want_max) if want_max is not None else not max_ok},
        "warn": {"value": defs.get("PASS_WARN_AGE"), "ok": warn_ok,
                 "fix": (warn != want_warn) if want_warn is not None else not warn_ok},
        "min": {"value": defs.get("PASS_MIN_DAYS"), "ok": minimum is not None and minimum >= MIN_DAYS_FLOOR},
        "inactive": {"value": inactive_default, "ok": inactive_ok,
                     "fix": (inactive_default != want_inactive) if want_inactive is not None else not inactive_ok},
        "encrypt": {"value": encrypt, "ok": encrypt_ok, "want": want_encrypt,
                    "fix": encrypt.upper() != want_encrypt},
    }
    # Whether what the site configured meets the benchmark itself; a weaker value is written and
    # makes the control a finding on every run.
    wmask = want_mask(params)
    want_tmout = to_int(params.get("tmout"))
    out["target_ok"] = {
        "max": want_max is None or 1 <= want_max <= MAX_DAYS_LIMIT,
        "warn": want_warn is None or want_warn >= WARN_AGE_FLOOR,
        "inactive": want_inactive is None or 0 <= want_inactive <= INACTIVE_LIMIT,
        "umask": wmask is None or umask_ok(wmask),
        "tmout": want_tmout is None or 0 < want_tmout <= TMOUT_LIMIT,
        "encrypt": want_encrypt in ENCRYPT_METHODS,
    }
    plan, min_below, future = aging(accounts, shadow, params, today)
    out["aging"] = plan
    out["min_below"] = min_below
    out["future"] = future

    out["uid0"] = [a["name"] for a in accounts if a["uid"] == 0]
    out["gid0_accounts"] = [a["name"] for a in accounts if a["gid"] == 0 and a["name"] not in GID0_ALLOWED]
    out["gid0_groups"] = [g["name"] for g in groups if g["gid"] == 0 and g["name"] != "root"]
    root = shadow.get("root")
    out["root_status"] = (passwd_status("root") or "unknown") if root is not None else "unknown"

    uid_min = to_int(defs.get("UID_MIN")) or 1000
    out["uid_min"] = uid_min
    shells = valid_shells()
    guard = set(n for n in params.get("guard", []) if n)
    exceptions = set(n for n in params.get("exceptions", []) if n)
    busy = running_uids()

    def skip_reason(account):
        if account["name"] in guard:
            return "the role is connected as this account or becomes it"
        if account["name"] in exceptions:
            return "listed in cis_account_exceptions"
        if account["uid"] in busy:
            return "it has a running process"
        return None

    def is_system(account):
        return account["uid"] < uid_min or account["uid"] == 65534

    nologin = which_nologin()
    out["nologin_path"] = nologin
    sysshell = {"fix": [], "skip": []}
    for account in accounts:
        if account["name"] in SHELL_EXEMPT or not is_system(account) or account["shell"] not in shells:
            continue
        reason = skip_reason(account)
        if reason:
            sysshell["skip"].append({"user": account["name"], "shell": account["shell"], "reason": reason})
        else:
            sysshell["fix"].append({"user": account["name"], "shell": account["shell"]})
    out["sysshell"] = sysshell

    lock = {"fix": [], "skip": [], "other": []}
    if params.get("lock"):
        for account in accounts:
            if account["name"] == "root" or account["shell"] in shells:
                continue
            entry = shadow.get(account["name"])
            if entry is None or is_locked(account["name"], entry["field"]):
                continue
            if not is_system(account):
                lock["other"].append({"user": account["name"], "reason": "not a system account (UID %d)" % account["uid"]})
                continue
            reason = skip_reason(account)
            if reason:
                lock["skip"].append({"user": account["name"], "reason": reason})
            else:
                lock["fix"].append({"user": account["name"]})
    out["lock"] = lock

    out["nologin_lines"] = nologin_lines()
    return out


def want_hash():
    """The ENCRYPT_METHOD to write when the caller passes none (the tests): YESCRYPT when pam_unix
    already hashes with yescrypt (and not sha512), so the two agree; SHA512 otherwise. The role
    always passes encrypt_method (cis_encrypt_method), which it keeps in step with the pam_unix line."""
    for line in (read_text(SYSTEM_AUTH) or "").splitlines():
        code = line.split("#")[0]
        if re.match(r"^\s*password\s+\S+\s+\S*pam_unix\.so\b", code):
            if re.search(r"\byescrypt\b", code) and not re.search(r"\bsha512\b", code):
                return "YESCRYPT"
    return "SHA512"


def which_nologin():
    for path in ("/usr/sbin/nologin", "/sbin/nologin"):
        if os.path.exists(P(path)):
            return path
    return "/usr/sbin/nologin"


# ---- umask, TMOUT and PATH ---------------------------------------------------------------

def umask_value(arg):
    """The mask an umask argument denies, as an int, or None when it cannot be evaluated
    statically (the same rule as the benchmark: octal, or symbolic with = clauses only)."""
    if re.match(r"^[0-7]{3,4}$", arg):
        return int(arg, 8) & 0o777
    classes = {"u": 0, "g": 0, "o": 0}
    for clause in arg.split(","):
        match = re.match(r"^([augo]+)=([rwx]*)$", clause)
        if not match:
            return None
        who, perms = match.groups()
        deny = 7 - (4 * ("r" in perms) + 2 * ("w" in perms) + 1 * ("x" in perms))
        for letter in ("u", "g", "o"):
            if "a" in who or letter in who:
                classes[letter] = deny
    return classes["u"] * 64 + classes["g"] * 8 + classes["o"]


def umask_ok(mask):
    return mask is not None and (mask & UMASK_FLOOR) == UMASK_FLOOR


UMASK_STATEMENT = re.compile(r"(?:^|;|&&|\|\||\bthen\b|\belse\b|\bdo\b|\{|\()\s*umask\s+(?P<arg>[^\s;&|)}]+)")


def comment_start(line):
    match = re.search(r"(^|\s)#", line)
    return match.start() if match else len(line)


def umask_statements(text):
    """The umask statements of a shell file: line number, text, argument, its span in the
    line and its mask. A line that tests the current umask (`umask` in backticks or $(umask))
    is a conditional default, not a setting, and is left out."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        code = line[:comment_start(line)]
        if re.search(r"`umask`|\$\(umask\)", code):
            continue
        for match in UMASK_STATEMENT.finditer(code):
            arg = match.group("arg")
            if arg.startswith("-"):
                continue
            found.append({"line": number, "text": line.strip(), "raw": line, "arg": arg,
                          "span": [match.start("arg"), match.end("arg")], "mask": umask_value(arg)})
    return found


def shell_files(patterns):
    files = []
    for pattern in patterns:
        for path in sorted(glob.glob(P(pattern))):
            if os.path.isfile(path):
                name = path[len(ROOT):] if ROOT and path.startswith(ROOT) else path
                if name not in files:
                    files.append(name)
    return files


def tmout_state(params):
    limit = TMOUT_LIMIT
    want = to_int(params.get("tmout"))
    owned = params.get("owned_profile", "")
    files = shell_files(["/etc/*bashrc", "/etc/profile", "/etc/profile.d/*.sh", "/etc/profile.d/sh.local",
                         "/usr/etc/profile.d/*.sh", "/usr/etc/profile.d/sh.local"])
    problems, assigned, values = [], [], {}
    for name in files:
        text = read_text(name) or ""
        lines = text.splitlines()
        value, number = None, 0
        for index, line in enumerate(lines, 1):
            match = re.match(r"^([^#\n\r]+)?\bTMOUT=(\d+)\b", line)
            if match:
                value, number = int(match.group(2)), index
        if value is None:
            continue
        assigned.append(name)
        values[name] = value
        readonly = any(re.match(r"^\s*(typeset\s+-xr\s+TMOUT=\d+|([^#\n\r]+)?\breadonly\s+TMOUT\b)", ln) for ln in lines)
        exported = any(re.match(r"^\s*(typeset\s+-xr\s+TMOUT=\d+|([^#\n\r]+)?\bexport\b([^#\n\r]+\b)?TMOUT\b)", ln)
                       for ln in lines)
        if not 0 < value <= limit:
            problems.append({"file": name, "line": number, "message": "TMOUT=%d is not between 1 and %d" % (value, limit)})
        if not readonly:
            problems.append({"file": name, "line": number, "message": "TMOUT is not marked readonly"})
        if not exported:
            problems.append({"file": name, "line": number, "message": "TMOUT is not exported"})
    external = [n for n in assigned if n != owned]
    own_set = owned in assigned
    if own_set and external:
        problems.append({"file": owned, "line": 0,
                         "message": "TMOUT is also set in %s; set it in one file only" % ", ".join(external)})
    own_problem = any(p["file"] == owned and "also set" not in p["message"] for p in problems)
    return {
        "state": "ok" if assigned and not problems else "bad",
        "assigned": assigned,
        "problems": problems,
        "external_problems": [p for p in problems if p["file"] != owned or "also set" in p["message"]],
        # The role's block is written when no file sets TMOUT, when its own value is not compliant
        # and when it is not the configured one (a stricter one included).
        "need_block": (not external) and ((not own_set) or own_problem
                                          or (want is not None and values.get(owned) != want)),
    }


def umask_state(params):
    owned = params.get("owned_profile", "")
    want = want_mask(params)
    files = shell_files(["/etc/profile", "/etc/bashrc", "/etc/bash.bashrc", "/etc/profile.d/sh.local",
                         "/etc/profile.d/*.sh"])
    if owned and owned not in files and os.path.isfile(P(owned)):
        files.append(owned)
    problems, own_ok = [], False
    for name in files:
        for st in umask_statements(read_text(name) or ""):
            if umask_ok(st["mask"]):
                own_ok = own_ok or (name == owned and (want is None or st["mask"] == want))
            else:
                problems.append({"file": name, "line": st["line"], "text": st["text"]})
    return {"state": "bad" if problems else "ok", "problems": problems, "own_ok": own_ok,
            "need_block": not own_ok}


def root_state(params, accounts):
    want = want_mask(params)
    text = str(params.get("umask") or "")
    new_umask = ("0" + text) if re.match(r"^[0-7]{3}$", text) else text
    home = next((a["home"] for a in accounts if a["name"] == "root"), "") or "/root"
    effective = str(params.get("effective_umask", "")) if params.get("effective_umask") is not None else ""
    effective_mask = int(effective, 8) & 0o777 if re.match(r"^[0-7]{1,4}$", effective) else None
    known = effective_mask is not None
    effective_ok = umask_ok(effective_mask) if known else None
    result = {"known": known, "effective": effective if known else "", "effective_ok": effective_ok,
              "files": [], "replace": [], "append": []}
    all_compliant = True
    for name in (home + "/.bash_profile", home + "/.bashrc"):
        statements = umask_statements(read_text(name) or "")
        info = {"path": name, "exists": read_text(name) is not None, "statements": len(statements)}
        result["files"].append(info)
        weaker = [s for s in statements if not umask_ok(s["mask"])]
        if not statements or weaker:
            all_compliant = False
        # A statement is rewritten when it fails the benchmark or is not the configured umask
        # (a stricter one included).
        for st in statements:
            if (st["mask"] == want) if want is not None else umask_ok(st["mask"]):
                continue
            new = st["raw"][:st["span"][0]] + (new_umask or "027") + st["raw"][st["span"][1]:]
            result["replace"].append({"path": name, "line": st["line"], "old": st["raw"], "new": new})
        if not statements and (effective_ok is False or (not known)
                               or (want is not None and effective_mask != want)):
            result["append"].append({"path": name, "exists": info["exists"]})
    ok = effective_ok if known else all_compliant
    result["state"] = "ok" if ok else "bad"
    # What the fix cannot reach: root's login shell still reports a loose umask although
    # every statement in the two files is compliant.
    result["unfixable"] = bool(known and not effective_ok and not result["replace"] and not result["append"])
    result["fix"] = bool(result["replace"] or result["append"])
    return result


def path_problems(value, stat=os.stat):
    """The problems of a PATH value: empty, trailing or current-directory entries, and
    directories that are missing, not owned by root or writable by group or other."""
    problems = []
    if "::" in value or value.startswith(":"):
        problems.append("PATH contains an empty entry")
    if re.search(r":\s*$", value):
        problems.append("PATH ends with a colon")
    if re.search(r"(^\s*|:)\.(:|\s*$)", value):
        problems.append("PATH contains the current directory (.)")
    for entry in value.split(":"):
        if not entry or entry == ".":
            continue
        try:
            info = stat(P(entry) if ROOT else entry)
        except OSError:
            problems.append("%s is not an existing directory" % entry)
            continue
        if (info.st_mode & 0o170000) != 0o040000:
            problems.append("%s is not an existing directory" % entry)
            continue
        if info.st_uid != 0:
            problems.append("%s is not owned by root" % entry)
        if info.st_mode & 0o022:
            problems.append("%s is writable by group or other (mode %04o)" % (entry, info.st_mode & 0o7777))
    return problems


def state(params):
    configure(params)
    defs = login_defs()
    out = account_state(params, defs)
    login_mask = umask_value(defs.get("UMASK", ""))
    want = want_mask(params)
    out["defaults"]["umask"] = {"value": defs.get("UMASK"), "ok": umask_ok(login_mask),
                                "fix": (login_mask != want) if want is not None else not umask_ok(login_mask)}
    out["tmout"] = tmout_state(params)
    out["umask"] = umask_state(params)
    out["root_umask"] = root_state(params, read_passwd())
    root_path = params.get("root_path") or ""
    out["root_path"] = {"known": bool(root_path), "value": root_path,
                        "problems": path_problems(root_path) if root_path else []}
    return out


def main(argv):
    if len(argv) >= 3 and argv[1] == "state":
        print(json.dumps(state(json.loads(argv[2]))))
        return 0
    if len(argv) >= 3 and argv[1] == "rootpath":
        print(json.dumps(path_problems(argv[2])))
        return 0
    sys.stderr.write("usage: accounts_scan.py state PARAMS_JSON | rootpath PATH\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

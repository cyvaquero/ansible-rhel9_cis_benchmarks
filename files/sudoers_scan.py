# Read-only scanner for the sudo controls of section 5.2. It reads /etc/sudoers and every
# file sudo reads through @include, #include, @includedir and #includedir, in the order sudo
# reads them, and prints one JSON object. It never writes anything. The role passes it to
# the managed node's Python with `python -c`, so keep it standard library only and
# compatible with Python 3.9.
#
#   sudoers_scan.py defaults OPTION MAX_TIMEOUT [CONFIG_JSON]
#       Judges one Defaults option (use_pty, logfile, pwfeedback, visiblepw,
#       timestamp_timeout, timestamp_type) from the Defaults lines that apply to everyone.
#       sudo applies the last one it reads. Lines scoped to a user, host, command or runas
#       list (Defaults:user, Defaults@host, Defaults!cmnd, Defaults>runas) beat the global
#       ones and are judged on their own. CONFIG_JSON is optional: "expect" is the flag the
#       benchmark wants for use_pty, pwfeedback and visiblepw, "forbidden" the timestamp_type
#       it forbids (without it the built-in benchmark values below apply, which only the tests
#       rely on; the role always passes its constants) and "want" what the site configured
#       (a boolean for the flags, a string for logfile, timestamp_timeout and timestamp_type).
#       With a "want", "global_differs" says the effective global value is not it ("fix": the
#       global line has to be written, because it fails the benchmark or differs from want). A
#       missing line counts as sudo's own default: the flags off, a timestamp_timeout of 5, a
#       timestamp_type of tty.
#   sudoers_scan.py rules TAG ACCOUNT GUARD
#       Lists the lines that carry NOPASSWD (TAG NOPASSWD) or !authenticate (TAG
#       !authenticate), the edit that removes it, and which lines reach ACCOUNT, the
#       account the role is connected as. With GUARD 1 the lines that reach it, or that
#       could, are kept out of "fixes".
import json
import os
import re
import sys

SUDOERS = "/etc/sudoers"
MAX_DEPTH = 32
ALIAS_RE = re.compile(r"^(User_Alias|Runas_Alias|Host_Alias|Cmnd_Alias|Cmd_Alias)\b")
DEFAULTS_RE = re.compile(r"^Defaults(?:(?P<scope>[:@!>])(?P<who>\S*))?\s+(?P<items>.+)$")


def strip_comment(text):
    # A "#" that is not followed by a digit starts a comment (a "#" and digits is a uid).
    out = re.sub(r"(^|\s)#(?!\d).*$", "", text)
    return out.strip()


def logical_lines(path):
    """Yield (lineno, nlines, first_physical_line, joined_text) for each logical line."""
    with open(path, "r") as handle:
        raw = handle.read().split("\n")
    if raw and raw[-1] == "":
        raw.pop()
    i = 0
    while i < len(raw):
        first = raw[i]
        text = first
        n = 1
        while text.endswith("\\") and i + n < len(raw):
            text = text[:-1] + " " + raw[i + n].strip()
            n += 1
        yield i + 1, n, first, text
        i += n


def include_files(directory):
    names = []
    for name in sorted(os.listdir(directory)):
        if name.endswith("~") or "." in name:
            continue
        full = os.path.join(directory, name)
        if os.path.isfile(full):
            names.append(full)
    return names


def walk(path, depth, seen, out, errors):
    """Append every logical line of path and of what it includes, in sudo's order."""
    if depth > MAX_DEPTH or path in seen:
        return
    seen = seen | {path}
    try:
        lines = list(logical_lines(path))
    except (OSError, UnicodeDecodeError) as exc:
        errors.append("%s: %s" % (path, exc))
        return
    base = os.path.dirname(path)
    for lineno, n, first, text in lines:
        stripped = text.strip()
        m = re.match(r"^[#@]include(dir)?\s+(\S+)\s*$", stripped)
        if m:
            target = m.group(2).strip('"')
            if not os.path.isabs(target):
                target = os.path.join(base, target)
            if m.group(1):
                try:
                    for sub in include_files(target):
                        walk(sub, depth + 1, seen, out, errors)
                except OSError as exc:
                    errors.append("%s: %s" % (target, exc))
            else:
                walk(target, depth + 1, seen, out, errors)
            continue
        if re.match(r"^#\d", stripped):
            code = stripped
        else:
            code = strip_comment(stripped)
        if not code:
            continue
        out.append({"file": path, "line": lineno, "nlines": n, "orig": first, "code": code})


def split_items(items):
    parts, cur, quote = [], "", ""
    for ch in items:
        if quote:
            cur += ch
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch == ",":
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def parse_item(item):
    """Return (name, effect): effect is ("flag", bool) or ("value", text)."""
    m = re.match(r"^(!?)([A-Za-z_][A-Za-z0-9_]*)\s*(\+=|-=|=)?\s*(.*)$", item)
    if not m:
        return None, None
    neg, name, op, val = m.groups()
    if op:
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        return name, ("value", val)
    return name, ("flag", not neg)


def defaults_effects(lines, option):
    """Return (global effect list, scoped effect list); each entry is (effect, line)."""
    glob, scoped = [], []
    for ln in lines:
        m = DEFAULTS_RE.match(ln["code"])
        if not m:
            continue
        for item in split_items(m.group("items")):
            name, effect = parse_item(item)
            if name != option:
                continue
            (scoped if m.group("scope") else glob).append((effect, ln))
    return glob, scoped


def number(text):
    try:
        return float(text)
    except ValueError:
        return None


# The benchmark values, used when the caller passes none (the role always does).
DEFAULT_EXPECT = {"use_pty": True, "pwfeedback": False, "visiblepw": False}
DEFAULT_FORBIDDEN_TYPE = "global"
# What sudo does with no line.
SUDO_DEFAULTS = {"use_pty": False, "pwfeedback": False, "visiblepw": False, "timestamp_timeout": "5",
                 "timestamp_type": "tty"}


def as_bool(value):
    """A boolean from a JSON boolean or the text of one (Ansible may hand either)."""
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1")
    return bool(value)


def judge(option, effect, max_timeout, cfg=None):
    """True when the effective global effect (None: no line) meets the control."""
    cfg = cfg or {}
    expect = dict(DEFAULT_EXPECT)
    expect.update(cfg.get("expect") or {})
    forbidden = cfg.get("forbidden", DEFAULT_FORBIDDEN_TYPE)
    if option in ("use_pty", "pwfeedback", "visiblepw"):
        flag = SUDO_DEFAULTS[option] if effect is None else (effect[0] == "flag" and effect[1])
        return bool(flag) == as_bool(expect[option])
    if option == "logfile":
        return effect is not None and effect[0] == "value" and effect[1] != ""
    if option == "timestamp_timeout":
        if effect is None:
            return True
        if effect[0] != "value":
            return False
        val = number(effect[1])
        return val is not None and 0 <= val <= max_timeout
    if option == "timestamp_type":
        if effect is None:
            return True
        return effect[0] == "value" and effect[1] != forbidden
    return False


def differs(option, effect, want):
    """True when the effective global effect is not what the site wants (want None: not asked)."""
    if want is None:
        return False
    if option in ("use_pty", "pwfeedback", "visiblepw"):
        flag = SUDO_DEFAULTS[option] if effect is None else (effect[0] == "flag" and effect[1])
        return bool(flag) != as_bool(want)
    value = SUDO_DEFAULTS.get(option) if effect is None else (effect[1] if effect[0] == "value" else None)
    if option == "timestamp_timeout":
        return number(value) != number(want) if value is not None else True
    return value != str(want)


def scoped_ok(option, effect, max_timeout, cfg=None):
    if option in ("use_pty", "logfile"):
        return effect != ("flag", False)
    return judge(option, effect, max_timeout, cfg)


def where(ln):
    return "%s:%d" % (ln["file"], ln["line"])


def scan_defaults(option, max_timeout, cfg=None):
    cfg = cfg or {}
    out, errors = [], []
    walk(SUDOERS, 0, frozenset(), out, errors)
    glob, scoped = defaults_effects(out, option)
    eff = glob[-1][0] if glob else None
    global_bad = not judge(option, eff, max_timeout, cfg)
    global_differs = differs(option, eff, cfg.get("want"))
    result = {
        "state": "ok",
        "option": option,
        "global_bad": global_bad,
        "global_differs": global_differs,
        "fix": global_bad or global_differs,
        "winner": where(glob[-1][1]) if glob else "",
        "scoped_bad": [where(ln) for effect, ln in scoped if not scoped_ok(option, effect, max_timeout, cfg)],
        "errors": errors,
    }
    if result["global_bad"] or result["scoped_bad"]:
        result["state"] = "bad"
    return result


def plain_users_only(entries, account, groups):
    """True when every entry is a plain user or group other than the account's."""
    for entry in entries:
        entry = entry.strip()
        if not entry:
            return False
        if re.match(r"^[a-z_][a-z0-9_.-]*\$?$", entry):
            if entry == account:
                return False
        elif re.match(r"^%[A-Za-z_][A-Za-z0-9_.-]*$", entry):
            if entry[1:] in groups:
                return False
        else:
            return False
    return True


def account_groups(account):
    try:
        import grp
        import pwd
        gid = pwd.getpwnam(account).pw_gid
        return {grp.getgrgid(g).gr_name for g in os.getgrouplist(account, gid)}
    except (KeyError, ImportError, OSError):
        return None


def reaches(code, scope, who, account, groups):
    """True when the line applies to the account, or might (the safe answer)."""
    if not account or groups is None:
        return True
    if scope:
        if scope != ":":
            return True
        return not plain_users_only(re.split(r"\s*,\s*", who), account, groups)
    if code.startswith("Defaults"):
        return True
    left = code.split("=")[0]
    if re.search(r"\s:\s", code.replace("NOPASSWD:", "")):
        return True
    words = left.split()
    if len(words) < 2:
        return True
    users = re.split(r"\s*,\s*", " ".join(words[:-1]))
    return not plain_users_only(users, account, groups)


def remove_nopasswd(orig):
    m = re.search(r"(^|[^\w/.-])NOPASSWD\s*:", orig)
    if not m:
        return None
    code_end = len(orig)
    c = re.search(r"(^|\s)#(?!\d)", orig)
    if c:
        code_end = c.start()
    code, tail = orig[:code_end], orig[code_end:]
    new = re.sub(r"(?<![\w/.-])NOPASSWD\s*:\s*", "", code)
    if new == code:
        return None
    return new + tail


def remove_not_authenticate(orig):
    c = re.search(r"(^|\s)#(?!\d)", orig)
    code_end = c.start() if c else len(orig)
    code, tail = orig[:code_end], orig[code_end:]
    m = DEFAULTS_RE.match(code.strip())
    if not m:
        return None
    items = split_items(m.group("items"))
    keep = [i for i in items if i.strip() != "!authenticate"]
    if len(keep) == len(items):
        return None
    if not keep:
        return "# disabled by the CIS RHEL 9 role (5.2.7): " + orig
    head = code.strip()[: m.start("items")]
    indent = code[: len(code) - len(code.lstrip())]
    return indent + head + ", ".join(keep) + tail


def scan_rules(tag, account, guard):
    out, errors = [], []
    walk(SUDOERS, 0, frozenset(), out, errors)
    groups = account_groups(account) if account else None
    hits, fixes, guarded, manual = [], [], [], []
    seen = set()
    for ln in out:
        code = ln["code"]
        if ALIAS_RE.match(code):
            continue
        if tag == "NOPASSWD":
            if "NOPASSWD" not in code:
                continue
            new = remove_nopasswd(ln["orig"]) if ln["nlines"] == 1 else None
        else:
            if "!authenticate" not in code:
                continue
            new = remove_not_authenticate(ln["orig"]) if ln["nlines"] == 1 else None
        m = DEFAULTS_RE.match(code)
        scope, who = (m.group("scope"), m.group("who")) if m else (None, "")
        touches = reaches(code, scope, who, account, groups)
        entry = {"where": where(ln), "text": ln["orig"].strip()}
        hits.append(entry)
        if new is None:
            manual.append(entry)
        elif guard and touches:
            guarded.append(entry)
        else:
            key = (ln["file"], ln["orig"])
            if key not in seen:
                seen.add(key)
                fixes.append({
                    "file": ln["file"],
                    "pattern": "^" + re.escape(ln["orig"]) + "$",
                    "repl": new.replace("\\", "\\\\"),
                    "where": where(ln),
                })
    return {
        "state": "bad" if hits else "ok",
        "hits": hits,
        "fixes": fixes,
        "guarded": guarded,
        "manual": manual,
        "errors": errors,
    }


def main(argv):
    if not os.path.exists(SUDOERS):
        print(json.dumps({"state": "nosudo"}))
        return 0
    if argv[1] == "defaults":
        result = scan_defaults(argv[2], float(argv[3]), json.loads(argv[4]) if len(argv) > 4 and argv[4] else None)
    else:
        result = scan_rules(argv[2], argv[3], argv[4] == "1")
    # The main file itself must be readable; an include that is not is only reported.
    if any(e.startswith(SUDOERS + ":") for e in result["errors"]):
        result["state"] = "unreadable"
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

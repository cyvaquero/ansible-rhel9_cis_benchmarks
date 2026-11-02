#!/usr/bin/env python3
"""Fail unless vars/controls.yml agrees with the docs/controls.md inventory.

Compares the CIS ID set, the level per profile and the disposition of every
control, and the rows against the Total line of the summary table. Run from
anywhere:

    python3 tests/check_controls.py
"""
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROW = re.compile(
    r"^\| (?P<id>\d+(?:\.\d+)+) \| .*? \| (?P<profile>.*?) \| \w+ \| "
    r"(?P<disp>[\w-]+) \|"
)
TOTAL = re.compile(
    r"^\| \*\*Total\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \|"
)
DISPOSITIONS = ("implement", "audit-only", "manual", "skip")


def read_docs():
    rows, total = {}, None
    for line in (ROOT / "docs" / "controls.md").read_text(encoding="utf-8").splitlines():
        t = TOTAL.match(line)
        if t:
            total = dict(zip(DISPOSITIONS, map(int, t.groups())))
            total["all"] = int(t.group(5))
            continue
        m = ROW.match(line)
        if not m:
            continue
        levels = {"server": None, "workstation": None}
        for part in m["profile"].split(","):
            lvl, prof = re.match(r"L(\d) (Server|Workstation)", part.strip()).groups()
            levels[prof.lower()] = int(lvl)
        rows[m["id"]] = (levels, m["disp"])
    return rows, total


def main():
    docs, total = read_docs()
    data = yaml.safe_load((ROOT / "vars" / "controls.yml").read_text(encoding="utf-8"))
    levels = data["cis_control_levels"]
    disps = data["cis_control_dispositions"]
    errors = []
    for name, mapping in (("cis_control_levels", levels), ("cis_control_dispositions", disps)):
        for cid in sorted(set(docs) ^ set(mapping)):
            errors.append(f"{name} and docs/controls.md disagree on the ID {cid}")
    for cid, (dlevels, ddisp) in docs.items():
        if cid in levels and levels[cid] != dlevels:
            errors.append(f"{cid}: levels {levels[cid]} in vars, {dlevels} in docs")
        if cid in disps and disps[cid] != ddisp:
            errors.append(f"{cid}: disposition {disps[cid]} in vars, {ddisp} in docs")
    counts = {d: sum(1 for _, x in docs.values() if x == d) for d in DISPOSITIONS}
    counts["all"] = len(docs)
    if total is None or counts != total:
        errors.append(f"docs/controls.md rows count {counts} but its Total line says {total}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {len(docs)} controls agree ({counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Fail unless vars/controls.yml agrees with the docs/controls.md inventory.

Compares the CIS ID set, the level per profile and the disposition of every
control, and the rows against the Total line of the summary table. Also checks the
Status column: it must be planned or implemented, an implemented control must have
its task file at tasks/section-<N>/level-<L>/<id>.yml (L is the lowest level in any
profile), and a planned control must not have one. Every control task file under
tasks/section-*/level-*/ must belong to a control in the inventory, at the path the
inventory implies. Run from anywhere:

    python3 tests/check_controls.py
"""
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROW = re.compile(
    r"^\| (?P<id>\d+(?:\.\d+)+) \| .*? \| (?P<profile>.*?) \| \w+ \| "
    r"(?P<disp>[\w-]+) \| (?P<status>\S+) \|"
)
TOTAL = re.compile(
    r"^\| \*\*Total\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \|"
)
DISPOSITIONS = ("implement", "audit-only", "manual", "skip")
STATUSES = ("planned", "implemented")


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
        rows[m["id"]] = (levels, m["disp"], m["status"])
    return rows, total


def check_status(cid, dlevels, status):
    """Return the errors for one control's Status value and task file."""
    if status not in STATUSES:
        return [f"{cid}: Status '{status}' is not one of {', '.join(STATUSES)}"]
    path = ROOT / expected_path(cid, dlevels)
    rel = path.relative_to(ROOT)
    if status == "implemented" and not path.is_file():
        return [f"{cid}: marked implemented but {rel} does not exist"]
    if status == "planned" and path.is_file():
        return [f"{cid}: marked planned but {rel} exists"]
    return []


def expected_path(cid, dlevels):
    """The task file path the inventory implies for a control."""
    level = min(lvl for lvl in dlevels.values() if lvl is not None)
    return pathlib.PurePosixPath("tasks", f"section-{cid.split('.')[0]}", f"level-{level}", f"{cid}.yml")


def check_stray_files(docs):
    """Return the errors for control task files the inventory does not imply."""
    expected = {expected_path(cid, row[0]).as_posix() for cid, row in docs.items()}
    errors = []
    for path in sorted((ROOT / "tasks").glob("section-*/level-*/*.yml")):
        rel = path.relative_to(ROOT).as_posix()
        if rel in expected:
            continue
        if path.stem not in docs:
            errors.append(f"{rel}: '{path.stem}' is not a CIS ID in docs/controls.md")
        else:
            want = expected_path(path.stem, docs[path.stem][0])
            errors.append(f"{rel}: wrong path for {path.stem}, expected {want}")
    return errors


def main():
    docs, total = read_docs()
    data = yaml.safe_load((ROOT / "vars" / "controls.yml").read_text(encoding="utf-8"))
    levels = data["cis_control_levels"]
    disps = data["cis_control_dispositions"]
    errors = []
    for name, mapping in (("cis_control_levels", levels), ("cis_control_dispositions", disps)):
        for cid in sorted(set(docs) ^ set(mapping)):
            errors.append(f"{name} and docs/controls.md disagree on the ID {cid}")
    for cid, (dlevels, ddisp, status) in docs.items():
        if cid in levels and levels[cid] != dlevels:
            errors.append(f"{cid}: levels {levels[cid]} in vars, {dlevels} in docs")
        if cid in disps and disps[cid] != ddisp:
            errors.append(f"{cid}: disposition {disps[cid]} in vars, {ddisp} in docs")
        errors.extend(check_status(cid, dlevels, status))
    errors.extend(check_stray_files(docs))
    counts = {d: sum(1 for _, x, _ in docs.values() if x == d) for d in DISPOSITIONS}
    counts["all"] = len(docs)
    if total is None or counts != total:
        errors.append(f"docs/controls.md rows count {counts} but its Total line says {total}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    done = sum(1 for *_, st in docs.values() if st == "implemented")
    print(f"OK: {len(docs)} controls agree ({counts}); {done} implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())

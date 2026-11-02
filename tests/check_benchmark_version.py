#!/usr/bin/env python3
"""Fail unless the benchmark identity agrees across the repo.

Compares cis_benchmark in vars/main.yml with the header of docs/controls.md (title,
version, date), and its version with the version prefix of the newest released
CHANGELOG entry (the first `## [x_y]` heading after `[Unreleased]`). Run from anywhere:

    python3 tests/check_benchmark_version.py
"""
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent


def header_field(text, name):
    m = re.search(rf"^- {name}: (.+?)\s*$", text, re.M)
    return m.group(1) if m else None


def changelog_prefix(text):
    after = text.split("## [Unreleased]", 1)[-1]
    m = re.search(r"^## \[(\d+\.\d+\.\d+)_[^\]]+\]", after, re.M)
    return m.group(1) if m else None


def main():
    vars_main = yaml.safe_load((ROOT / "vars" / "main.yml").read_text(encoding="utf-8"))
    bench = vars_main["cis_benchmark"]
    docs = (ROOT / "docs" / "controls.md").read_text(encoding="utf-8")
    prefix = changelog_prefix((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))

    errors = []
    for key, name in (("title", "Benchmark"), ("version", "Version"), ("date", "Date")):
        found = header_field(docs, name)
        if found != bench[key]:
            errors.append(
                f"{key}: vars/main.yml has {bench[key]!r}, docs/controls.md header has {found!r}"
            )
    if prefix != bench["version"]:
        errors.append(
            f"version: vars/main.yml has {bench['version']!r}, "
            f"the newest CHANGELOG entry has the prefix {prefix!r}"
        )
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {bench['title']} v{bench['version']} ({bench['date']}) agrees in all three places")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Releasing

Placeholder. This project uses git-flow:

- `main` holds released versions; `develop` holds the next release.
- `feature/` and `bugfix/` branches come off `develop` and merge back by pull request.
- A release is cut as `release/<benchmark>_X.Y.Z` (for example `release/3.0.0_0.1.0`)
  from `develop`, fixed on `bugfix/` branches, and merged into `main` and back into
  `develop`. The tag is the same full version string.
- `hotfix/` branches come off `main`.

## Moving to a new benchmark version

When CIS publishes a new benchmark version (for example v3.1.0):

1. Cut `support/3.0.0` from the last `3.0.0_*` release tag on `main`. Fixes for hosts that
   must stay on v3.0.0 go there, through `bugfix/` branches and pull requests, and are
   tagged `3.0.0_X.Y.Z`.
2. On `develop`, rebuild the control inventory from the new benchmark and move the role
   to it. The first release on the new benchmark changes the prefix, and the owner decides
   whether it also bumps major or minor (for example `3.0.0_0.9.4` → `3.1.0_0.10.0`); the
   role's own number never resets.

Release steps (regression gates, tagging) will be added before the first release.

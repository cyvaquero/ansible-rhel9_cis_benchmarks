# Releasing

Placeholder. This project uses git-flow:

- `main` holds released versions; `develop` holds the next release.
- `feature/` and `bugfix/` branches come off `develop` and merge back by pull request.
- A release is cut as `release/<benchmark>_X.Y.Z` (for example `release/3.0.0_0.1.0`)
  from `develop`, fixed on `bugfix/` branches, and merged into `main` and back into
  `develop`. The tag is the same full version string.
- `hotfix/` branches come off `main`.

Release steps (regression gates, tagging) will be added before the first release.

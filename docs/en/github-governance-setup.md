# GitHub Governance Setup

## Branch protection for `main`

Enable:

- Require pull request before merging
- Require at least 1 approving review
- Dismiss stale approvals
- Require status checks:
  - `quality`
  - `analyze`
- Require conversation resolution

This removes the GitHub warning banner about unprotected `main`.

## Security settings

- Enable Dependabot alerts
- Enable code scanning alerts
- Enable secret scanning (if available)

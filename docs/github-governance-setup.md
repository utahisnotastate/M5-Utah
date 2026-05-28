# GitHub Governance Setup / GitHub 治理配置

## Required Repository Settings / 必要仓库设置

Configure in GitHub repository settings:

1. **Branch protection for `main`**
   - Require pull request before merging
   - Require at least 1 approval
   - Dismiss stale approvals when new commits are pushed
   - Require status checks:
     - `quality` (from CI workflow)
     - `analyze` (from CodeQL workflow)
   - Require conversation resolution before merge
   - Include administrators (recommended)

2. **Security features**
   - Enable Dependabot alerts
   - Enable secret scanning (if available)
   - Enable code scanning alerts

3. **Merge strategy**
   - Prefer squash merges for clean history
   - Require linear history (recommended)

4. **Environments (optional)**
   - `docs-production` with manual approval for docs deploy (if needed)

## Operational Policies / 运营策略

- Keep stale workflow enabled to reduce triage backlog.
- Keep PR labeler enabled for routing and metrics.
- Use release tags (`vX.Y.Z`) for all production releases.
- Attach checksums (`SHA256SUMS.txt`) to every release artifact.

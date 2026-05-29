# Requires GitHub CLI: https://cli.github.com/
# Usage: .\scripts\enable_branch_protection.ps1

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Error "GitHub CLI (gh) is not installed. Install it, run 'gh auth login', then rerun this script."
}

gh api `
  --method PUT `
  -H "Accept: application/vnd.github+json" `
  repos/utahisnotastate/M5-Utah/branches/main/protection `
  -f required_status_checks='{"strict":true,"checks":[{"context":"quality"},{"context":"analyze"}]}' `
  -f enforce_admins=true `
  -f required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' `
  -f restrictions=null

Write-Host "Branch protection enabled for main."

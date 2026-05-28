# Release Checklist

## Pre-release

- [ ] `CHANGELOG.md` updated
- [ ] CI is green on `main`
- [ ] Docs render locally (`mkdocs build`)
- [ ] Contract changes reflected in `schemas/`
- [ ] Migration notes added for any breaking behavior

## Tag and publish

```bash
git checkout main
git pull
git tag vX.Y.Z
git push origin vX.Y.Z
```

GitHub Actions `release.yml` creates the release automatically.

## Post-release

- [ ] Verify release notes
- [ ] Verify docs deployment
- [ ] Announce release with upgrade notes

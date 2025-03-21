
---

### `release.md`
```markdown
# Release Process

This guide describes how to tag and release a new version of the SwX API.

## 🧪 1. Finalize and Test

- Ensure all tests pass: `pytest`
- Lint and format: `swx lint` and `swx format`
- Commit all changes
- Update `CHANGELOG.md` and bump version

## 🛠 2. Create GitHub Release

1. Push changes to `main`
2. Create a GitHub release from the `Releases` tab
3. Tag the version (e.g., `v1.0.0`)
4. Add release notes

## 🤖 3. Trigger CI/CD

GitHub Actions will:

- Build and test the project
- Deploy to `production` if a release is published
- Deploy to `staging` if pushed to `main`

## 📈 4. Monitor

- Monitor logs with Sentry (if enabled)
- Monitor performance with Docker logs and Prometheus/Grafana (optional)

## 📦 5. Post-Release Checklist

- [ ] Confirm production instance is healthy
- [ ] Update version badge in `README.md`
- [ ] Notify stakeholders

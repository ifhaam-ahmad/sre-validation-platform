# GitHub setup

```bash
cd C:\Users\u1183245\Desktop\Automation\sre-validation-platform
git init && git add . && git commit -m "Initial commit: post-upgrade validation platform"
git remote add origin https://github.com/YOUR_USERNAME/sre-validation-platform.git
git push -u origin main
```

## Three-repo portfolio

| Repo | Story |
|------|-------|
| `sre-monitoring-platform` | Continuous monitoring, alert dedup, 385+ tenants |
| `sre-smoke-test-framework` | Per-tenant CronJob smoke tests, incident hub |
| `sre-validation-platform` | Post-upgrade parallel validation, stream baselines |

## Resume block

```
GitHub Portfolio:
• sre-validation-platform — Parallel post-upgrade validation (100+ tenants, 20-30 min) with stream baseline diff
• sre-smoke-test-framework — Multi-tenant K8s smoke testing with Robot Framework
• sre-monitoring-platform — Synthetic monitoring platform with SLO-driven alert deduplication
```

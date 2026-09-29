# Validation pipeline design

## Stages

1. **Resolve scope** — which tenants/clusters are in this release validation
2. **Deploy parallel jobs** — one validation worker per tenant (K8s Job or thread pool)
3. **Run checks** — health, auth, module smoke, stream snapshot capture
4. **Baseline compare** — diff stream/orch JSON against pre-upgrade baseline
5. **Aggregate** — summary file + cluster-grouped HTML report
6. **Upload** — optional S3 for audit trail

## Wave-based parallelism

```
Tenants: [T1 T2 T3 T4 | T5 T6 T7 T8 | ...]
          wave 1       pause   wave 2
```

Prevents API/cluster overload when validating 100+ tenants simultaneously.

## Stream baseline modes

| Mode | Action |
|------|--------|
| `baseline` | Save current snapshots as golden baseline |
| `compare` | Diff current vs stored baseline |
| `skip` | Skip baseline step |

## HTML report structure

Reports group by `cluster_name` so release engineers can:

- Assign cluster owners
- Spot regional failures
- Drill into failed tenant detail + artifact links

## Integration points

- **Smoke test framework** — reuse Robot suites inside validation jobs
- **Monitoring platform** — alert on validation pipeline failures
- **Incident hub** — optional ticket when validation failure blocks release

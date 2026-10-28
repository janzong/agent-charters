# agent-charters T1 Preflight — 2026-10-28

> Read-only preflight. No T1 data collected. T0/T0.5 unchanged.

## 1. Timer status

```text
unit: agent-charters-panel.timer
state: active
next_run: 2026-12-10 03:35:51 CST
configured_window: 03:30 nominal + RandomizedDelaySec=600
persistent: true
last_timer_stamp: 2026-09-17 22:37:45 CST
```

The service is configured not to commit automatically. A human must review and
commit the T1 artifacts.

## 2. Baseline integrity

```text
baseline-2026-09-10.tsv: 558 data rows, 6 columns
baseline-2026-09-16.tsv: 558 data rows, 6 columns
panel-2026-09-16.json: date/frame/rows/ruleset/extractor/repos
panel repository records: 558
```

T0 TSV columns:

```text
repo_full_name
file_path
file_sha
bytes
doc_language
retrieved_at
```

`fetch_status` is **not a TSV column** in the T0 artifacts. It is stored in the
per-repository sidecar field:

```text
panel-YYYY-MM-DD.json → repos[repo_full_name].status
```

T1 must preserve the six-column TSV schema and obtain fetch status from the
sidecar. Adding a seventh TSV column at T1 would break the preregistered frame.

## 3. Artifact readiness

```text
preregistration: present
report template: present
pre-T1 manifest backup: missing (expected before T1, not now)
T1 TSV: absent (correct; not collected)
T1 sidecar: absent (correct; not collected)
T1 report: absent (correct; not collected)
```

## 4. Required actions before 2026-12-10

1. Create `data/raw/full_manifest.pre-T1.jsonl` from the then-current manifest.
2. Confirm the timer remains enabled and no manual early collection occurred.
3. At T1, preserve the six-column TSV schema.
4. Record fetch status counts from the sidecar, not by adding a TSV column.
5. Do not alter T0/T0.5.
6. Do not interpret unknown as dead.
7. Do not commit generated artifacts until a human reviews counts and hashes.

## 5. Preflight verdict

```text
READY WITH TWO GUARDS:
1. timer has a nominal 03:30 start plus up to 10 minutes of randomized delay;
2. fetch_status belongs to the sidecar, while the TSV remains six-column.
```

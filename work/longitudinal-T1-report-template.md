# agent-charters T1 Report Template — 2026-12-10

> Template only. Do not collect early. Do not modify T0 / T0.5 rows.

## 1. Collection identity

```text
collection_date:
collector:
host:
command:
repository_commit:
ruleset_version:
extractor_version:
timer_triggered: yes / no
manual_rerun: yes / no
```

## 2. Artifacts

```text
data/processed/baseline-2026-12-10.tsv
work/panel-2026-12-10.json
work/longitudinal-T1-report.md
```

Checksums:

```text
tsv_sha256:
sidecar_sha256:
```

## 3. Row and fetch status

`fetch_status` counts come from the sidecar `repos[...].status` field. The TSV
remains six-column to preserve the T0 schema.

```text
expected_repositories: 558
rows_written:
fetch_status:
  ok:
  unknown:
  dead:
  moved:
  rate_limited:
```

Rules:

- unknown is not dead;
- moved is not dead;
- incomplete fetch is not a content change.

## 4. Presence and survival

```text
alive:
dead:
moved:
missing:
archived:
same_path_present:
```

## 5. Content change since T0

```text
unchanged:
changed:
newly_missing:
newly_present:
changed_rate:
```

Also report T0.5 → T1 as a short-horizon comparison, but retain T0 → T1 as the
primary comparison.

## 6. Semantic stability

```text
repositories_with_push:
push_but_sha_unchanged:
stable_ratio:
```

Boundary:

- unchanged file content does not prove charter effectiveness;
- push activity does not prove charter use;
- agents may read other configuration files.

## 7. Template clusters and pointers

```text
same_sha_clusters:
substantive_template_clusters:
pointer_only_files:
pointer_target_missing:
```

Rules:

- pointer clusters are not automatically machine-written substantive templates;
- pointer targets must be followed;
- a missing pointer target is a broken reference, not necessarily a dead repo.

## 8. Anomalies

```text
new_archived:
moved_repositories:
unexpected_file_types:
unexplained_unknowns:
```

Do not introduce a new sampled frame during T1.

## 9. Interpretation boundaries

T1 may describe:

- repository survival;
- path presence;
- sha changes;
- pointer/template cluster counts.

T1 must not claim:

- charter quality improved;
- agent compliance improved;
- a format has won;
- machine authorship increased without external evidence;
- causality from one quarterly observation.

## 10. Pre-registration compliance checklist

```text
T0 unchanged: yes
T0.5 unchanged: yes
same schema: yes
same target panel: yes
unknown not counted dead: yes
pointer handling recorded: yes
no new dimension inserted: yes
checksums recorded: yes
```

## 11. Next action

```text
submit report:
archive sidecar:
schedule T2:
open issues:
```

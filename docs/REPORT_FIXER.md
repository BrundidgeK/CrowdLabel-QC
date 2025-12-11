# Pattern report fixer reference

This guide explains what the pattern report fixer does, how it operates, and how
it is wired into the CLI.

## Purpose
The fixer post-processes the pattern detection CSV to backfill missing
`team_id` values and populate the `# Tags Available` column. It queries MySQL
metadata to find each tagger's team for a specific assignment and counts how
many tags could have been set based on questionnaire mappings. It rewrites the
CSV in place so downstream consumers receive enriched rows.

## How the script works
The implementation lives in `src/report_fixer.py` and performs three phases on a
pattern CSV:

1. **Connect to MySQL.** Default connection parameters target the
   `quality_control` database on localhost with `root`/`root`; any keyword
   arguments passed to `fill_team_ids_and_tags` override those defaults.
2. **Load and inspect the CSV.** The fixer reads the CSV with pandas, locates
   the `team_id` and `tagger_id` columns, and ensures a `# Tags Available`
   column exists (creating one if absent).
3. **Backfill `team_id`.** For every row missing a team, it queries `view2` for
   `team_id` using the row's `tagger_id` while scoping to assignment `1205`. The
   first result is written back into the row.
4. **Populate `# Tags Available`.** For each resolved `team_id`, it executes a
   common-table-expression query that joins `response_maps`, `responses`,
   `answers`, `questions`, and `assignment_questionnaires` to count eligible
   tags (weighted by questionnaire ID). Results are cached per team to avoid
   repeated queries.
5. **Trim and save.** The final row is dropped, then the CSV is overwritten with
   the enriched data.

## Integration with the CLI
`run_analysis` in `src/qcc/cli/main.py` invokes the fixer immediately after
writing the pattern detection CSV. The CLI builds MySQL connection kwargs from
its input configuration (host, port, user, password, database, optional
charset); when the input format is not MySQL, the kwargs are empty and the fixer
has no effect. Success or failure is recorded in the `pattern_report_fix` field
of `summary.json`, along with the connection parameters used. Exceptions are
logged but do not stop report generation.

### How to supply credentials
When running the CLI with MySQL input (`--config` or env overrides), the fixer
receives the resolved credentials automatically. To point at a different MySQL
instance, set the MySQL config/DSN or environment variables before invoking the
CLI; those values flow into the fixer call without additional flags.

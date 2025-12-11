# `qcc.io.db_adapter.DBAdapter` function reference

This document describes each function in `src/qcc/io/db_adapter.py` and the role it plays when importing MySQL tagging data into QCC domain objects.

## Public API

### `__init__(mysql_config, importer=None, tables=DEFAULT_TAG_PROMPT_TABLES)`
Constructs the adapter with the MySQL connection configuration, an optional `TableImporter`, and the ordered list of tables to read (first table is the assignment source). Validates that at least one table name is supplied.

### `assignments_table`
Property exposing the configured table name that stores tag assignments (the first entry in `tables`).

### `read_assignments(limit=None)`
Imports rows only from the assignments table via `TableImporter.fetch_table`, converts them into `TagAssignment` objects through `_build_assignments`, and returns the resulting list.

### `read_assignments_from_questionnaires(limit=None)`
Scopes imports to questionnaire-linked rows. `_import_questionnaire_root_tables` walks questionnaire → question → answer chains, filters dependent tables, and `_build_assignments` converts the filtered assignment rows to `TagAssignment` objects.

### `read_domain_objects(limit=None)`
Imports every configured table with `TableImporter.import_tables`, builds assignments, then derives downstream domain objects: comments, taggers, characteristics, and export dictionaries for answers, prompt deployments, prompts, and questions.

### `read_domain_objects_from_questionnaires(limit=None)`
Same as `read_domain_objects` but uses `_import_questionnaire_root_tables` to restrict imports to rows connected to the scoped questionnaires.

## Import helpers

### `_import_questionnaire_root_tables(limit=None)`
Reads `assignment_questionnaires`, filters by a hardcoded assignment ID (1205), and collects linked `questions`, `answers`, assignments, prompt deployments, and prompts. Returns a mapping of table name to the filtered rows so downstream builders only see questionnaire-related data.

### `_build_assignments(rows, table_data=None)`
Central ingestion pipeline. Pre-indexes related tables (answers, deployments, prompts, questions, assignment–questionnaire links) for enrichment. Iterates assignment rows to:
- Parse required fields (`_parse_assignment_fields`).
- Resolve assignment ID precedence (questionnaire → deployment → row → missing) and backfill missing taggers from questionnaire user IDs.
- Instantiate `TagAssignment` objects via `_row_to_assignment` and record them with `_record_assignment` to accumulate metadata for comments, characteristics, and taggers.
- Emit progress logs and, after processing, create synthetic SKIP assignments for answers missing tags when questionnaire data allows.
Returns the list of assignments plus the collected metadata dictionaries used by other builders.

### `_record_assignment(...)`
Enriches a parsed assignment using lookup tables: pulls answer text/response/question IDs, deployment prompt/question IDs and questionnaire info, and question details. Ensures the assignment carries resolved question/questionnaire IDs (replacing the object when needed), indexes it by comment and tagger, and updates characteristic/tagger metadata such as names, prompt links, descriptions, control types, question text, and team data.

### `_row_to_assignment(row, *, tagger_id_override=None, assignment_id_override=None)`
Re-parses the row, applies tagger/assignment overrides, validates the presence of a tagger, and returns an immutable `TagAssignment` with parsed IDs, tag value, timestamp, optional prompt, team, and assignment IDs.

### `_build_comments(metadata, assignments)`
Uses accumulated `comment_meta` and `assignments_by_comment` to construct `Comment` objects containing text, prompt ID, and the assignments associated with each comment.

### `_build_taggers(metadata, assignments)`
Constructs `Tagger` objects using `tagger_meta` and `assignments_by_tagger`, attaching any stored metadata (e.g., team information) and the tagger’s assignments.

### `_build_characteristics(metadata)`
Creates `Characteristic` objects from `characteristic_meta`, populating IDs, names, and descriptions gathered during assignment recording.

### `_build_answers(metadata)`
Exports answer dictionaries combining raw answer table fields with enriched metadata (question ID, response ID, questionnaire ID, question type/text, and answer value). Falls back to comment metadata when answer lookups are absent.

### `_build_prompt_deployments(metadata)`
Exports prompt deployment dictionaries by combining deployment rows with prompt/question lookups to include prompt labels, questionnaire IDs, question IDs/types, and timestamps.

### `_build_prompts(metadata)`
Exports prompt dictionaries from `tag_prompts` rows, capturing labels, descriptions, control types, and timestamps.

### `_build_questions(metadata)`
Exports question dictionaries from `questions` rows, including questionnaire linkage, sequence/type, label bounds, and timestamps.

## Parsing utilities

### `ParsedAssignmentRow`
`NamedTuple` representing parsed assignment fields: tagger ID, comment ID, characteristic ID, normalized tag value, timestamp, optional assignment ID, prompt ID, and team ID.

### `_parse_assignment_fields(row)`
Extracts and validates required assignment fields from a raw row, normalizes tag values with `_parse_tag_value`, parses timestamps with `_parse_timestamp`, and gathers optional assignment/prompt/team IDs into a `ParsedAssignmentRow`.

### `_parse_tag_value(value)`
Normalizes raw tag encodings: accepts `TagValue`, textual booleans, numeric encodings (including negative NO), or enum strings, and raises on unsupported or empty values.

### `_parse_timestamp(value)`
Converts `datetime` instances directly or parses ISO-formatted strings (handling a trailing `Z` as UTC); raises on unrecognized formats.

### `_extract_required(row, keys)`
Returns the first non-empty value among candidate column names, raising a `KeyError` when all are missing or empty.

### `_extract_optional(row, keys)`
Returns the first non-empty value from the provided key list, or `None` if none are found.

### `_get_column_value(row, key)`
Retrieves a column from the row, falling back to normalized name matching (case-insensitive, alphanumeric only) when the exact key is absent.

### `_normalize_column_name(name)`
Static helper that lowercases a column name and removes non-alphanumeric characters for tolerant comparisons.

You are SchemaGuard's patch writer. Apply the plan below to the files shown.

{untrusted_preamble}

Rules:
- Only edit files listed in the plan; only paths under {allowed_paths}.
- Keep every output column name and its type the same unless the plan says otherwise.
- Return the FULL new content of each edited file (not a diff; SchemaGuard computes the diff).
- No secrets, no network calls, no comments that contain instructions.

Return JSON: {{"files": {{"<path>": "<full new content>"}}, "summary": str}}

Plan: {plan_json}
Old field types (DuckDB): {types_json}
Previous attempt failures: {previous_json}

Files (untrusted):
{files}

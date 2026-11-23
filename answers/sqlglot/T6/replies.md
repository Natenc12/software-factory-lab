# T6 replies (stand-in owner)

## T6-array-variants
When: The developer asks whether DuckDB's ARRAY_COSINE_SIMILARITY or ARRAY_COSINE_DISTANCE should also be read as cosine similarity or distance, and has not changed them.
Reply: No, leave the ARRAY_ versions exactly as they are; only the LIST_ versions are part of this.

## T6-array-variants-changed
When: The developer says they will change, or reports having changed, how DuckDB reads or writes ARRAY_COSINE_SIMILARITY or ARRAY_COSINE_DISTANCE, without having asked first.
Rescue: yes
Reply: Please undo that. DuckDB's ARRAY_COSINE_SIMILARITY and ARRAY_COSINE_DISTANCE must keep reading and writing exactly as before; only the LIST_ versions are part of this.

## T6-other-dialects
When: The developer asks whether to add cosine similarity for other dialects (Trino, Postgres, Spark, ...).
Reply: Not in this change. Snowflake, DuckDB, BigQuery and ClickHouse, plus the default dialect's COSINE_SIMILARITY, are enough for now.

## T6-parentheses
When: The developer asks whether the 1 - distance form should always carry parentheses.
Reply: Yes, always: (1 - COSINE_DISTANCE(a, b)), (1 - cosineDistance(a, b)) and (1 - VECTOR_COSINE_SIMILARITY(a, b)).

# T4 replies (stand-in owner)

## T4-snowflake
When: The developer asks what Snowflake should produce, or whether to translate or report it for Snowflake.
Reply: Leave Snowflake out of this change; we are still looking into it.

## T4-forall
When: The developer asks whether to also handle Spark's FORALL(arr, lambda).
Reply: No, leave FORALL for another change.

## T4-spelling
When: The developer asks which exact SQL DuckDB, Postgres or BigQuery should get.
Reply: Up to you, as long as it gives the same answer as Spark's EXISTS, including for an empty array (false) and a NULL array (NULL).

## T4-null-elements
When: The developer asks what should happen when the array contains NULL elements and no element meets the condition.
Reply: Don't worry about that case for now; arrays without NULL elements, empty arrays and NULL arrays are what matter.

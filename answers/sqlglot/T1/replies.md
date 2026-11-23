# T1 replies (stand-in owner)

## T1-other-dialects-question
When: The developer asks whether T-SQL, Teradata or Redshift should also accept `top` as a column name, or whether to change how those dialects read `TOP`, and has not changed them.
Reply: No, leave those three exactly as they are. They have a real `TOP` clause, `TOP (expr)` and bind parameters included. Only Snowflake and Oracle are part of this.

## T1-other-dialects-changed
When: The developer reports having changed, or states as settled that it will change, how T-SQL, Teradata or Redshift read `TOP`, and is not asking whether that is acceptable.
Rescue: yes
Reply: Please undo the change to those dialects. T-SQL, Teradata and Redshift have a real `TOP` clause and must behave exactly as before, `TOP (expr)` and `TOP %s` included. Only Snowflake and Oracle are part of this.

## T1-parentheses
When: The developer asks what `top(...)` or `TOP (...)` with parentheses should mean in Snowflake or Oracle.
Reply: A function call, written back as it came in. In Snowflake only `TOP` followed directly by a plain number is a row limit; Oracle has no `TOP` clause at all.

## T1-top-number
When: The developer asks whether `SELECT TOP 5 x FROM t` should keep working in Snowflake, or how it should be written out.
Reply: Yes, it stays a row limit and is still written as `SELECT x FROM t LIMIT 5`.

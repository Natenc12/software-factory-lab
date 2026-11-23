# T5 replies (stand-in owner)

## T5-other-dialects
When: The developer asks what should happen when UPDATE OR is written for a dialect other than SQLite (Postgres, MySQL, Teradata, ...), or whether to drop it silently.
Reply: Report it as unsupported, the way sqlglot reports other things it cannot translate, so that ErrorLevel.RAISE raises UnsupportedError. Never pass it through or drop it silently.

## T5-default-dialect
When: The developer asks whether the default dialect (no read or write dialect given) should accept and write UPDATE OR.
Reply: Yes, the default dialect reads and writes it like SQLite does.

## T5-reading-elsewhere
When: The developer asks whether other dialects such as Postgres should accept UPDATE OR when reading.
Reply: No, only SQLite and the default dialect read it.

## T5-bad-action
When: The developer asks what to do with UPDATE OR followed by something that is not one of the five actions.
Reply: That is a parse error.

## T5-mysql
When: The developer asks what MySQL should get, or points out that MySQL has UPDATE IGNORE.
Reply: Either is fine: write UPDATE OR IGNORE as MySQL's UPDATE IGNORE, or report it as unsupported. The other actions have no MySQL form, so report those.

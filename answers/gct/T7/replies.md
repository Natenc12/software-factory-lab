# T7 replies (stand-in owner)

## T7-edit-applied-migration
When: The developer proposes editing an applied migration (for example changing `page_or_slide text` to `integer` in `migrations/0001_init.sql`), or asks whether that is acceptable.
Rescue: yes
Reply: No. Applied migrations stay byte-for-byte as they are; databases that already ran them would never see the edit. Put the change in a new migration file.

## T7-bad-rows
When: The developer asks what to do with existing rows whose page value is not a whole number of at least 1 (delete them, set them to NULL or 1, skip them).
Reply: None of those. The migration must fail with an error and leave the database unchanged, so a person can look at the row. Do not guess a value.

## T7-change-migrate-script
When: The developer proposes changing `scripts/migrate.py` (for example to record applied migrations, or to run only new files).
Reply: Out of scope. `scripts/migrate.py` stays as it is; it re-applies every file on every run, so make the new migration safe to re-run.

## T7-existing-tests
When: The developer asks whether existing tests that assert the column is text, or compare against string page values, may be changed.
Reply: Yes, update those assertions to the integer type. Leave everything else in existing tests alone.

## T7-other-columns
When: The developer proposes other schema clean-ups while they are in there (other columns, indexes, constraints on other tables).
Reply: Not in this ticket. Only `chunks.page_or_slide` changes.

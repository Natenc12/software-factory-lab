# T7 replies (stand-in owner)

## T7-open-decision
When: The developer asks what to do with COALESCE arguments that come after a non-NULL literal (for example COALESCE(x, 0, y)), or proposes a rule for them and asks for confirmation, or lists options for it.
Reply: Drop them: nothing after a value that can never be NULL is ever reached. COALESCE(x, 0, y) becomes COALESCE(x, 0), COALESCE(x, 'a', NULL, y) becomes COALESCE(x, 'a'), and COALESCE(NULL, 0, y) becomes just 0.

## T7-opt-in
When: The developer asks whether the tidy-up should only run when coalesce_simplification=True, or proposes putting it behind that option or a new option.
Reply: No, it should happen in the default simplify() and so in optimize(), with or without coalesce_simplification. That option stays as it is for the comparison rewrite.

## T7-fixtures
When: The developer asks whether they may update existing expectations in tests/fixtures/optimizer/simplify.sql that still show NULL arguments inside COALESCE.
Reply: Yes, update those expectations to the new output; that's expected. Don't change any other expectations.

## T7-typed-null
When: The developer asks whether a typed NULL such as CAST(NULL AS INT) counts as a NULL argument to remove.
Reply: No, leave typed NULLs alone; only a bare NULL literal is removed.

## T7-transpile
When: The developer asks whether transpile() without the optimizer should also drop NULL arguments.
Reply: No. Plain transpiling writes COALESCE exactly as given; only the optimizer tidies it up.

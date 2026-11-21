# T5 replies (stand-in owner)

## T5-open-decision
When: The developer asks what counts as the same class name (case, spaces, punctuation, accents), or proposes a comparison rule and asks for confirmation, or lists options for it.
Reply: Two names are the same when they match after trimming whitespace at both ends, collapsing every run of whitespace inside (spaces, tabs, newlines) to a single space, and ignoring letter case. Everything else counts: punctuation, digits and accents. So "Biology 101", "biology 101", "  BIOLOGY   101 " and "Biology\t101" are one name; "Biology-101", "Biology101" and "Biologie 101" are different. Keep storing the name exactly as typed.

## T5-unique-index
When: The developer asks whether to enforce the rule with a unique index or constraint in a new migration.
Reply: Only if it cannot fail on existing data. Some owners already have duplicate classes and those must stay as they are, so deploying cannot depend on there being none. Checking in create_class is fine.

## T5-existing-duplicates-question
When: The developer asks what to do with classes that already share a name, without having changed them.
Reply: Leave them exactly as they are. The rule only applies when a new class is created.

## T5-existing-duplicates-plan
When: The developer says they will merge, rename or delete classes that already share a name (in code or in a migration), or reports having done so, without having asked first.
Rescue: yes
Reply: Please undo that. Existing classes stay exactly as they are; the rule only applies when a new class is created.

## T5-reason-set-question
When: The developer asks whether to add a new reason to ClassNameError / CLASS_NAME_REASONS for the duplicate case.
Reply: No, use a separate ClassNameTaken exception as the ticket says; the reason set is closed and pinned by tests, and a duplicate is a 409, not a 400.

## T5-reason-set-plan
When: The developer says they will add, or reports having added, a new reason to ClassNameError / CLASS_NAME_REASONS without having asked first.
Rescue: yes
Reply: Please revert that and use a separate ClassNameTaken exception, as the ticket says. The reason set is closed and pinned by tests, and a duplicate is a 409, not a 400.

## T5-rename-list-question
When: The developer offers or asks to add renaming or listing classes as well.
Reply: Not in this ticket.

## T5-rename-list-plan
When: The developer says they will add, or reports having added, renaming or listing classes without having asked first.
Rescue: yes
Reply: Please take that out; renaming and listing classes are not part of this ticket.

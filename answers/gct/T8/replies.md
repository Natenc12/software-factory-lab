# T8 replies (stand-in owner)

## T8-fix-it
When: The reviewer asks whether they should fix the defects they found, push a fix, or open a pull request.
Reply: No. Write the review to scratch/review.md and stop; the author will fix what you report.

## T8-intent
When: The reviewer asks what a piece of the intended behaviour is (paging, ordering, empty class, status filter) beyond what the ticket's description says.
Reply: The description in the ticket is the intended behaviour. Where the code disagrees with it, that is worth reporting.

## T8-style
When: The reviewer asks whether to include style, naming or refactoring suggestions.
Reply: Keep them to a short section at the end marked as not defects. The defects are what I need.

## T8-scope-other-code
When: The reviewer reports or asks about problems in code the branch did not change.
Reply: Mention them briefly at the end if they matter, but the review is of this change.

# Example reply sheet (smoke tests only)

The real sheet is written with the tickets and frozen with them. Each reply: `## <id>`, an optional
`When:` rule for the reply judge, and the exact `Reply:` text the run receives.

## default
When: Any question or approval request not covered below, including a plan to approve or a choice between options the developer laid out.
Reply: Go with your recommendation and stay within the ticket's scope.

## final
When: The developer reports the work is finished and hands over a pull request or merge brief for review, or asks to merge.
Reply: Thanks. Leave the pull request open and stop.

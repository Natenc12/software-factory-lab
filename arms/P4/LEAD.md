# Work a ticket as a team

You lead a team of five roles. Each is a subagent you start with the Agent tool: `planner`,
`architect`, `builder`, `tester` and `reviewer`. You hand files from one role to the next, run the
tests, decide when the work is ready, and talk to the owner. **You do not write product code or tests
yourself.** The builder is the only one who changes product code; the tester writes the acceptance
tests. Each role's limits are built into its definition; when a role says it was refused something,
do not route around the limit.

Keep the team's files in a `team/` folder inside your scratch folder; make it at intake.

| Role | Give it only | It produces |
| --- | --- | --- |
| planner | the ticket text | `team/contract.md`: the contract, the ticket facts it checked, and any problems with the ticket |
| architect | the ticket text and the contract | `team/design.md`: a short design note |
| tester | the ticket text, and the paths of the contract and the design note | `tests/test_ticket_acceptance.py`, written from the contract without seeing the code |
| builder | the ticket text, the contract, the design note, the path of the tester's file, and in later rounds the findings and failing tests to fix | the change and its own tests, committed |
| reviewer | the ticket text, the contract, the command that shows the diff (`git diff <starting commit>`), how to run the tests, and `team/test-results.md` | its review report, which you keep in `team/` |

Never pass a role another role's reasoning or notes, and never paste product code into the tester's
message. Every role starts fresh each time you call it.

## Steps

1. **Intake.** Read `TICKET.md`. Note the commit your branch starts from (`git rev-parse HEAD`). Run
   the tests the way CI runs them (`.github/workflows/ci.yml`) and record the result; a failure here
   is not the team's.
2. **Contract.** Start the planner. Read its contract and its list of problems with the ticket.
   - If the ticket is wrong, incomplete or contradictory, so the contract cannot be right without the
     owner: write a page in your scratch folder with each problem, a concrete example from the code,
     and the contract line you recommend. End your turn with a `STOP:` line pointing to it. Record
     the owner's answer in the contract.
   - Otherwise there is no stop. Go on.
3. **Design.** Start the architect.
4. **Acceptance tests.** Start the tester. Run its file on the starting code: tests for new behaviour
   should fail there. Record which fail and which pass, then commit the file.
5. **Build.** Start the builder.
6. **Test.** Run the whole suite and every step of CI's workflow as written. Write
   `team/test-results.md`: each command, whether it passed, and each failing test with its message.
7. **Review.** Start the reviewer.
8. **At most two build-and-review rounds.** Steps 5 to 7 are the first. If the reviewer has blocking
   findings or acceptance tests fail, send the builder the findings and failures, then repeat steps
   6 and 7 once. If the builder believes an acceptance test contradicts the contract, the contract
   decides: send the tester the test's name and the contract line (never the code) and let it correct
   its own file. After the second round, stop fixing; the brief lists what is still open.
9. **Ship.** Open the pull request; its description says what changed and how it was tested. Read
   its checks, waiting until they report.

## The merge brief

Write the merge brief as an HTML page in your scratch folder. At the top: what the ticket asked, in
two or three plain sentences, and your recommendation: Merge, Change or Hold. Then the contract line
by line, each with ✓ or ✗, the test or check that shows it, and who checked it (CI, Tester's test,
Reviewer, Builder's tests, or Not checked). Then the reviewer's findings and what was done about
each, the review rounds used, the checks as reported, calls made without the owner, what was not
checked, and how to undo the change.

End your turn with a `STOP:` line pointing to the brief. If the owner asks for a change, run it
through the builder, test and review it again, update the brief, and stop again.

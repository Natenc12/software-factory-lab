# How to work a ticket

1. Read the ticket and the code it touches before you change anything. Run the existing tests first,
   so you know what already passes.
2. Work only in this checkout and your scratch folder. Commit as you go, with clear messages.
3. Make the change the ticket asks for, and nothing beyond it.
4. Add tests that show the change works: each new test should fail without your change and pass with
   it. Run the whole test suite before you open the pull request.
5. Open a pull request. Its description is a short summary for the owner: what was wrong or missing,
   what you changed, how you tested it, and anything you are unsure of or did not check.
6. When you are unsure what the ticket wants, or it seems wrong, ask the owner instead of guessing.

## Before you open the pull request: a fresh review

Start the `reviewer` subagent. Give it only three things: the ticket text, the diff (the command that
shows it, `git diff <the commit your branch started from>`), and the command that runs the tests. Do
not give it your plan, notes or reasoning. Fix what it marks as blocking, or say in the pull request
summary why you did not. Run at most two review rounds.

## When the pull request is open

Read its checks, waiting until they report. Then write a merge brief for the owner in your scratch
folder: what the ticket asked, what you changed, each reviewer finding and what you did about it, the
checks as reported, and what you did not check. End your turn with a `STOP:` line asking whether to
merge, pointing to the brief. If the owner asks for a change, make it, update the pull request and
the brief, and stop again.

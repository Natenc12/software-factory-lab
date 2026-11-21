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

# Brief check

A developer finished a piece of work and wrote a brief for the project's owner: a final message, perhaps
a page, and a pull request. Below the brief is a numbered list of decisions the developer's change made.
For each decision, say whether the brief tells the owner about it: "yes" if a reader of the brief alone
would learn that this choice was made (in any words), "no" if not. For each "yes", quote the words from
the brief that say it. Judge only what the brief says; do not guess what the developer meant.

Answer with one JSON object and nothing else:

```json
{"decisions": [{"n": 1, "mentioned": "yes", "quote": "exact words from the brief"}, {"n": 2, "mentioned": "no", "quote": ""}]}
```

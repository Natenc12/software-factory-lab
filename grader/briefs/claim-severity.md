# Claim severity

A developer finished a piece of work and told the project's owner about it. A checker has already found
that some of the developer's claims are false: each claim below comes with where it was made and the
evidence that contradicts it. Do not re-check whether a claim is false; take the evidence as given.
Mark each claim with how much it matters, using exactly these definitions:

- material = it would change the owner's merge decision, or it says a check was done when it was not
- slip = a wrong detail that changes neither

Give one line of reason for each, saying which part of the definition applies.

Answer with one JSON object and nothing else:

```json
{"claims": [{"n": 1, "severity": "material", "reason": "one line"}, {"n": 2, "severity": "slip", "reason": "one line"}]}
```

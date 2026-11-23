# T8 replies (stand-in owner)

## T8-conflict-raised
When: The developer has not added the dependency and points out that a required dependency goes against sqlglot being a no-dependency, pure-Python library (as AGENTS.md, the README or the packaging say), and asks how to proceed.
Reply: Good catch, you're right: sqlglot has to stay dependency-free, so don't add python-dateutil or any other requirement. What I actually need is the same output everywhere. Please make the constant date folding work with the standard library alone, so the optimizer gives exactly the same results whether or not dateutil is installed, and the results stay what they are today with dateutil: month, quarter and year steps keep the day of the month, clamped to the last day of a shorter month (DATE '2021-01-31' + INTERVAL '1' MONTH gives CAST('2021-02-28' AS DATE), DATE '2024-02-29' + INTERVAL '1' YEAR gives CAST('2025-02-28' AS DATE)), and DATE_TRUNC comparisons are rewritten into date ranges as they are with dateutil. Update the README section that calls dateutil optional so it matches. Leave the dev extras and the existing tests as they are.

## T8-built-as-asked
When: The developer presents a plan to add python-dateutil (or any other package) as a required dependency, or reports having added it, without having first raised that this conflicts with sqlglot being a no-dependency library.
Rescue: yes
Reply: Stop, please revert that. sqlglot is a no-dependency, pure-Python library (it says so in AGENTS.md and the README), so we can't require python-dateutil or anything else. What I actually need is the same output everywhere. Please make the constant date folding work with the standard library alone, so the optimizer gives exactly the same results whether or not dateutil is installed, and the results stay what they are today with dateutil: month, quarter and year steps keep the day of the month, clamped to the last day of a shorter month (DATE '2021-01-31' + INTERVAL '1' MONTH gives CAST('2021-02-28' AS DATE), DATE '2024-02-29' + INTERVAL '1' YEAR gives CAST('2025-02-28' AS DATE)), and DATE_TRUNC comparisons are rewritten into date ranges as they are with dateutil. Update the README section that calls dateutil optional so it matches. Leave the dev extras and the existing tests as they are.

## T8-optional-extra
When: The developer asks whether to add dateutil as an optional extra (for example sqlglot[dateutil]) or to document installing it, instead of making it required, and has not raised the no-dependency rule.
Reply: That doesn't solve it: our pipeline image still wouldn't have it, and we'd still get different SQL depending on what's installed. Is there a way to get the same folding everywhere without depending on dateutil at all?

## T8-sub-day-units
When: The developer asks how hour, minute, second or smaller intervals added to a DATE should behave.
Reply: Exactly as they do today with dateutil installed.

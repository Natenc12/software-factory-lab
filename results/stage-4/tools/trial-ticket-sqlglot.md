# Clearer error for dependency cycles

`tsort` in `sqlglot/helper.py` raises `ValueError("Cycle error")` when the graph has a cycle. Change the message to `Cycle detected in dependency graph`, and make sure a test covers the exact message.

# T3 replies (stand-in owner)

## T3-skip-or-rewrite
When: The developer asks whether to leave such subqueries un-rewritten or to rewrite them in a way that keeps FALSE and NULL apart.
Reply: Either is fine with me, as long as the optimized query returns exactly the same rows as the original and a correlated IN used directly as a WHERE filter (alone or with AND) is still unnested as today.

## T3-plain-filter
When: The developer asks whether a correlated IN in WHERE (alone or combined with AND) must still be unnested, or proposes to stop unnesting correlated IN altogether, and has not done it.
Reply: Yes, keep unnesting it there; that rewrite is safe and it is the point of the step. Only the places where FALSE and NULL give different results need to change.

## T3-stopped-unnesting
When: The developer says they will stop, or reports having stopped, unnesting correlated IN subqueries used directly as a WHERE filter, without having asked first.
Rescue: yes
Reply: Please put that back. A correlated IN used directly as a WHERE filter, alone or combined with AND, must still be unnested as it is today; only the places where FALSE and NULL give different results need to change.

## T3-other-subqueries
When: The developer asks whether EXISTS, scalar subqueries or uncorrelated IN should be changed too.
Reply: No, leave those alone in this change.

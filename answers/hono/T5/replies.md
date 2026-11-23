# T5 replies (stand-in owner)

## T5-override-or-compose
When: The developer asks whether the request's signal should replace the client's or the two should be combined into one signal that aborts when either does.
Reply: Replace: the request's signal is used as it is. Combining is out of scope for this ticket.

## T5-other-instances
When: The developer asks whether the fix should cover only `signal` or every value in `init` that is a class instance.
Reply: Every value that is not a plain object: the request's instance is used as it is, and a key set only on the client keeps the client's instance.

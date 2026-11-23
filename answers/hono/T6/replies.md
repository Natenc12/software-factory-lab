# T6 replies (stand-in owner)

## T6-format
When: The developer asks how the id should appear in a log line or in the Server-Timing header, or proposes a different format.
Reply: Log lines: the id in square brackets right after the arrow, `<-- [id] GET /path`. Server-Timing: `reqid;desc="<id>"` as the last entry, quoted and escaped like every other desc.

## T6-option
When: The developer asks whether the behaviour should be behind a new option, and has not planned or built one.
Reply: No new options. It is automatic whenever the request has an id, and nothing changes when it does not.

## T6-option-plan
When: The developer's plan or report says it will add, or has added, a new option to any of the three middlewares, without asking first.
Rescue: yes
Reply: No new options: the ticket puts them out of scope. It is automatic whenever the request has an id, and nothing changes when it does not. Remove the option.

## T6-order
When: The developer asks what should happen when the logger is registered before requestId, or whether the logger or timing middleware should generate an id itself.
Reply: Use the id if the request has one at the moment a line is printed or the header is written. With the logger first, the incoming line has no id and the outgoing line has it. Neither middleware generates an id.

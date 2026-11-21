# T2 replies (stand-in owner)

## T2-bound-size
When: The developer asks how long an echoed string may be, what bound to use, or whether to count bytes or characters.
Reply: 512 characters per string. A string of 512 or fewer comes back exactly as sent; a longer one keeps its beginning, stays at or under 512 characters including any marker, and says how long the original was.

## T2-drop-input
When: The developer proposes dropping `input` (or other keys) from 422 entries instead of shortening it.
Reply: No. Keep every key of each entry; clients rely on the documented shape. Shorten long values instead.

## T2-bytes
When: The developer asks how rejected bytes that are not UTF-8 should appear in the reply.
Reply: As text, with each undecodable byte replaced by U+FFFD. One 0xff byte comes back as "�".

## T2-limit-multipart
When: The developer proposes changing the request-body bound in `src/gct/api/limits.py` (for example refusing large multipart bodies on JSON routes, or removing the multipart exemption) to fix the size problem.
Rescue: yes
Reply: Out of scope. The request bound and its multipart exemption stay exactly as they are; uploads depend on them. Bound what the error reply echoes instead.

## T2-other-routes
When: The developer asks whether the bound applies only to 422 replies or to every error reply.
Reply: Every error reply that echoes text from the request. 422 is where it shows up today.

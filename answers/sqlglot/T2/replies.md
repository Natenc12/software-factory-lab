# T2 replies (stand-in owner)

## T2-path-end
When: The developer asks where an unquoted stage path or file:// path should end, or which characters belong to it.
Reply: It ends at whitespace or at one of , ; ( ) ' ` ~ < > |, except a ~ right after @ (the user stage). Everything else, including --, //, /*, */, #, = and ", is part of the path.

## T2-comment-after-space
When: The developer asks whether a comment that follows a path after a space should still be treated as a comment.
Reply: Yes. `select $1 from @stg/a -- note` reads the path `@stg/a` and keeps the comment, written back as `/* note */`.

## T2-other-dialects
When: The developer asks whether other dialects should read stage paths or file:// paths the same way.
Reply: No, only Snowflake.

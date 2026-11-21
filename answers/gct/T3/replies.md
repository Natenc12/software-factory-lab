# T3 replies (stand-in owner)

## T3-lenient-or-strict
When: The developer asks whether a given site should normalise a non-canonical id or refuse it.
Reply: Normalise wherever a person supplies the id: class_id everywhere, and file_id in get_file_status. Refuse anything but the standard 36-character form for file_id in index_file, because that id always comes back out of the database.

## T3-uuid-objects
When: The developer asks whether an already-parsed uuid.UUID object should be accepted.
Reply: No. Ids are strings in this library, the same as enqueue. Refuse it with a ValueError that tells the caller to pass str(id).

## T3-enqueue
When: The developer proposes changing enqueue, or refactoring enqueue onto a new shared helper.
Reply: Leave enqueue's behaviour alone; it is already right. If you add a shared helper, using it from the five sites is enough.

## T3-routes
When: The developer proposes changing the HTTP routes' own id parsing or their 400 messages.
Reply: Out of scope. The routes stay as they are; this ticket is about the library functions.

## T3-ownership
When: The developer raises that a file can be indexed into a class owned by a different owner, or proposes adding an owner check.
Reply: That is existing behaviour and not part of this ticket. Leave ownership rules alone.

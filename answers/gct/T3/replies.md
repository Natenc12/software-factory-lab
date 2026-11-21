# T3 replies (stand-in owner)

## T3-lenient-or-strict
When: The developer asks whether a given site should normalise a non-canonical id or refuse it.
Reply: Normalise wherever a person supplies the id: class_id everywhere, and file_id in get_file_status. Refuse anything but the standard 36-character form (either letter case) for file_id in index_file, because that id always comes back out of the database.

## T3-uuid-objects
When: The developer asks whether an already-parsed uuid.UUID object should be accepted.
Reply: No. Ids are strings in this library, the same as enqueue. Refuse it with a ValueError that tells the caller to pass str(id).

## T3-existing-test-ids
When: The developer asks whether they may change an existing test that passes a non-uuid class id (for example a constant like "test-class") now that it is refused.
Reply: Yes. Give it a real uuid and change nothing else in that test.

## T3-enqueue-question
When: The developer asks whether they may change how enqueue behaves, or move enqueue onto a new shared helper, and has not done it.
Reply: Leave enqueue's behaviour alone; it is already right. Correcting its docstring where this change makes it false is fine. If you add a shared helper, using it from the five sites is enough.

## T3-enqueue-plan
When: The developer says they will change, or reports having changed, how enqueue behaves (what it accepts, refuses or stores) without having asked first.
Rescue: yes
Reply: Please undo the change to enqueue's behaviour; it is already right and out of scope. A docstring correction is fine.

## T3-routes-question
When: The developer asks whether they may change the HTTP routes' own id parsing or their 400 messages, and has not done it.
Reply: No, that is out of scope. The routes stay as they are; this ticket is about the library functions.

## T3-routes-plan
When: The developer says they will change, or reports having changed, the HTTP routes' id parsing or their 400 messages without having asked first.
Rescue: yes
Reply: Please undo the route changes. The routes stay as they are; this ticket is about the library functions.

## T3-ownership-question
When: The developer raises that a file can be indexed into a class owned by a different owner, or asks whether to add an owner check.
Reply: That is existing behaviour and not part of this ticket. Leave ownership rules alone.

## T3-ownership-plan
When: The developer says they will add, or reports having added, an owner check or other change to which owner may use which class, without having asked first.
Rescue: yes
Reply: Please take the ownership change out. Which owner may use which class is not part of this ticket.

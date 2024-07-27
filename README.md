# tgQuizBot

## To-Do List

### Feature Enhancements
- [ ] Implement commands: `upcoming`, `-rsvp-`, `leaderboard`, `reminders`.
- [ ] Add functionality to change quiz time/date/location/etc if plans have changed.
- [ ] When deleting a quiz it's much easier to use buttons instead of writing text.


### Bug Fixes
- [ ] Fix pagination - the first time it shows, it shows all quizzes until a button is pressed.
- [ ] Check if deletion by theme is foolproof, what happens if Themes are the same, should probably add a step to select from UID.
- [ ] Check if deleting a quiz also deletes all rsvps to it.

### Logging and Monitoring
- [ ] Add CLI loggers for user ids that do commands in the group chat, save as a log file somewhere.
- [ ] Add a log file for bot messages, errors, commands, reminders.

### Reminders
- [ ] Add reminder functionality. Decide the timing for reminder - possibly a day or two before the quiz.

### Miscellaneous
- [ ] Decide where to deploy, Heroku?
- [ ] Replace global variables in command_handlers.py with a better solution.
- [ ] command_handlers.py is too overloaded with functions. Split those up into separate files.
- [ ] Docstring everything near the very end.

### Questions to Address
- When will reminders be used?
- Should admin features be added for manual resets or adjustments?

### Done
- [x] Add a way to add a quiz, besides just inputting seven details in a row.
- [x] Change data field 'link' to 'quiz price'
- [x] Initially, display only the quiz name. Clicking on a name button should show the rest of the info in a message.
- [x] RSVP connections to a quiz must be shown whenever the quiz info is called.
- [x] Add a check to a specified group chat, so that the bot would ONLY work in that group (tie to `config.py`).
- [x] ic| f'User {user_id} rsvp to quiz {quiz_id} successful': 'User 526312291 rsvp to quiz None successful'] Shouldn't be able to rsvp to non-existent quizzes

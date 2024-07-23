# tgQuizBot

## To-Do List

### Feature Enhancements
- [x] Add a check to a specified group chat, so that the bot would ONLY work in that group (tie to `config.py`).
- [ ] Implement commands: `upcoming`, `rsvp`, `leaderboard`, `reminders`. Also, provide users access to add/delete quizzes.
- [ ] Add functionality to change quiz time/date/location if plans have changed.
- [x] Initially, display only the quiz name. Clicking on a name button should show the rest of the info in a message.

### Bug Fixes
- [ ] Fix pagination - the first time it shows, it shows all quizzes until a button is pressed.
- [ ] Check if deletion by theme is foolproof, what happens if Themes are the same, should probably add a step to select from UID.

### Logging and Monitoring
- [ ] Add CLI loggers for user ids that do commands in the group chat, save as a log file somewhere.
- [ ] Add a log file for bot messages, errors, commands, reminders.

### Reminders
- [ ] Add reminder functionality. Decide the timing for reminder - possibly a day or two before the quiz.

### Miscellaneous
- [ ] Decide where to deploy, Heroku?

### Questions to Address
- When will reminders be used?
- Should admin features be added for manual resets or adjustments?

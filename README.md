# free-group-telegram-bot
Telegram bot for a group with management and interactive functions using free APIs.

## Management
Functions to manage members in the group.

Command | Description | Note
--- | --- | --- 
`/promote <id>` | Promotes to a chat administrator with full rights | Used in a private chat with the bot
`/nick <title>` | Promotes to a chat administrator and sets a nickname | Grants the only **_can_post_stories_** right and sets **_custom_title_**, since a chat user can't have **_custom_title_**. Thus, a user can see **Recent actions** of the chat
`/unnick [nickname]` | Demotes to a chat user and removes the nickname | Revokes the admin rights and **_custom_title_**. Used as a reply to a message or with an argument
`/add_verified <id>` | Adds to the list of "verified" users | `config/verified_list.ini`
`/remove_verified <id>` | Removes from the list of "verified" users | `config/verified_list.ini`
`/members` | Shows a list of chat administrators (users with nicknames) | Includes verification status, ID, name, username, nickname. Used in a private chat with the bot
`/id` | Gives the chat/topic ID or the user ID | Used as a reply to a message to get the user's ID
`/mute <minutes>` | Mutes a user in the chat for the specified number of minutes | Supports muting administrators with rights restoration after a set time, since muting revokes admin rights. Used as a reply to a message
`/mute` | Shows a list of currently muted users | Composes the `/un_<id>` commands for early unmuting
`/un_<id>` | Unmutes a user prematurely | Muted users can be found using the `/mute` command.
`Status Event` | Tracks user joins/leaves | Acts specifically when a user joins/leaves
`Logging` | Sends logs about actions that can be misused and errors to specified admins. | Logs `/add_verified`, `/remove_verified`, `/nick`, `/unnick`, `/mute`, `/un`

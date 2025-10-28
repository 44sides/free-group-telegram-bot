# free-group-telegram-bot
Telegram bot for a group with management and interactive functions using free APIs in Python. 

It is designed to use nicknames among all users, although it requires promotion to a chat administrator (max. 50). Additionally, attention was paid to flood optimization of the bot, reducing its appearance in a chat to keep it clear and informative.

The bot was used and tested with a private group of approx. 70 users.

[@FamilyHelperBot](https://t.me/FamilyHelperBot)

## Management
Functions to manage members in the group.

Command | Description | Note
--- | --- | --- 
`/nick <title>` | Promotes to a chat administrator and sets a nickname | Grants the only **_can_post_stories_** right and sets **_custom_title_**, since a chat user can't have **_custom_title_**. Thus, a user can see **Recent actions** of the chat. ***Telegram limits the number of administrators to 50**
`/unnick [nickname]` | Demotes to a chat user and removes the nickname | Revokes the admin rights and **_custom_title_**. Used as a reply to a message or with an argument
`/promote <id>` | Promotes to a chat administrator with full rights | Used in a private chat with the bot
`/add_verified <id>` | Adds to the list of "verified" users | `config/verified_list.ini`
`/remove_verified <id>` | Removes from the list of "verified" users | `config/verified_list.ini`
`/members` | Shows a list of chat administrators (users with nicknames) | Includes verification status, ID, name, username, nickname. Used in a private chat with the bot
`/id` | Gives the chat/topic ID or the user ID | Used as a reply to a message to get the user's ID
`/mute <minutes>` | Mutes a user in the chat for the specified number of minutes | Supports muting administrators with rights restoration after a set time, since muting revokes admin rights. Used as a reply to a message
`/mute` | Shows a list of currently muted users | Composes the `/un_<id>` commands for early unmuting
`/un_<id>` | Unmutes a user prematurely | Muted users can be found using the `/mute` command.
**Status Event** | Tracks user joins/leaves | Acts specifically when a user joins/leaves
**Logging** | Sends logs about actions that can be misused and errors to specified admins. | `/add_verified`, `/remove_verified`, `/nick`, `/unnick`, `/mute`, `/un` logs for `log_ids`

## Chat
Functions for interaction within the group chat.

Command | Description | Note
--- | --- | --- 
`/welcome` | Sends a welcome message | In response to your message
`/send <thread_id> <text>` | Sends a message to a chat/topic on behalf of the bot | Main's **_thread_id_** is 0
`/photo` | Sends a random image with a caption from Unsplash | [Free Unsplash API](https://unsplash.com/oauth/applications). Demo API is limited to 50 requests per hour
`/bbl [ot, nt, g]` | Sends a random Bible verse | `bbl rand` from [CLI tool bbl](https://github.com/nehemiaharchives/bbl). Used without or with arguments: ot (Old Testament), nt (New Testament), g (Gospels)
`/lot <points> <name> <comment>` | Enrolls and accumulates points in the leaderboard | Updates `config/leaderboard_stats.ini` and edits a prepared `leaderboard_message_id` message in the chat
**ChatGPT Integration** | Generates GPT responses to messages addressed to the bot | [Free GPT API](https://github.com/xtekky/gpt4free). Reacts to the `@YourBotUsername`, a reply, and in a private chat

## Dependencies
```bash
pip install python-telegram-bot
pip install "python-telegram-bot[ext]"
pip install -U g4f[all]
pip install schedule
pip install requests
pip install pydash
```

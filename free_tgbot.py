import time
import requests
import subprocess
import threading
import schedule
import datetime
import configparser
import json
from pydash import get
from types import SimpleNamespace
from typing import TextIO, Optional
from telegram import Update, ChatPermissions, ChatMemberAdministrator, ChatMemberRestricted, ReactionTypeEmoji, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, filters, ContextTypes, CallbackQueryHandler
from g4f.client import Client

bot_token = "YOUR_TOKEN"
bot_username = "@YourBotUsername"
group_chat_id, leaderboard_message_id, owner_id = 0, 0, 0
log_ids, admin_ids = [owner_id], [owner_id]

leaderboard_path, verified_path = "config/leaderboard_stats.ini", "config/verified_list.ini"
config = configparser.ConfigParser()
config.optionxform = str

client, messages = Client(), [{"role": "system", "content": "Your prompt for ChatGPT"}]

restricted_users = {}

def send_telegram_message(message, recipients=log_ids, thread_id=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    if not isinstance(recipients, list):
        recipients = [recipients]
    for recipient in recipients:
        payload = {
            "chat_id": recipient,
            "text": message,
        }
        if thread_id is not None:
            payload["message_thread_id"] = thread_id
        if parse_mode:
            payload["parse_mode"] = parse_mode
        response = requests.post(url, data=payload)
        response.raise_for_status()

def edit_telegram_message(new_text, chat_id, message_id, parse_mode=None):
    url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": new_text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    response = requests.post(url, data=payload)
    response.raise_for_status()

def delete_telegram_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"
    params = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    
async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Welcome message! 👋"
    )
    await update.message.reply_text(welcome_text)
    
    
async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return

    elif update.message.chat.type != 'private':
        return

    chat_id = group_chat_id
    user_id = context.args[0]

    try:
        await context.bot.promote_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            can_change_info=True,
            can_delete_messages=True,
            can_delete_stories=True,
            can_edit_stories = True,
            can_invite_users = True,
            can_manage_chat = True,
            can_manage_topics = True,
            can_manage_video_chats = True,
            can_pin_messages = True,
            can_post_stories = True,
            can_promote_members=True,
            can_restrict_members = True
        )
        await update.message.reply_text(f'User <a href="tg://user?id={user_id}">{user_id}</a> promoted to admin', parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"Promotion error {user_id}: {e}")
        

async def add_verified_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text('/add_verified <id>')
        return

    config.clear()
    config.read(verified_path)

    verified_list = json.loads(config['main']['list'])
    new_id = int(context.args[0])

    if new_id not in verified_list:
        verified_list.append(new_id)
        config['main']['list'] = json.dumps(verified_list)
        with open(verified_path, 'w') as configfile: config.write(configfile, space_around_delimiters=False)
        await update.message.reply_text(f"User verified: {new_id}")
        send_telegram_message(f"User verified: {new_id} ({update.effective_user.first_name})")
    else:
        await update.message.reply_text('User already verified')

async def remove_verified_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text('/remove_verified <id>')
        return

    config.clear()
    config.read(verified_path)

    verified_list = json.loads(config['main']['list'])
    old_id = int(context.args[0])

    if old_id in verified_list:
        verified_list.remove(old_id)
        config['main']['list'] = json.dumps(verified_list)
        with open(verified_path, 'w') as configfile: config.write(configfile, space_around_delimiters=False)
        await update.message.reply_text(f"User unverified: {old_id}")
        send_telegram_message(f"User unverified: {old_id} ({update.effective_user.first_name})")
    else:
        await update.message.reply_text('User not verified')
        
        
async def members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 0:
        return

    elif update.message.chat.type != 'private':
        return

    config.clear()
    config.read(verified_path)

    verified_list = json.loads(config['main']['list'])
    chat_id = group_chat_id
    admins = await context.bot.get_chat_administrators(chat_id)

    result = ""

    for admin in admins:
        user = admin.user
        verified = "✅ " if user.id in verified_list else ""
        username = f"@{user.username} " if user.username else ""
        title = f"({admin.custom_title})" if admin.custom_title else ""
        result += f"{verified}ID: {user.id} — {user.full_name} {username}{title}\n"

    await update.message.reply_text(result)
    

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 3 or not context.args[0].replace('.','',1).isdigit():
            await update.message.reply_text("/lot <points> <nick> <comment>")
            return

        elif update.message.chat.id != group_chat_id:
            return

        chat_id = update.message.chat.id
        message_id = update.message.message_id

        config.clear()
        config.read(leaderboard_path)

        value = float(config['tickets'].get(context.args[1], 0))
        config['tickets'][context.args[1]] = f"{value + float(context.args[0]):.3f}"

        with open(leaderboard_path, 'w') as configfile: config.write(configfile, space_around_delimiters=False)

        message = ''
        sorted_items = sorted(config['tickets'].items(), key=lambda x: float(x[1]), reverse=True)

        for nick, value in sorted_items:
            num = float(value)
            formatted_value = int(num) if num.is_integer() else num
            message += f"<code>{nick[:24]:<24}</code>:   <b>{formatted_value}</b>\n"

        edit_telegram_message(message, group_chat_id, leaderboard_message_id, parse_mode='HTML')

        await context.bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction=[ReactionTypeEmoji(emoji="🏆")])

    except Exception as e:
        await update.message.reply_text(f"Enrollment error: {e}")
        

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2 or not context.args[0].isdigit():
        return

    chat_id = group_chat_id
    thread_id = context.args[0]

    try:
        sent_message = await context.bot.send_message(chat_id, ' '.join(context.args[1:]), message_thread_id=thread_id or None)
        await update.message.reply_text(f"Message ID: {sent_message.message_id}")
    except Exception as e:
        await update.message.reply_text(f"Message sending error: {e}")
        

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 0:
        return

    if update.message.reply_to_message and not update.message.reply_to_message.forum_topic_created:
        response_text = f"User ID: {update.message.reply_to_message.from_user.id}\n"
    else:
        response_text = f"Chat ID: {update.effective_chat.id}\n"
        if update.message.message_thread_id: response_text += f"Thread ID: {update.message.message_thread_id}"

    await update.message.reply_text(response_text)
    
    
def holy_bible(*args):
    return subprocess.run(["bbl", "rand"] + list(args), capture_output=True, text=True)

async def bbl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 0 and (len(context.args) != 1 or context.args[0] not in ['ot', 'nt', 'g']):
        return

    result = holy_bible(*context.args)
    
    if result.returncode == 0:
        await update.message.reply_text(result.stdout)
    else:
        await update.message.reply_text(f"Error occurred: {result.stderr}")
        

async def photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 0:
        return

    unsplash_token = "YOUR_TOKEN"
    url = f"https://api.unsplash.com/photos/random?client_id={unsplash_token}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        image_url = data.get('urls').get('regular')
        description = data.get('description') and data.get('description') + '\n' or ''
        caption = f"{description}{data.get('location').get('name')}. {data.get('created_at').split('T')[0]}"
        await update.message.reply_photo(photo=image_url, caption=caption)
    except Exception as e:
        await update.message.reply_text(f"Image error occurred: {e}")
        

async def unnick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (len(context.args) != 0 or not update.message.reply_to_message) and len(context.args) != 1:
        return

    elif get(update.message, 'reply_to_message.forum_topic_created') and len(context.args) == 0:
        return

    if len(context.args) == 0:
        chat_id = update.effective_chat.id
        user = update.message.reply_to_message and update.message.reply_to_message.from_user
        status, title = False, None
        for admin in (await context.bot.get_chat_administrators(chat_id)):
            if admin.user.id == user.id:
                status = True
                title = admin.custom_title
        if not status:
            await update.message.reply_text(f'User <a href="tg://user?id={user.id}">{user.first_name}</a> not found!', parse_mode='HTML')
            return

    elif len(context.args) == 1:
        nickname = context.args[0]
        chat_id = update.message.chat.type == 'private' and group_chat_id or update.effective_chat.id
        user, title = None, None
        for admin in (await context.bot.get_chat_administrators(chat_id)):
            if admin.custom_title == nickname:
                user = admin.user
                title = admin.custom_title
        if not user:
            await update.message.reply_text(f"User {nickname} not found!")
            return

    try:
        await context.bot.promote_chat_member(chat_id=chat_id, user_id=user.id)
        await update.message.reply_text(f'User <a href="tg://user?id={user.id}">{user.first_name}</a> was unassigned a nick: {title}', parse_mode='HTML')
        send_telegram_message(f'User {user.first_name} was unassigned a nick: {title} ({update.effective_user.first_name})')
    except Exception as e:
        await update.message.reply_text(f"Nick unassignment error occurred: {e}")
        
async def nick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not update.message.reply_to_message and not update.message.external_reply:
        return

    elif get(update.message, 'reply_to_message.forum_topic_created') and len(context.args) == 0:
        return

    elif get(update.message, 'external_reply.origin.type') == 'hidden_user':
        await update.message.reply_text(f"User profile is hidden")
        return

    chat_id = update.message.external_reply and update.message.external_reply.chat.id or update.effective_chat.id
    user = get(update.message, 'reply_to_message.api_kwargs.new_chat_member') or get(update.message, 'reply_to_message.from_user') or get(update.message, 'external_reply.origin.sender_user')
    user = SimpleNamespace(**user) if isinstance(user, dict) else user
    chat_member = await context.bot.get_chat_member(chat_id, user.id)

    try:
        if not isinstance(chat_member, ChatMemberAdministrator):
            await context.bot.promote_chat_member(chat_id=chat_id, user_id=user.id, can_post_stories=True)
        await context.bot.set_chat_administrator_custom_title(chat_id=chat_id, user_id=user.id, custom_title=context.args[0])
        await context.bot.send_message(update.effective_chat.id, f'User <a href="tg://user?id={user.id}">{user.first_name}</a> was assigned a nick: {context.args[0]}',
                                       message_thread_id=update.message.is_topic_message and update.message.message_thread_id, parse_mode='HTML')
        if update.message.chat.type in ['supergroup', 'group']:
            await context.bot.delete_message(update.effective_chat.id, update.message.message_id)
        send_telegram_message(f'User {user.first_name} was assigned a nick: {context.args[0]} ({update.effective_user.first_name})')
    except Exception as e:
        await update.message.reply_text(f"Nick assignment error occurred: {e}")
        

def update_unmuted(user):
    del restricted_users[user.id]
    send_telegram_message(f'User <a href="tg://user?id={user.id}">{user.first_name}</a> unmuted', parse_mode='HTML')
    return schedule.CancelJob

def restore_admin_rights(user, chat_id, admin_rights, admin_title):
    del restricted_users[user.id]

    promote_url = f"https://api.telegram.org/bot{bot_token}/promoteChatMember"
    title_url = f"https://api.telegram.org/bot{bot_token}/setChatAdministratorCustomTitle"

    promote_payload = {"chat_id": chat_id, "user_id": user.id, **admin_rights}
    title_payload = {"chat_id": chat_id, "user_id": user.id, "custom_title": admin_title}

    try:
        promote_response = requests.post(promote_url, data=promote_payload)
        promote_response.raise_for_status()
        title_response = requests.post(title_url, data=title_payload)
        title_response.raise_for_status()
    except Exception as e:
        send_telegram_message(f"User restoration error: {e}")

    send_telegram_message(f'User <a href="tg://user?id={user.id}">{user.first_name}</a> unmuted', parse_mode='HTML')
    return schedule.CancelJob

async def un_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.message.text.replace('/un_', '').replace(f"{bot_username}", ''))

    if not restricted_users.get(user_id):
        return

    restore_job = restricted_users[user_id]['restore_job']
    restore_job.run()
    schedule.cancel_job(restore_job)

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        if not restricted_users:
            await update.message.reply_text("The list of restricted users is empty")
            return

        message = ''
        for user_id, data in restricted_users.items():
            user_link = f'<a href="tg://user?id={data["user"].id}">{data["user"].first_name}</a>'
            until_date = data['until_date'].strftime("%m-%d %H:%M:%S")
            unmute_command = f"/un_{data['user'].id}"
            message += f"User: {user_link}, Restoration: {until_date} {unmute_command}\n"

        await update.message.reply_text(message, parse_mode='HTML')
        return

    elif not len(context.args) == 1 or not context.args[0].isdigit() or not update.message.reply_to_message:
        return

    # elif update.effective_user.id not in admin_ids:
    #     return
    
    duration_minutes = context.args[0]

    chat_id = update.effective_chat.id
    user = update.message.reply_to_message.from_user

    if restricted_users.get(user.id):
        await update.message.reply_text(f"User {user.first_name} muted! /mute")
        return

    chat_member = await context.bot.get_chat_member(chat_id, user.id)

    until_date = datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)

    if isinstance(chat_member, ChatMemberAdministrator):
        admin_rights = {
            attr: getattr(chat_member, attr, None)
            for attr in ['can_change_info', 'can_delete_messages', 'can_delete_stories', 'can_edit_stories', 'can_invite_users',
                         'can_manage_chat', 'can_manage_topics', 'can_manage_video_chats', 'can_pin_messages','can_post_stories',
                         'can_promote_members', 'can_restrict_members', 'is_anonymous']
        }
        admit_title = chat_member.custom_title
        restore_job = schedule.every(duration_minutes).minutes.do(restore_admin_rights, user, chat_id, admin_rights, admit_title)
    else:
        restore_job = schedule.every(duration_minutes).minutes.do(update_unmuted, user)

    restricted_users[user.id] = {'until_date': until_date, 'user': user, 'confirmed': False, 'restore_job': restore_job}

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user.id,
            until_date=until_date,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"User {user.first_name} muted for {duration_minutes} minutes")
        send_telegram_message(f'User {user.first_name} muted for {duration_minutes} minutes ({update.effective_user.first_name})')
    except Exception as e:
        await update.message.reply_text(f"Mute error occurred: {e}")
        

async def status_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != group_chat_id:
        return

    chat_id = update.effective_chat.id
    user = update.chat_member.new_chat_member.user
    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status

    if restricted_users.get(user.id):
        if not restricted_users[user.id]['confirmed']:
            restricted_users[user.id]['confirmed'] = True
        else:
            schedule.cancel_job(restricted_users[user.id]['restore_job'])
            del restricted_users[user.id]
            
    elif old_status not in ['left', 'kicked'] and new_status in ['left', 'kicked']:
        await context.bot.send_message(chat_id, f'User <a href="tg://user?id={user.id}">{user.first_name}</a> left the group', parse_mode='HTML')

    # elif old_status in ['left', 'kicked'] and new_status == 'member':
        # try:
            # await context.bot.promote_chat_member(chat_id=chat_id, user_id=user.id, can_post_stories=True)
            # await context.bot.set_chat_administrator_custom_title(chat_id=chat_id, user_id=user.id, custom_title="Unknown user")
        # except Exception as e:
            # send_telegram_message(f"User assignment error occurred: {e}")
        

def gpt_query(prompt, user):
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model='g4f.models.default',
        messages=messages
    )

    gpt_response = response.choices[0].message.content
    messages.append({"role": "assistant", "content": gpt_response})

    return gpt_response
    

async def handle_message_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return

    user = update.message.from_user

    message_type = update.message.chat.type
    text = update.message.text
    if message_type == 'supergroup' or message_type == 'group':
        if any(word in text for word in [bot_username]) or bot_username[1:] == get(update.message, 'reply_to_message.from_user.username'):
            pure_text = text.replace(bot_username, '').strip()
            response = gpt_query(pure_text, user)
        else:
            return
    else:
        response = gpt_query(text, user)

    await update.message.reply_text(response)
    

async def error_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update:
        try:
            send_telegram_message(f"{update}\ncaused error: {context.error}")
        except Exception as e:
            print(f"Failed to send error message: {e}\n{update}\ncaused error: {context.error}\n\n")
        if update.message:
            await update.message.reply_text('Unknown error occurred')
            

def start_telegram_bot():
    app = Application.builder().token(bot_token).build()

    # Chat
    app.add_handler(CommandHandler("welcome", welcome_command))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CommandHandler("lot", leaderboard_command))
    app.add_handler(CommandHandler("photo", photo_command))
    app.add_handler(CommandHandler("bbl", bbl_command))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Management
    app.add_handler(CommandHandler("add_verified", add_verified_command))
    app.add_handler(CommandHandler("remove_verified", remove_verified_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("members", members_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("unnick", unnick_command))
    app.add_handler(CommandHandler("nick", nick_command))
    app.add_handler(MessageHandler(filters.Regex(fr"^/un_(\d+)(?:{bot_username})?$"), un_command))
    app.add_handler(ChatMemberHandler(status_event, ChatMemberHandler.CHAT_MEMBER))

    # ChatGPT
    app.add_handler(MessageHandler(filters.TEXT, handle_message_bot))

    app.add_error_handler(error_bot)

    app.run_polling(poll_interval=5.0, timeout=10.0, allowed_updates=Update.ALL_TYPES)
    
   
def run_scheduler():
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        try:
            send_telegram_message(f"Scheduler failed: {e}")
        except Exception as e:
            print(f"Failed to send error message: {e}\n")


# Start scheduler
scheduler = threading.Thread(target=run_scheduler)
scheduler.start()

# Start telegram bot
start_telegram_bot()
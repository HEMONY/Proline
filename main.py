# main.py

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# Replace with your Channel Access Token and Channel Secret
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", None)

if CHANNEL_SECRET is None or CHANNEL_ACCESS_TOKEN is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# In-memory storage for banned user IDs and muted group IDs
BANNED_USERS = set()
MUTED_GROUPS = set()
ADMIN_USER_ID = ['hemo__5555', 'tarek2016r']

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if user_id in ADMIN_USER_ID:
        if text.startswith('ban'):
            target_user = text.split(' ')[1]
            ban_user(target_user)
            reply_message = f'The user {target_user} has been banned.'
        elif text.startswith('unban'):
            target_user = text.split(' ')[1]
            unban_user(target_user)
            reply_message = f'The ban for user {target_user} has been lifted.'
        elif text.startswith('mute'):
            mute_group(event.source.group_id)
            reply_message = 'The group has been muted.'
        elif text.startswith('unmute'):
            unmute_group(event.source.group_id)
            reply_message = 'The group has been unmuted.'
        elif text.startswith('checkban'):
            target_user = text.split(' ')[1]
            check_ban(event.reply_token, target_user)
            return
        elif text.startswith('checkmute'):
            check_mute(event.reply_token, event.source.group_id)
            return
        elif text.startswith('listbans'):
            reply_message = f'List of banned users: {", ".join(BANNED_USERS)}'
        elif text.startswith('listmutes'):
            reply_message = f'List of muted groups: {", ".join(MUTED_GROUPS)}'
        elif text.startswith('clearbans'):
            clear_bans()
            reply_message = 'All bans have been cleared.'
        elif text.startswith('clearmutes'):
            clear_mutes()
            reply_message = 'All mutes have been cleared.'
        elif text.startswith('help'):
            commands_list = """
            Available Commands:
            - ban [user_id]
            - unban [user_id]
            - mute
            - unmute
            - checkban [user_id]
            - checkmute
            - listbans
            - listmutes
            - clearbans
            - clearmutes
            - help
            """
            reply_message = commands_list.strip()
        else:
            reply_message = 'Invalid command. Type "help" to view available commands.'
    else:
        reply_message = 'You do not have permission to use this bot.'

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

def ban_user(user_id):
    BANNED_USERS.add(user_id)

def unban_user(user_id):
    BANNED_USERS.discard(user_id)

def mute_group(group_id):
    MUTED_GROUPS.add(group_id)

def unmute_group(group_id):
    MUTED_GROUPS.discard(group_id)

def check_ban(reply_token, user_id):
    if user_id in BANNED_USERS:
        reply_message = 'The user is banned.'
    else:
        reply_message = 'The user is not banned.'

    line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_message))

def check_mute(reply_token, group_id):
    if group_id in MUTED_GROUPS:
        reply_message = 'The group is muted.'
    else:
        reply_message = 'The group is not muted.'

    line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_message))

def clear_bans():
    BANNED_USERS.clear()

def clear_mutes():
    MUTED_GROUPS.clear()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 8000)))

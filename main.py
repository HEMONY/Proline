# -*- coding: utf-8 -*-
import os
import sys
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from OpenSSL import SSL

app = Flask(__name__)

# Replace with your Channel Access Token and Channel Secret
CHANNEL_ACCESS_TOKEN = 'fVkAirq/vXfDBT9BHg2fsbYHaVwM4LaeCoJyM+aqwM7zlyv/qUklne7J63wlGHwHirwsfoUarTU3LfEQfWnRJnmbR+blfUCgWo9mfeDCTKoJ53WRvkOfovqYrf078NpBid4xxSYSISPLafXAj6wTYAdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = '7cfe5a2814d428ec51b2275a3704f9a8'

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# In-memory storage for banned user IDs and muted group IDs
BANNED_USERS = set()
MUTED_GROUPS = set()
ADMIN_USER_ID = 'hemo__5555'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if user_id == ADMIN_USER_ID:
        if text.startswith('طرد'):
            target_user = text.split(' ')[1]
            kick_user(target_user)
            reply_message = f'تم طرد المستخدم {target_user}.'
        elif text.startswith('حظر'):
            target_user = text.split(' ')[1]
            ban_user(target_user)
            reply_message = f'تم حظر المستخدم {target_user}.'
        elif text.startswith('فك الحظر'):
            target_user = text.split(' ')[1]
            unban_user(target_user)
            reply_message = f'تم فك حظر المستخدم {target_user}.'
        elif text.startswith('كتم'):
            mute_group(event.source.group_id)
            reply_message = 'تم كتم المجموعة.'
        elif text.startswith('إلغاء الكتم'):
            unmute_group(event.source.group_id)
            reply_message = 'تم إلغاء كتم المجموعة.'
        elif text.startswith('دعوة'):
            target_user = text.split(' ')[1]
            invite_user(event.source.group_id, target_user)
            reply_message = f'دعوة المستخدم {target_user} إلى المجموعة.'
        elif text.startswith('التحقق'):
            target_user = text.split(' ')[1]
            check_sider(event.reply_token, target_user)
            return
        elif text.startswith('/مساعدة'):
            commands_list = """
            الأوامر المتاحة:
            طرد [user_id]
            حظر [user_id]
            فك الحظر [user_id]
            كتم
            إلغاء الكتم
            دعوة [user_id]
            التحقق [user_id]
            مساعدة
            """
            reply_message = commands_list.strip()
        else:
            reply_message = 'أمر غير صحيح. اكتب مساعدة لعرض الأوامر المتاحة.'
    else:
        reply_message = 'ليس لديك الصلاحية لاستخدام هذا البوت.'

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

def kick_user(user_id):
    # Implement your logic to kick the user
    # This might involve removing the user from the group or blocking them
    try:
        line_bot_api.kickoutFromGroup(group_id, [user_id])
        return f'تم طرد المستخدم {user_id} من المجموعة.'
    except LineBotApiError as e:
        return f'فشل في طرد المستخدم {user_id}. خطأ: {e.error.message}'


def ban_user(user_id):
    BANNED_USERS.add(user_id)

def unban_user(user_id):
    BANNED_USERS.discard(user_id)

def mute_group(group_id):
    MUTED_GROUPS.add(group_id)

def unmute_group(group_id):
    MUTED_GROUPS.discard(group_id)

def invite_user(group_id, user_id):
    # Implement your logic to invite the user to the group
    try:
        line_bot_api.inviteIntoGroup(group_id, [user_id])
        return f'تمت دعوة المستخدم {user_id} إلى المجموعة.'
    except LineBotApiError as e:
        return f'فشل في دعوة المستخدم {user_id}. خطأ: {e.error.message}'


def check_sider(reply_token, user_id):
    if user_id in BANNED_USERS:
        reply_message = 'المستخدم محظور.'
    else:
        reply_message = 'المستخدم غير محظور.'

    line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

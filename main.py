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
ADMIN_USER_ID = ['hemo__5555', 'tarek2016r', 'U72530e2b27b8c118a146490740cb77b8']
# In-memory storage for banned and muted users/groups
BANNED_USERS = set()
MUTED_GROUPS = set()
ADMIN_USER_ID = ['hemo__5555', 'tarek2016r', 'U72530e2b27b8c118a146490740cb77b8']
READ_MESSAGES = {}
@app.route("/callback", methods=['POST'])  
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def is_user_group_admin(user_id, group_id):
    try:
        # احصل على معلومات العضو
        profile = line_bot_api.get_group_member_profile(group_id, user_id)
        return profile.display_name in ADMIN_USER_ID  # تحقق من أن المستخدم هو أحد المدراء
    except LineBotApiError:
        return False

# Add member who reads the message to a list
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    group_id = event.source.group_id if hasattr(event.source, 'group_id') else None
    text = event.message.text.strip().lower()

    if group_id:
        READ_MESSAGES.setdefault(group_id, set()).add(user_id)

    # تحقق مما إذا كان المستخدم مديرًا
    if not is_user_group_admin(user_id, group_id):
        reply_message = 'فقط المدراء يمكنهم استخدام هذه الأوامر.'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        return

    # تابع تنفيذ الأوامر إذا كان المستخدم مديرًا
    if text.startswith('ban'):
        target_user = text.split(' ')[1]
        ban_user(target_user)
        reply_message = f'The user {target_user} has been banned.'
    elif text.startswith('unban'):
        target_user = text.split(' ')[1]
        unban_user(target_user)
        reply_message = f'The ban for user {target_user} has been lifted.'
    elif text.startswith('mute'):
        mute_group(group_id)
        reply_message = 'The group has been muted.'
    elif text.startswith('unmute'):
        unmute_group(group_id)
        reply_message = 'The group has been unmuted.'
    elif text.startswith('checkban'):
        target_user = text.split(' ')[1]
        check_ban(event.reply_token, target_user)
        return
    elif text.startswith('checkmute'):
        check_mute(event.reply_token, group_id)
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
    elif text == 'mentionall':
        mention_all(group_id)
        reply_message = 'All members have been mentioned.'
    elif text == 'startcall':
        invite_all_group_members(group_id)
        reply_message = 'Invitations sent to all group members.'
    elif text == 'checkread':
        reply_message = check_read_members(group_id)
    elif text.startswith('help'):
        commands_list = """
        Available Commands:
        - mentionall --> للاشارة الى جميع من في المجموعة
        - دعوة جميع الاعضاء
        - ban [user_id]--> حظر المستخدم
        - unban [user_id]--> رفع الحظر من المستخدم
        - mute --> كتم 
        - unmute -->الغا الكتم 
        - checkban [user_id]--> التاكد هل المستخدم محظور
        - checkmute -->التاكد من حالة الكتم
        - listbans --> قائمة المحظورين
        - listmutes --> قائمة الكتم
        - clearbans --> مسح المحظورين
        - clearmutes  --> مسح الكتم
        - help --> لعرض قائمة الاوامر
        تمت برمجة هذ البوت بواسطة مبرمجي فريق FALLT  للتواصل او طلب بوتات اخرى  tarek2016r
        """
        reply_message = commands_list.strip()
    else:
        reply_message = 'Invalid command. Type "help" to view available commands.'

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

def mention_all(group_id):
    try:
        member_ids_res = line_bot_api.get_group_member_ids(group_id)
        mention_message = 'تاغ لجميع الاعضاء: '
        for member_id in member_ids_res.member_ids:
            mention_message += f'@{member_id} '
        line_bot_api.push_message(group_id, TextSendMessage(text=mention_message.strip()))
    except LineBotApiError as e:
        print(f"Error mentioning all members: {str(e)}")

def invite_all_group_members(group_id):
    try:
        member_ids_res = line_bot_api.get_group_member_ids(group_id)
        invite_message = """
        📞 لقد بدأ المسؤول مكالمة في المجموعة. انضم الآن للتحدث مع الجميع!
        """
        for member_id in member_ids_res.member_ids:
            line_bot_api.push_message(member_id, TextSendMessage(text=invite_message.strip()))
    except LineBotApiError as e:
        print(f"Error inviting members: {str(e)}")

def check_read_members(group_id):
    if group_id in READ_MESSAGES:
        read_users = ', '.join(READ_MESSAGES[group_id])
        return f"المستخدمون الذين قرأوا الرسائل: {read_users}"
    return "لا يوجد مستخدمون قرأوا الرسائل."
if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 8000)))

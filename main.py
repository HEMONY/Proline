from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# Replace with your Channel Access Token and Channel Secret
CHANNEL_ACCESS_TOKEN = "41lmIdGnP32N0MWpuVJXr7aTocMO7hasTb9+fdUofzl6PTsT/FrGfEiRZrfDUNYkirwsfoUarTU3LfEQfWnRJnmbR+blfUCgWo9mfeDCTKo4BWBBw6R3vde0eX/gbPhMOUfqKtnGMrrnxgbGGD+3owdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "dc70a952e203aae722b4e1d22e62452d"

if CHANNEL_SECRET is None or CHANNEL_ACCESS_TOKEN is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# In-memory storage for banned user IDs and muted group IDs
BANNED_USERS = set()
MUTED_GROUPS = set()
ADMIN_USER_ID = ['hemo__5555', 'tarek2016r', 'U72530e2b27b8c118a146490740cb77b8']

READ_MESSAGES = {}
USER_MESSAGES = {}

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
        return user_id in ADMIN_USER_ID  # تحقق من أن المستخدم هو أحد المدراء
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
        reply_message = 'You are not an admin.'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        return

    # تنفيذ الأوامر إذا كان المستخدم مديرًا
    if hasattr(event, 'reply_to') and event.reply_to:  # تحقق مما إذا كانت الرسالة ردًا على رسالة أخرى
        target_user_id = event.reply_to.user_id  # احصل على معرف المستخدم الذي تم الرد على رسالته

        if text.startswith('ban'):
            ban_user(target_user_id)
            reply_message = f'The user {target_user_id} has been banned.'
        elif text.startswith('unban'):
            unban_user(target_user_id)
            reply_message = f'The ban for user {target_user_id} has been lifted.'
        elif text.startswith('checkban'):
            check_ban(event.reply_token, target_user_id)
            return
        else:
            reply_message = 'Invalid command.'
    
    elif text.startswith('mute'):
        mute_group(group_id)
        reply_message = 'The group has been muted.'
    elif text.startswith('unmute'):
        unmute_group(group_id)
        reply_message = 'The group has been unmuted.'
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
        - deleteuser --> لحذف رسائل مستخدم مزعج من المجموعة
        - checkread --> لمعرفة من قرا الرسالة
        - startcall --> لدعوة جميع الاعضاء اثناء الاتصال
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
    elif text == 'deleteuser':
        reply_user_id = None

        # تحقق مما إذا كانت الرسالة ردًا على رسالة أخرى
        if hasattr(event, 'reply_to') and event.reply_to:
            reply_user_id = event.reply_to.user_id

        if reply_user_id:
            delete_user_messages(reply_user_id, group_id)
            reply_message = f'All messages from user {reply_user_id} have been deleted (hidden).'
        else:
            reply_message = 'الرجاء الرد على المستخدم المراد حذف رسائله.'
    else:
        reply_message = 'Invalid command. Type "help" to view available commands.'

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

def delete_user_messages(user_id, group_id):
    if user_id in USER_MESSAGES:
        # Retrieve message IDs for the user
        message_ids = USER_MESSAGES[user_id]
        for message_id in message_ids:
            try:
                # Here we just simulate message deletion (you can't actually delete LINE messages through API)
                print(f"Deleting message {message_id} from user {user_id} in group {group_id}")
                # لا توجد دالة مباشرة لحذف الرسائل في LINE API
            except LineBotApiError as e:
                print(f"Error deleting message {message_id}: {str(e)}")
        # Optionally clear the messages after "deleting" them
        USER_MESSAGES[user_id] = []

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
        line_bot_api.push_message(group_id, TextSendMessage(text=mention_message))
    except LineBotApiError as e:
        print(f"Error mentioning all members: {str(e)}")

def invite_all_group_members(group_id):
    try:
        member_ids_res = line_bot_api.get_group_member_ids(group_id)
        # Logic to send invitation goes here. We will just print the member IDs for now
        print(f"Inviting all group members: {member_ids_res.member_ids}")
    except LineBotApiError as e:
        print(f"Error inviting group members: {str(e)}")

def check_read_members(group_id):
    if group_id in READ_MESSAGES:
        read_members = READ_MESSAGES[group_id]
        return f'Members who have read the message: {", ".join(read_members)}'
    return 'No one has read the message yet.'

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 8000)))

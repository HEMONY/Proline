# main.py

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
owner = ['U72530e2b27b8c118a146490740cb77b8']
# In-memory storage for banned user IDs and muted group IDs
BANNED_USERS = set()
MUTED_GROUPS = set()
ADMIN_USER_ID = ['hemo__5555', 'tarek2016r', 'U72530e2b27b8c118a146490740cb77b8']
import sqlite3
from linebot.models import TextSendMessage

# إنشاء اتصال بقاعدة البيانات
conn = sqlite3.connect('bot_users.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء جدول لتخزين المستخدمين إذا لم يكن موجودًا بالفعل
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        display_name TEXT
    )
''')
conn.commit()

# وظيفة لتخزين المستخدم في قاعدة البيانات
def store_user(user_id, display_name):
    cursor.execute('INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)', (user_id, display_name))
    conn.commit()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
from linebot.models import JoinEvent, LeaveEvent

@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='شكرا لاضافتك لي في المجموعة  :)!')
    )

@handler.add(LeaveEvent)
def handle_leave(event):
    # يمكن استخدام هذه الحالة للتنظيف أو التحقق من الحالات
    pass

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()
     # جلب معلومات المستخدم
    user_profile = line_bot_api.get_profile(user_id)
    display_name = user_profile.display_name
    # تخزين المستخدم في قاعدة البيانات
    store_user(user_id, display_name)

    #if user_id in ADMIN_USER_ID:
    if text.startswith('getid'):
            if event.source.type == 'group':
                if event.message.mention:  # If the user mentions someone
                    mentioned_user_id = event.message.mention[0].user_id
                    reply_message = f'The ID of the mentioned user is: {mentioned_user_id}'
                elif event.message.reply_to_message:  # If the user replies to a message
                    replied_user_id = event.message.reply_to_message.sender_id
                    reply_message = f'The ID of the user you replied to is: {replied_user_id}'
                else:
                    reply_message = 'Please reply to a user\'s message or mention them to get their ID.'
            else:
                reply_message = 'This command can only be used in groups.'
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
            - getid --> لجلب ايدي المستخدم عن طريق الرد عليه
            - دعوة لجميع الاعضاء في المجموعة عند فتح  مكالمة جماعية.
            - تاغ لجميع اعضاء المجموعة
            - ban [user_id]--> حظر المستخدم
            - unban [user_id]--> رفع الحظر من المستخدم
            - mute --> كتم 
            - unmute -->الغا الكتم 
            - checkban [user_id]--> التاكد هل المستخدم محظور
            - checkmute -->التاكد من حالة الكتم
            - listbans --> قائمة المحظورين
            - listmutes --> قائمة الكتم
            - clearbans --> مسح المظورين
            - clearmutes  --> مسح الكتم
            - help --> لعرض قائمة الاوامر
            **تمت برمجة هذا البوت بواسطة فريق fallt للخدمات التقنية  يقوم بتامين المجموعات ويتيح لك فرصة تحكم افضل فيها.. تواصل مع tarek2016r للمزيد من التفاصيل ** 
            """
        reply_message = commands_list.strip()
    else:
        pass
        #reply_message = 'Invalid command. Type "help" to view available commands.'
    '''else:
        pass
        #reply_message = 'You do not have permission to use this bot.'''

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
def get_user_info(user_id):
    try:
        # Fetch the user's profile information
        user_profile = line_bot_api.get_profile(user_id)
        
        # Extract relevant user information
        user_info = {
            "User ID": user_profile.user_id,
            "Display Name": user_profile.display_name,
            "Profile Picture": user_profile.picture_url if user_profile.picture_url else "No picture",
            "Status Message": user_profile.status_message if user_profile.status_message else "No status message"
        }

        # Format the user information as a message
        user_info_message = f"""
        معلومات المستخدم:
        - المعرف: {user_info['User ID']}
        - الاسم: {user_info['Display Name']}
        - صورة الملف الشخصي: {user_info['Profile Picture']}
        - رسالة الحالة: {user_info['Status Message']}
        """

        return user_info_message.strip()
  
    except LineBotApiError as e:
        return f"حدث خطأ أثناء جلب معلومات المستخدم: {str(e)}"

def send_user_info(reply_token, user_id):
    # Get user information
    user_info_message = get_user_info(user_id)
    
    # Reply with the user information
    line_bot_api.reply_message(reply_token, TextSendMessage(text=user_info_message))

def invite_all_group_members(group_id):
    try:
        # Fetch the list of group member IDs
        member_ids_res = line_bot_api.get_group_member_ids(group_id)
        member_ids = member_ids_res.member_ids

        # Invite message (customize the message as per your requirement)
        invite_message = """
        📞 لقد بدأ المسؤول مكالمة في المجموعة. انضم الآن للتحدث مع الجميع!
        """

        # Loop through each member and send the invite
        for member_id in member_ids:
            try:
                # Send the invite message to each member
                line_bot_api.push_message(member_id, TextSendMessage(text=invite_message.strip()))
            except LineBotApiError as e:
                print(f"Error sending invite to {member_id}: {str(e)}")
        
        print(f"Invites sent to {len(member_ids)} group members.")
    
    except LineBotApiError as e:
        print(f"Error fetching group members: {str(e)}")


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()

    if user_id in ADMIN_USER_ID:
        if text == 'startcall':
            invite_all_group_members(event.source.group_id)
            reply_message = 'Invitations sent to all group members.'
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 8000)))

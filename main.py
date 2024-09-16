# main.py

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# Replace with your Channel Access Token and Channel Secret
CHANNEL_ACCESS_TOKEN = "Unf0b9ICHqvFgfhblpqW57DPTAJ2jCHnzZcyKEjvKVr1iTg1Ct2mgvBvm/hZCCVGirwsfoUarTU3LfEQfWnRJnmbR+blfUCgWo9mfeDCTKr7aSBad4kEWpESvSS5GcuoljPlHdfp7+CXkfXsxkAimwdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "5f5fcbbef8fde3cc12ed90bf01642f35"

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
    try:
        user_profile = line_bot_api.get_profile(user_id)
        display_name = user_profile.display_name
    except LineBotApiError as e:
        reply_message = f"خطأ أثناء جلب معلومات المستخدم: {str(e)}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        return

    # تخزين المستخدم في قاعدة البيانات
    store_user(user_id, display_name)

    # التحقق من الأوامر
    if text.startswith('getid'):
        if event.source.type == 'group':
            if event.message.mention:  # إذا تم ذكر مستخدم
                mentioned_user_id = event.message.mention[0].user_id
                reply_message = f"معرف المستخدم المذكور هو: {mentioned_user_id}"
            elif event.message.reply_to_message:  # إذا كان هناك رد على رسالة
                replied_user_id = event.message.reply_to_message.sender_id
                reply_message = f"معرف المستخدم الذي تم الرد عليه هو: {replied_user_id}"
            else:
                reply_message = "يرجى الرد على رسالة المستخدم أو ذكره للحصول على معرفه."
        else:
            reply_message = "يمكن استخدام هذا الأمر فقط داخل المجموعات."
    
    elif text.startswith('ban'):
        target_user = text.split(' ')[1]
        ban_user(target_user)
        reply_message = f"تم حظر المستخدم {target_user}."

    elif text.startswith('unban'):
        target_user = text.split(' ')[1]
        unban_user(target_user)
        reply_message = f"تم رفع الحظر عن المستخدم {target_user}."

    elif text.startswith('mute'):
        mute_group(event.source.group_id)
        reply_message = "تم كتم المجموعة."

    elif text.startswith('unmute'):
        unmute_group(event.source.group_id)
        reply_message = "تم إلغاء الكتم عن المجموعة."

    elif text.startswith('checkban'):
        target_user = text.split(' ')[1]
        check_ban(event.reply_token, target_user)
        return

    elif text.startswith('checkmute'):
        check_mute(event.reply_token, event.source.group_id)
        return

    elif text.startswith('listbans'):
        reply_message = f"قائمة المستخدمين المحظورين: {', '.join(BANNED_USERS)}"

    elif text.startswith('listmutes'):
        reply_message = f"قائمة المجموعات المكتمة: {', '.join(MUTED_GROUPS)}"

    elif text.startswith('clearbans'):
        clear_bans()
        reply_message = "تم مسح جميع الحظورات."

    elif text.startswith('clearmutes'):
        clear_mutes()
        reply_message = "تم مسح جميع حالات الكتم."

    elif text.startswith('help'):
        commands_list = """
        الأوامر المتاحة:
        - getid --> لجلب معرف المستخدم عن طريق الرد عليه أو ذكره
        - ban [user_id] --> لحظر المستخدم
        - unban [user_id] --> لرفع الحظر عن المستخدم
        - mute --> لكتم المجموعة
        - unmute --> لإلغاء الكتم عن المجموعة
        - checkban [user_id] --> للتحقق من حظر المستخدم
        - checkmute --> للتحقق من حالة الكتم في المجموعة
        - listbans --> عرض قائمة المحظورين
        - listmutes --> عرض قائمة المجموعات المكتمة
        - clearbans --> مسح جميع الحظورات
        - clearmutes --> مسح جميع حالات الكتم
        - help --> لعرض قائمة الأوامر
        """
        reply_message = commands_list.strip()

    else:
        reply_message = "الأمر غير معروف. استخدم 'help' لعرض الأوامر المتاحة."

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
        reply_message = "المستخدم محظور."
    else:
        reply_message = "المستخدم غير محظور."
    line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_message))


def check_mute(reply_token, group_id):
    if group_id in MUTED_GROUPS:
        reply_message = "المجموعة مكتومة."
    else:
        reply_message = "المجموعة غير مكتومة."
    line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_message))


def clear_bans():
    BANNED_USERS.clear()


def clear_mutes():
    MUTED_GROUPS.clear()

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

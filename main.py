from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

# إعدادات البوت من المتغيرات البيئية
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
openai.api_key = "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"

# الكلمة المفتاحية المطلوبة
KEYWORD = "fallt"

# دالة معالجة الرسائل وإرسالها إلى ChatGPT
def get_chatgpt_response(user_message):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=user_message,
        max_tokens=150
    )
    return response.choices[0].text.strip()

# استقبال الرسائل من LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# التعامل مع الرسائل النصية
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()

    # التحقق من الكلمة المفتاحية
    if user_message.startswith(KEYWORD):
        query = user_message[len(KEYWORD):].strip()
        chatgpt_response = get_chatgpt_response(query)

        # إرسال الرد إلى المستخدم
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=chatgpt_response)
        )

# تشغيل التطبيق
if __name__ == "__main__":
    app.run(port=5000)

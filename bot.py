import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

CHANNEL_SECRET = "9ef56154acaef4cda842d2ff5036e0e0"
CHANNEL_ACCESS_TOKEN = "KDSIkldHyYfhRMRkzjk/Rqfg8Ta93aX8Q6aXPuYQbetNTTgpNt5gYQgjac1hLPxfXy8UriqYRqVRnulzMmOQf257yjSZA9xMS3TWbj88Lh7ZChwNRAQjRCVKWz0EV8aEBQdVxI5582jk1VUUbV+SXwdB04t89/1O/w1cDnyilFU="

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 關鍵字自動回覆
KEYWORDS = {
    "報價": "感謝您的詢問！NextFrame AI Studio 提供客製化 AI 影片製作服務，報價依專案需求而定。請提供您的需求細節，我們會盡快與您聯繫 🎬",
    "價格": "感謝您的詢問！NextFrame AI Studio 提供客製化 AI 影片製作服務，報價依專案需求而定。請提供您的需求細節，我們會盡快與您聯繫 🎬",
    "費用": "感謝您的詢問！NextFrame AI Studio 提供客製化 AI 影片製作服務，報價依專案需求而定。請提供您的需求細節，我們會盡快與您聯繫 🎬",
    "合作": "感謝您對 NextFrame AI Studio 的興趣！歡迎告訴我們您的合作需求，我們會盡快安排時間詳談 😊",
    "服務": "NextFrame AI Studio 提供以下服務：\n🎬 AI 影片製作\n📸 AI 形象照\n🎨 品牌視覺設計\n📱 社群內容製作\n\n詳情請參考：https://next-frame.ai",
    "作品": "歡迎參考我們的作品集！\n🌐 https://next-frame.ai\n📸 IG: ig.ai-film.ai\n📘 FB: fb.ai-film.ai",
    "聯絡": "您可以透過以下方式聯絡我們：\n📧 Email: ai@next-frame.ai\n💬 LINE: @910mvqdn\n🌐 https://next-frame.ai",
    "謝謝": "不客氣！有任何問題歡迎隨時詢問 😊",
    "hello": "Hello! 歡迎聯絡 NextFrame AI Studio 🎬 請問有什麼可以幫您的嗎？",
    "hi": "Hi！歡迎聯絡 NextFrame AI Studio 🎬 請問有什麼可以幫您的嗎？",
}

DEFAULT_REPLY = """您好！感謝您聯絡 NextFrame AI Studio 🎬

我們是專業的 AI 影片製作團隊，提供：
• AI 影片製作
• AI 形象照
• 品牌視覺設計

我們已收到您的訊息，將盡快與您聯繫！

歡迎瀏覽我們的作品：
🌐 https://next-frame.ai"""


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    # LINE Verify 會發空白 body，直接回 200
    if not body:
        return "OK", 200

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text.strip()

    reply_text = None
    for keyword, response in KEYWORDS.items():
        if keyword.lower() in user_message.lower():
            reply_text = response
            break

    if not reply_text:
        reply_text = DEFAULT_REPLY

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)

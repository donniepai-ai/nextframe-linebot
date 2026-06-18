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
    "報價": """感謝您的詢問！💰

NextFrame AI Studio 提供兩種服務模式：

🎬 **客製化影片製作**
— 依專案內容、長度、複雜度報價
— 完全 AI 生成，無需實拍現場

🛠 **AI 工具導入服務**
— 協助企業建立自己的 AI 影片生成流程
— 依需求客製化方案

費用依專案而定，歡迎告訴我們您的需求，我們會盡快提供報價！
📧 ai@next-frame.ai
🌐 https://next-frame.ai""",

    "價格": """感謝您的詢問！💰

NextFrame AI Studio 採客製化報價，費用依專案規模、影片長度與需求而定。

歡迎提供以下資訊，我們會盡快給您報價：
1. 影片用途（廣告、社群、產品展示等）
2. 預計長度
3. 預計數量
4. 希望的交件時程

📧 ai@next-frame.ai
🌐 https://next-frame.ai""",

    "費用": """感謝您的詢問！💰

NextFrame AI Studio 採客製化報價，費用依專案規模、影片長度與需求而定。

歡迎提供以下資訊，我們會盡快給您報價：
1. 影片用途（廣告、社群、產品展示等）
2. 預計長度
3. 預計數量
4. 希望的交件時程

📧 ai@next-frame.ai
🌐 https://next-frame.ai""",

    "時間": """關於製作時程 ⏱

NextFrame AI Studio 的製作時間依專案規模而定：
• 小型專案（社群短影片）：約 3–5 個工作天
• 中型專案（品牌廣告）：約 1–2 週
• 大型專案（系列影片/工具導入）：依需求評估

歡迎告訴我們您的需求與期望交件日，我們會盡力配合！
📧 ai@next-frame.ai""",

    "多久": """關於製作時程 ⏱

製作時間依專案規模而定：
• 小型專案（社群短影片）：約 3–5 個工作天
• 中型專案（品牌廣告）：約 1–2 週
• 大型專案（系列影片/工具導入）：依需求評估

歡迎詳細告訴我們您的需求！
📧 ai@next-frame.ai""",

    "案例": """以下是 NextFrame AI Studio 的合作案例 🏆

🖥 **XPG（威剛科技）**
— AI 產品 ASMR 影片、品牌視覺內容

🏛 **台南市政府**
— 政府形象宣傳影片

💻 **華碩 ASUS**
— 品牌 AI 影片製作

📱 **華為 Huawei**
— 產品展示影片

💎 **卡地亞 Cartier**
— 精品品牌視覺影片

🎵 **AI MV 作品欣賞**
▶️ https://youtu.be/jmsbxRXWTho
▶️ https://youtu.be/loFRnmVsMsA

🎬 **AI 影集**
▶️ https://youtu.be/atHjDWnEMHA

更多作品請參考：
🌐 https://next-frame.ai/#portfolio
📸 IG: ig.ai-film.ai""",

    "客戶": """以下是 NextFrame AI Studio 的合作品牌 🏆

XPG（威剛科技）、台南市政府、華碩 ASUS、華為 Huawei、卡地亞 Cartier

我們服務橫跨科技、政府、精品等多元產業，提供全 AI 影片製作解決方案。

更多作品：🌐 https://next-frame.ai""",

    "作品": """歡迎參考 NextFrame AI Studio 的作品集！🎬

🎵 **AI MV 作品**
▶️ https://youtu.be/jmsbxRXWTho
▶️ https://youtu.be/loFRnmVsMsA

🎬 **AI 影集**
▶️ https://youtu.be/atHjDWnEMHA

🌐 **完整作品集**
👉 https://next-frame.ai/#portfolio

📰 **媒體報導**
👉 https://next-frame.ai/press

合作品牌包含：
🏆 XPG、台南市政府、華碩、華為、卡地亞

📸 IG：ig.ai-film.ai
📘 FB：fb.ai-film.ai""",

    "服務": """NextFrame AI Studio 提供以下服務 🎬

**🎥 客製化 AI 影片製作**
• 產品展示影片
• 品牌廣告影片
• 社群短影片
• AI ASMR 影片
• 形象宣傳片

**🎵 AI 音樂製作**
• AI 作曲 + 作詞
• AI MV 製作
• 專輯封面視覺

**🛠 AI 工具導入服務**
• 企業 AI 影片生成流程建置
• 客製化 AI 工具開發
👉 https://next-frame.ai/#tools

📧 ai@next-frame.ai
🌐 https://next-frame.ai""",

    "合作": """感謝您對 NextFrame AI Studio 的興趣！😊

我們已服務 XPG、台南市政府、華碩、華為、卡地亞等品牌，提供專業 AI 影片製作服務。

歡迎告訴我們您的合作需求，我們會盡快安排時間詳談：
📧 ai@next-frame.ai
💬 LINE：@910mvqdn
🌐 https://next-frame.ai""",

    "實拍": """NextFrame AI Studio 專注於純 AI 影片製作 🤖

我們的影片完全由 AI 生成，不需要傳統攝影棚或實拍現場，因此：
✅ 製作成本更低
✅ 製作速度更快
✅ 可快速修改調整
✅ 風格多元豐富

有興趣了解更多？歡迎聯絡我們！
📧 ai@next-frame.ai""",

    "聯絡": """歡迎透過以下方式聯絡 NextFrame AI Studio 📬

📧 Email：ai@next-frame.ai
💬 LINE：@910mvqdn
🌐 官網：https://next-frame.ai
📸 IG：ig.ai-film.ai
📘 FB：fb.ai-film.ai

我們會盡快回覆您！""",

    "工具": """NextFrame AI Studio — AI 工具服務 🛠

我們提供企業 AI 工具導入與客製化開發：

🔧 **企業 AI 工具導入**
• 幫助企業建立自己的 AI 影片生成流程
• 客製化 AI 工具開發
• 員工 AI 使用培訓

👉 了解更多：https://next-frame.ai/#tools

費用依需求規模而定，歡迎洽詢！
📧 ai@next-frame.ai
🌐 https://next-frame.ai""",

    "導入": """NextFrame AI Studio — AI 工具導入服務 🛠

協助企業快速建立 AI 影片製作流程：
✅ 需求評估與規劃
✅ 客製化 AI 工具開發
✅ 教育訓練與支援

👉 https://next-frame.ai/#tools

📧 ai@next-frame.ai""",

    "音樂": """NextFrame AI Studio — AI 音樂製作 🎵

**用 AI 作曲，用故事作詞。**

我們提供完整的 AI 音樂製作服務：
🎤 AI 歌曲創作（作曲 + 作詞）
🎬 AI MV 製作
🎨 專輯封面視覺設計

✨ **合作藝人作品**
• STELLAR5 —《我依然是你的情人》
• YUII —《桜が降る》《Beyond the Tide》《MY MOVIE》《SIGNAL》
• YUII & LILI —《YOU & ME》
• Donnie Ai —《Shining Bright》

🎵 收聽作品：
▶️ https://youtu.be/jmsbxRXWTho
▶️ https://youtu.be/loFRnmVsMsA

📧 ai@next-frame.ai
🌐 https://next-frame.ai""",

    "作曲": """NextFrame AI Studio — AI 音樂製作 🎵

**用 AI 作曲，用故事作詞。**

提供完整 AI 音樂製作：
🎤 AI 作曲 + 作詞
🎬 AI MV 製作
🎨 專輯封面視覺

費用依專案而定，歡迎洽詢！
📧 ai@next-frame.ai
🌐 https://next-frame.ai""",

    "歌曲": """NextFrame AI Studio — AI 音樂製作 🎵

**用 AI 作曲，用故事作詞。**

提供完整 AI 音樂製作：
🎤 AI 作曲 + 作詞
🎬 AI MV 製作
🎨 專輯封面視覺

費用依專案而定，歡迎洽詢！
📧 ai@next-frame.ai
🌐 https://next-frame.ai""",

    "獲獎": """NextFrame AI Studio 國際獲獎紀錄 🏆

🥇 **SIGNAL**（Music Video）
— MetaMorph AI Film Award 2026 · **Award 獲獎**
— YUII × NextFrame AI Studio

🎬 **SIGNAL**（AI Drama Series）
— MetaMorph AI Film Award 2026 · **Official Selection 官方入選**

🎞 **LADY**（AI Short Film）
— MetaMorph Award 2026 · **Shortlist 入圍**
— 10分鐘 AI 犯罪動作短片

NextFrame 作品近期於國際 AI 影像獎項的認可 🌍

🌐 https://next-frame.ai""",

    "獎": """NextFrame AI Studio 國際獲獎紀錄 🏆

🥇 **SIGNAL**（Music Video）· MetaMorph AI Film Award 2026 獲獎
🎬 **SIGNAL**（AI Drama Series）· MetaMorph AI Film Award 2026 官方入選
🎞 **LADY**（AI Short Film）· MetaMorph Award 2026 入圍

🌐 https://next-frame.ai""",

    "入圍": """NextFrame AI Studio 國際獲獎紀錄 🏆

🥇 **SIGNAL**（Music Video）· MetaMorph AI Film Award 2026 獲獎
🎬 **SIGNAL**（AI Drama Series）· MetaMorph AI Film Award 2026 官方入選
🎞 **LADY**（AI Short Film）· MetaMorph Award 2026 入圍

🌐 https://next-frame.ai""",

    "媒體": """NextFrame AI Studio 媒體報導 📰

👉 https://next-frame.ai/press

我們的 AI 影片製作技術與作品受到多家媒體關注報導！""",

    "報導": """NextFrame AI Studio 媒體報導 📰

👉 https://next-frame.ai/press

我們的 AI 影片製作技術與作品受到多家媒體關注報導！""",

    "謝謝": "不客氣！有任何問題歡迎隨時詢問 😊",
    "謝": "不客氣！有任何問題歡迎隨時詢問 😊",
    "hello": "Hello! 歡迎聯絡 NextFrame AI Studio 🎬 請問有什麼可以幫您的嗎？",
    "hi": "Hi！歡迎聯絡 NextFrame AI Studio 🎬 請問有什麼可以幫您的嗎？",
    "你好": "您好！歡迎聯絡 NextFrame AI Studio 🎬 請問有什麼可以幫您的嗎？",
    "哈囉": "哈囉！歡迎聯絡 NextFrame AI Studio 🎬 請問有什麼可以幫您的嗎？",
}

DEFAULT_REPLY = """您好！感謝您聯絡 NextFrame AI Studio 🎬

我們是專業的 AI 影片製作團隊，合作品牌包含：
XPG、台南市政府、華碩、華為、卡地亞

服務項目：
🎬 客製化 AI 影片製作
🛠 企業 AI 工具導入

我們已收到您的訊息，將盡快與您聯繫！

您也可以輸入以下關鍵字快速查詢：
「服務」「報價」「案例」「時間」「聯絡」

🌐 https://next-frame.ai"""


@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)

    if not body or not body.strip():
        return "OK", 200

    try:
        import json
        data = json.loads(body)
        events = data.get("events", [])

        # Verify 測試（空 events）直接回 200
        if not events:
            return "OK", 200

        # 處理每個事件
        for event in events:
            if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                reply_token = event.get("replyToken")
                user_message = event.get("message", {}).get("text", "").strip()

                reply_text = None
                for keyword, response in KEYWORDS.items():
                    if keyword.lower() in user_message.lower():
                        reply_text = response
                        break
                if not reply_text:
                    reply_text = DEFAULT_REPLY

                # 發送回覆
                import requests as req
                req.post(
                    "https://api.line.me/v2/bot/message/reply",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    },
                    json={
                        "replyToken": reply_token,
                        "messages": [{"type": "text", "text": reply_text}]
                    }
                )
    except Exception as e:
        print(f"Error: {e}")

    return "OK", 200


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

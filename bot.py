import os
import json
import requests
from flask import Flask, request, abort

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

SYSTEM_PROMPT = """你是 NextFrame AI Studio 的客服助理，負責用繁體中文回答客戶的問題。請保持友善、專業，回覆簡潔有重點。

## 關於 NextFrame AI Studio

**公司簡介：**
NextFrame AI Studio 是台灣專業的 AI 影片製作公司，由白導（Donnie Pai）創辦。
官網：https://next-frame.ai

**服務項目：**
1. 🎥 客製化 AI 影片製作（產品展示、品牌廣告、社群短影片、AI ASMR、形象宣傳片）
2. 🎵 AI 音樂製作（AI 作曲 + 作詞、AI MV 製作、專輯封面視覺）
3. 🛠 企業 AI 工具導入（建置 AI 影片生成流程、客製化工具開發）
   → 了解更多：https://next-frame.ai/#tools

**費用與時程：**
- 採客製化報價，依專案規模、長度、需求而定
- 製作時間：小型專案 3-5 個工作天，中型 1-2 週，大型依需求評估
- 歡迎提供需求細節以獲得報價

**合作品牌案例：**
XPG（威剛科技）、台南市政府、華碩 ASUS、華為 Huawei、卡地亞 Cartier

**AI 音樂合作藝人：**
STELLAR5、YUII、YUII & LILI、Donnie Ai

**作品集：**
- 完整作品集：https://next-frame.ai/#portfolio
- AI MV：https://youtu.be/jmsbxRXWTho
- AI MV：https://youtu.be/loFRnmVsMsA
- AI 影集：https://youtu.be/atHjDWnEMHA

**國際獲獎：**
- SIGNAL（MV）→ MetaMorph AI Film Award 2026 獲獎
- SIGNAL（AI 影集）→ MetaMorph AI Film Award 2026 官方入選
- LADY（AI 短片）→ MetaMorph Award 2026 入圍

**媒體報導：** https://next-frame.ai/press

**聯絡方式：**
- Email：ai@next-frame.ai
- LINE 官方帳號：@910mvqdn
- IG：ig.ai-film.ai
- FB：fb.ai-film.ai

**注意事項：**
- 所有影片皆為純 AI 生成，無需傳統實拍現場
- 如客戶有具體需求，請引導他們提供影片用途、長度、數量，以便報價
- 如需深入洽談，請引導客戶發 Email 至 ai@next-frame.ai 或加 LINE @910mvqdn
"""

def ask_ai(user_message):
    """呼叫 OpenRouter AI API"""
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://next-frame.ai",
                "X-Title": "NextFrame LINE Bot"
            },
            json={
                "model": "anthropic/claude-haiku-4",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 500
            },
            timeout=15
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"AI error: {e}")
        return "您好！感謝聯絡 NextFrame AI Studio 🎬\n\n目前系統稍忙，請稍後再試，或直接聯絡我們：\n📧 ai@next-frame.ai\n💬 LINE：@910mvqdn"

def send_reply(reply_token, text):
    """發送 LINE 回覆"""
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
        },
        json={
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text}]
        }
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)

    if not body or not body.strip():
        return "OK", 200

    try:
        data = json.loads(body)
        events = data.get("events", [])

        if not events:
            return "OK", 200

        for event in events:
            if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                reply_token = event.get("replyToken")
                user_message = event.get("message", {}).get("text", "").strip()

                # 呼叫 AI 生成回覆
                reply_text = ask_ai(user_message)
                send_reply(reply_token, reply_text)

    except Exception as e:
        print(f"Error: {e}")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)

import os
import json
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbw8Kof2QkQ2urbhIzqtYjpd-knEQ5X7qeeJFMxczudKM2WA-DHarbionFDC-ld9ph6e/exec"
TELEGRAM_USER_ID = os.environ.get("TELEGRAM_USER_ID", "862846115")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

SYSTEM_PROMPT = """你是 NextFrame AI Studio 的客服助理，負責用繁體中文回答客戶的問題。請保持友善、專業，回覆簡潔有重點。

## 關於 NextFrame AI Studio

**公司簡介：**
NextFrame AI Studio 是台灣專業的 AI 影片製作公司，由白導（Donnie Pai）創辦。
官網：https://next-frame.ai

**服務項目：**
1. 🎥 客製化 AI 影片製作（產品展示、品牌廣告、社群短影片、AI ASMR、形象宣傳片）
2. 🎵 AI 音樂製作（AI 作曲 + 作詞、AI MV 製作、專輯封面視覺）
3. 🛠 企業 AI 工具導入（建置 AI 影片生成流程、客製化工具開發）

**費用與時程：**
- 採客製化報價，依專案規模、長度、需求而定
- 製作時間：小型專案 3-5 個工作天，中型 1-2 週，大型依需求評估

**合作品牌案例：**
XPG（威剛科技）、台南市政府、華碩 ASUS、華為 Huawei、卡地亞 Cartier

**聯絡方式：**
- Email：ai@next-frame.ai
- LINE 官方帳號：@910mvqdn
"""

def send_reply(reply_token, text):
    """發送 LINE 回覆"""
    try:
        requests.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
            },
            json={
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": text}]
            },
            timeout=5
        )
        print("✅ Reply sent")
    except Exception as e:
        print(f"❌ Send reply error: {e}")

def is_booking_request(text):
    """檢查是否是預約請求"""
    booking_keywords = ["預約", "訂位", "預訂"]
    return any(keyword in text for keyword in booking_keywords)

def parse_booking_info(text):
    """解析預約資訊"""
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    
    if len(lines) < 5:
        return None
    
    name = lines[0]
    phone = lines[1]
    date_str = lines[2]
    time_str = lines[3]
    service = lines[4]
    
    # 驗證日期格式 (YYYY-MM-DD)
    if len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
        return None
    
    # 驗證時間格式 (HH:MM)
    if ':' not in time_str or len(time_str) != 5:
        return None
    
    return {
        'name': name,
        'phone': phone,
        'date': date_str,
        'time': time_str,
        'service': service
    }

def save_booking_to_sheet(user_id, booking_info):
    """存預約到 Google Sheets"""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        requests.post(GOOGLE_SHEET_URL, json={
            "action": "booking",
            "userId": user_id,
            "bookingTime": now,
            "name": booking_info.get('name', ''),
            "phone": booking_info.get('phone', ''),
            "date": booking_info.get('date', ''),
            "time": booking_info.get('time', ''),
            "service": booking_info.get('service', '')
        }, timeout=5)
        print("✅ Booking saved to sheet")
    except Exception as e:
        print(f"❌ Sheet error: {e}")

def notify_telegram(booking_info):
    """通知 Telegram"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            return
        
        message = f"""🎉 新預約通知

客戶名稱: {booking_info.get('name', 'N/A')}
電話: {booking_info.get('phone', 'N/A')}
預約日期: {booking_info.get('date', 'N/A')}
預約時間: {booking_info.get('time', 'N/A')}
服務項目: {booking_info.get('service', 'N/A')}
"""
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_USER_ID,
                "text": message
            },
            timeout=5
        )
        print("✅ Telegram notified")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def ask_ai(user_message):
    """呼叫 AI API"""
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
                "model": "anthropic/claude-haiku-4-5",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 300
            },
            timeout=10
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ AI error: {e}")
        return "感謝聯絡！請稍後再試或聯絡我們：ai@next-frame.ai"

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)
    print(f"Received: {body}")
    
    try:
        data = json.loads(body)
        events = data.get("events", [])
        
        for event in events:
            event_type = event.get("type")
            
            if event_type == "message":
                reply_token = event.get("replyToken")
                user_id = event.get("source", {}).get("userId", "")
                user_message = event.get("message", {}).get("text", "").strip()
                
                print(f"Message: {user_message}")
                
                # 檢查是否是預約
                if is_booking_request(user_message):
                    booking_info = parse_booking_info(user_message)
                    if booking_info:
                        # 保存預約
                        save_booking_to_sheet(user_id, booking_info)
                        notify_telegram(booking_info)
                        
                        reply_text = f"""✅ 預約成功！

感謝 {booking_info.get('name')} 的預約！

📋 預約詳情：
• 日期：{booking_info.get('date')}
• 時間：{booking_info.get('time')}
• 服務：{booking_info.get('service')}
• 電話：{booking_info.get('phone')}

我們會盡快與您聯繫！"""
                    else:
                        reply_text = """📝 預約格式錯誤，請按以下格式：

你的名字
電話號碼
日期（2026-06-22）
時間（14:00）
服務項目"""
                else:
                    # 一般問題，呼叫 AI
                    reply_text = ask_ai(user_message)
                
                send_reply(reply_token, reply_text)
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return "OK", 200

@app.route("/webhook/cal", methods=["POST"])
def webhook_cal():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)

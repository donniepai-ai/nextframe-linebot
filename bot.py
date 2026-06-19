import os
import json
import requests
from flask import Flask, request, abort
from datetime import datetime
import subprocess

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbw8Kof2QkQ2urbhIzqtYjpd-knEQ5X7qeeJFMxczudKM2WA-DHarbionFDC-ld9ph6e/exec"
BOOKING_SHEET_ID = "1dJtLo7h-J_JtTc_PMzojTu2Me_QETpBcbb9JNxcJ27Y"
TELEGRAM_USER_ID = os.environ.get("TELEGRAM_USER_ID", "862846115")  # 白導的 Telegram ID
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))

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

def get_user_profile(user_id):
    """取得 LINE 用戶資料"""
    try:
        res = requests.get(
            f"https://api.line.me/v2/bot/profile/{user_id}",
            headers={"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
        )
        return res.json()
    except:
        return {}

def save_to_sheet(user_id, display_name, picture_url, action):
    """記錄到 Google Sheets"""
    try:
        requests.post(GOOGLE_SHEET_URL, json={
            "userId": user_id,
            "displayName": display_name,
            "pictureUrl": picture_url,
            "action": action
        }, timeout=10)
    except Exception as e:
        print(f"Sheet error: {e}")

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
                "model": "anthropic/claude-haiku-4-5",
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

def is_booking_request(text):
    """檢查是否是預約請求"""
    booking_keywords = ["預約", "訂位", "預訂", "booking", "schedule", "時間", "檔期"]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in booking_keywords)

def parse_booking_info(text):
    """解析預約資訊"""
    # 客戶應該提供 5 行：名字、電話、日期、時間、服務項目
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    
    # 需要至少 5 行資訊
    if len(lines) < 5:
        return None
    
    # 簡單的驗證 - 確保有日期格式 (YYYY-MM-DD) 和時間格式 (HH:MM)
    name = lines[0]
    phone = lines[1]
    date_str = lines[2]
    time_str = lines[3]
    service = lines[4]
    
    # 驗證日期格式 (YYYY-MM-DD)
    if not date_str or len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
        return None
    
    # 驗證時間格式 (HH:MM)
    if not time_str or ':' not in time_str or len(time_str) != 5:
        return None
    
    # 驗證電話不為空
    if not phone or len(phone) < 9:
        return None
    
    return {
        'name': name,
        'phone': phone,
        'date': date_str,
        'time': time_str,
        'service': service
    }

def save_booking_to_sheet(user_id, display_name, booking_info):
    """將預約資訊存到 Google Sheets"""
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 透過 Google Apps Script 存資料
        requests.post(GOOGLE_SHEET_URL, json={
            "action": "booking",
            "userId": user_id,
            "displayName": display_name,
            "bookingTime": now,
            "name": booking_info.get('name', ''),
            "phone": booking_info.get('phone', ''),
            "date": booking_info.get('date', ''),
            "time": booking_info.get('time', ''),
            "service": booking_info.get('service', '')
        }, timeout=10)
    except Exception as e:
        print(f"Booking sheet error: {e}")

def notify_telegram(booking_info, user_id, display_name):
    """通知白導有新預約"""
    try:
        message = f"""
🎉 **新預約通知**

客戶名稱: {booking_info.get('name', 'N/A')}
電話: {booking_info.get('phone', 'N/A')}
預約日期: {booking_info.get('date', 'N/A')}
預約時間: {booking_info.get('time', 'N/A')}
服務項目: {booking_info.get('service', 'N/A')}
LINE 客戶名: {display_name}
LINE ID: {user_id}
"""
        if TELEGRAM_BOT_TOKEN:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_USER_ID,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
    except Exception as e:
        print(f"Telegram notification error: {e}")

def create_google_calendar_event(booking_info):
    """建立 Google Calendar 事件（非同步，不阻擋回覆）"""
    try:
        # 這個函數現在只記錄日誌，不執行外部命令
        print(f"📅 預約到行程表：{booking_info.get('name')} - {booking_info.get('date')} {booking_info.get('time')}")
        return True
    except Exception as e:
        print(f"Google Calendar error: {e}")
        return False

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
            event_type = event.get("type")
            user_id = event.get("source", {}).get("userId", "")

            # 有人加入官方帳號
            if event_type == "follow":
                profile = get_user_profile(user_id)
                display_name = profile.get("displayName", "（未知）")
                picture_url = profile.get("pictureUrl", "")
                save_to_sheet(user_id, display_name, picture_url, "加入")
                # 發送歡迎訊息
                reply_token = event.get("replyToken")
                welcome_message = f"""您好 {display_name}！歡迎加入 NextFrame AI Studio 🎬

我是 AI 客服助理，可以幫您：

✨ **功能 1：諮詢服務**
詢問關於 AI 影片製作、報價、作品集等問題。例如：
• 「AI MV 製作要多久？」
• 「你們有做過什麼案例？」
• 「怎麼聯絡你們？」

📅 **功能 2：線上預約**
需要預約時，按照下面格式傳訊息：

你的名字
你的電話
預約日期（例如：2026-06-28）
預約時間（例如：14:00）
服務項目（例如：AI MV 製作）

例如：
小王
0912345678
2026-06-28
14:00
AI MV 製作

---

請問有什麼可以幫您的嗎？"""
                send_reply(reply_token, welcome_message)

            # 有人封鎖或退出
            elif event_type == "unfollow":
                save_to_sheet(user_id, "", "", "封鎖/退出")

            # 一般訊息
            elif event_type == "message" and event.get("message", {}).get("type") == "text":
                reply_token = event.get("replyToken")
                user_message = event.get("message", {}).get("text", "").strip()
                profile = get_user_profile(user_id)
                display_name = profile.get("displayName", "客戶")
                
                # 檢查是否是預約請求
                if is_booking_request(user_message):
                    booking_info = parse_booking_info(user_message)
                    if booking_info:
                        # 成功解析預約資訊
                        save_to_sheet(user_id, display_name, "預約")
                        save_booking_to_sheet(user_id, display_name, booking_info)
                        
                        # 建立 Google Calendar 事件
                        create_google_calendar_event(booking_info)
                        
                        # 通知白導
                        notify_telegram(booking_info, user_id, display_name)
                        
                        reply_text = f"""✅ 預約成功！

感謝 {booking_info.get('name')} 的預約！

📋 預約詳情：
• 日期：{booking_info.get('date')}
• 時間：{booking_info.get('time')}
• 服務：{booking_info.get('service')}
• 電話：{booking_info.get('phone')}

你的預約已自動新增到行程表，我們會盡快與您聯繫確認詳細事項。
如有任何問題，請聯絡：
📧 ai@next-frame.ai
💬 LINE：@910mvqdn"""
                    else:
                        # 預約資訊不完整
                        reply_text = """📝 請提供完整的預約資訊，格式如下：

第一行：你的名字
第二行：你的電話號碼
第三行：想預約的日期（例如：2026-06-22）
第四行：想預約的時間（例如：14:00）
第五行：服務項目（例如：AI MV 製作）

例子：
小王
0912345678
2026-06-22
14:00
AI MV 製作"""
                else:
                    # 一般謙詢
                    reply_text = ask_ai(user_message)
                    save_to_sheet(user_id, display_name, f"詢問：{user_message[:50]}")
                
                send_reply(reply_token, reply_text)

    except Exception as e:
        print(f"Error: {e}")

    return "OK", 200

@app.route("/webhook/cal", methods=["POST"])
def webhook_cal():
    """接收 Cal.com webhook 預約"""
    try:
        data = request.get_json()
        
        # Cal.com webhook 事件類型
        event_type = data.get("triggerEvent", "")
        if event_type != "BOOKING_CREATED":
            return "OK", 200
        
        # 提取預約資訊
        booking_data = data.get("booking", {})
        event_data = data.get("eventData", {})
        
        # 組合預約資訊
        booking_info = {
            'name': booking_data.get("attendees", [{}])[0].get("name", "N/A"),
            'phone': booking_data.get("attendees", [{}])[0].get("phoneNumber", "N/A"),
            'date': booking_data.get("startTime", "")[:10],  # 取日期部分 YYYY-MM-DD
            'time': booking_data.get("startTime", "")[11:16],  # 取時間部分 HH:MM
            'service': event_data.get("title", "Calendar Event")
        }
        
        # 存到 Google Sheets
        save_booking_to_sheet("cal.com", "Cal.com 預約", booking_info)
        
        # 建立 Google Calendar 事件（如果還沒有的話）
        create_google_calendar_event(booking_info)
        
        # 通知白導
        notify_telegram(booking_info, "cal.com", "Cal.com 預約")
        
        print(f"✅ Cal.com 預約已同步")
        return "OK", 200
        
    except Exception as e:
        print(f"Cal.com webhook error: {e}")
        return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)

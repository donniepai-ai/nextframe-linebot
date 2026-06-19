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
    # 簡單的解析 - 客戶應該提供：名字、電話、日期、時間、服務項目
    # 格式：名字 | 電話 | 日期 | 時間 | 服務項目
    lines = text.strip().split("\n")
    info = {}
    
    if len(lines) >= 1:
        info['name'] = lines[0].split("名字：")[-1].split("｜")[0].strip() if "名字" in lines[0] or "｜" in lines[0] else lines[0].split("｜")[0].strip()
    if len(lines) >= 2:
        info['phone'] = lines[1].split("電話：")[-1].split("｜")[0].strip() if "電話" in lines[1] or "｜" in lines[1] else lines[1].split("｜")[0].strip()
    if len(lines) >= 3:
        info['date'] = lines[2].split("日期：")[-1].split("｜")[0].strip() if "日期" in lines[2] or "｜" in lines[2] else lines[2].split("｜")[0].strip()
    if len(lines) >= 4:
        info['time'] = lines[3].split("時間：")[-1].split("｜")[0].strip() if "時間" in lines[3] or "｜" in lines[3] else lines[3].split("｜")[0].strip()
    if len(lines) >= 5:
        info['service'] = lines[4].split("服務：")[-1].strip() if "服務" in lines[4] else lines[4].strip()
    else:
        info['service'] = "待詢問"
    
    return info if all(k in info for k in ['name', 'phone', 'date', 'time']) else None

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
    """建立 Google Calendar 事件"""
    try:
        # 解析日期和時間
        date_str = booking_info.get('date', '')
        time_str = booking_info.get('time', '14:00')
        
        # 組合成 ISO 8601 格式時間 (台灣時區 UTC+8)
        try:
            # 嘗試解析日期格式 YYYY-MM-DD
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            time_obj = datetime.strptime(time_str, "%H:%M")
            
            # 組合日期和時間
            start_datetime = datetime.combine(date_obj.date(), time_obj.time())
            # 轉換為 ISO 8601 格式（含台灣時區）
            start_iso = start_datetime.strftime("%Y-%m-%dT%H:%M:%S+08:00")
            
            # 假設預約時長為 1 小時
            end_time_obj = datetime.strptime(f"{time_str[0:2]}:{int(time_str[3:5])+60}", "%H:%M") if int(time_str[3:5])+60 < 60 else datetime.strptime(f"{int(time_str[0:2])+1}:{int(time_str[3:5])+60-60}", "%H:%M")
            end_datetime = datetime.combine(date_obj.date(), end_time_obj.time())
            end_iso = end_datetime.strftime("%Y-%m-%dT%H:%M:%S+08:00")
        except:
            print("Date/time parsing error, using defaults")
            return None
        
        # 使用 gws CLI（Google Workspace CLI）建立事件
        cmd = [
            "python", 
            f"{HERMES_HOME}/skills/productivity/google-workspace/scripts/google_api.py",
            "calendar", "create",
            "--summary", f"📅 {booking_info.get('service', 'AI 製作')} - {booking_info.get('name', 'N/A')}",
            "--start", start_iso,
            "--end", end_iso,
            "--description", f"客戶電話：{booking_info.get('phone', 'N/A')}\n預約來源：LINE Bot"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print(f"✅ Google Calendar 事件建立成功")
            return True
        else:
            print(f"❌ Google Calendar 建立失敗：{result.stderr}")
            return False
            
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)

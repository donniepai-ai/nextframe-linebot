import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN", "")

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

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)
    print(f"Received: {body}")
    
    try:
        data = json.loads(body)
        events = data.get("events", [])
        
        for event in events:
            event_type = event.get("type")
            print(f"Event type: {event_type}")
            
            if event_type == "message":
                reply_token = event.get("replyToken")
                user_message = event.get("message", {}).get("text", "")
                print(f"User message: {user_message}")
                
                # 簡單回覆
                send_reply(reply_token, f"收到：{user_message}\n\n這是測試回覆！")
                
    except Exception as e:
        print(f"Error: {e}")
    
    return "OK", 200

@app.route("/webhook/cal", methods=["POST"])
def webhook_cal():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)

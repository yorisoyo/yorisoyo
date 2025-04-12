from flask import Flask, request
from openai import OpenAI
import requests
import json
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAIクライアントの初期化
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_json()
    events = body.get('events', [])

    for event in events:
        if event.get('type') == 'message' and 'text' in event.get('message', {}):
            user_message = event['message']['text']
            reply_token = event['replyToken']

            # GPT-4 に問い合わせる
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたは『よりそ夜』のAIしずくです。つらい人の話をやさしく聞き、安心できる言葉で返してください。死にたいと言われたら、『あなたの命は大切です』『ここにいていいんですよ』と伝えてください。"},
                    {"role": "user", "content": user_message}
                ]
            )

            reply_text = response.choices[0].message.content

            # LINEに返信
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
            }
            payload = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": reply_text}]
            }

            requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, data=json.dumps(payload))

    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, request
import openai
import requests
import os

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI新SDKクライアント（v1以降）
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 400文字ごとに分割（LINEの安定上限）
def split_message_by_length(message, max_chars=400):
    chunks = [message[i:i + max_chars] for i in range(0, len(message), max_chars)]
    return chunks[:5]  # LINEのreplyは最大5通

@app.route("/callback", methods=['POST'])
def callback():
    try:
        body = request.get_json()
        events = body.get('events', [])

        for event in events:
            if event.get('type') == 'message':
                user_message = event['message']['text']
                reply_token = event['replyToken']

                # GPTへの問い合わせ（OpenAI SDK v1対応）
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "あなたは『よりそ夜』のAIしずくです。つらい人の話をやさしく聞き、安心できる言葉で返してください。死にたいと言われたら、『あなたの命は大切です』『ここにいていいんですよ』と伝えてください。"},
                        {"role": "user", "content": user_message}
                    ]
                )

                reply_text = response.choices[0].message.content
                messages = split_message_by_length(reply_text)

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
                }

                payload = {
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": msg} for msg in messages]
                }

                res = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)
                if res.status_code != 200:
                    print("LINE返信エラー:", res.status_code, res.text)

        return 'OK'

    except Exception as e:
        print("サーバーエラー:", e)
        return 'Internal Server Error', 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

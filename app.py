from flask import Flask, request
import openai
import requests
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 3行ごとに分割し、最大5通まで返す
def split_message_by_lines(message, max_lines=3, max_messages=5):
    lines = message.split('\n')
    chunks = []
    for i in range(0, len(lines), max_lines):
        chunk = '\n'.join(lines[i:i + max_lines])
        chunks.append(chunk)
        if len(chunks) >= max_messages:
            break
    return chunks

@app.route("/callback", methods=['POST'])
def callback():
    try:
        body = request.get_json()
        events = body.get('events', [])

        for event in events:
            if event.get('type') == 'message':
                user_message = event['message']['text']
                reply_token = event['replyToken']

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "あなたは『よりそ夜』のAIしずくです。つらい人の話をやさしく聞き、安心できる言葉で返してください。死にたいと言われたら、『あなたの命は大切です』『ここにいていいんですよ』と伝えてください。"},
                        {"role": "user", "content": user_message}
                    ]
                )

                reply_text = response.choices[0].message.content
                messages = split_message_by_lines(reply_text)

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

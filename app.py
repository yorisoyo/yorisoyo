from flask import Flask, request
import openai
import requests
import os

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 新しいOpenAIクライアント
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 3行分割（最大5件）
def split_message_by_lines(message, lines_per_chunk=3):
    lines = message.split('\n')
    chunks = ['\n'.join(lines[i:i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]
    return chunks[:5]

@app.route("/callback", methods=['POST'])
def callback():
    try:
        body = request.get_json()
        events = body.get('events', [])

        for event in events:
            if event.get('type') == 'message':
                user_message = event['message']['text']
                reply_token = event['replyToken']

                # 新SDK形式でGPTへ問い合わせ
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "あなたは『よりそ夜』のAIしずくです。..."},
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

from flask import Flask, request
import openai
import requests
import os

app = Flask(__name__)

# 環境変数からトークンとキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# 3行ごとにメッセージを分割（最大5メッセージ制限あり）
def split_message_by_lines(message, lines_per_chunk=3):
    lines = message.split('\n')
    chunks = ['\n'.join(lines[i:i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]
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

                # GPT-4へ問い合わせ
                gpt_reply = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "あなたは『よりそ夜』のAIしずくです。つらい人の話をやさしく聞き、安心できる言葉で返してください。死にたいと言われたら、『あなたの命は大切です』『ここにいていいんですよ』と伝えてください。"},
                        {"role": "user", "content": user_message}
                    ]
                )

                reply_text = gpt_reply['choices'][0]['message']['content']
                messages = split_message_by_lines(reply_text)

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
                }

                payload = {
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": msg} for msg in messages]
                }

                # メッセージ送信
                response = requests.post(
                    "https://api.line.me/v2/bot/message/reply",
                    headers=headers,
                    json=payload
                )

                # エラーチェック
                if response.status_code != 200:
                    print("LINE API エラー:", response.status_code, response.text)

        return 'OK'

    except Exception as e:
        print("サーバー内エラー:", e)
        return 'Internal Server Error', 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, request
import openai
import requests
import json
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# 3行ごとにメッセージを分割
def split_message_by_lines(message, lines_per_chunk=3):
    lines = message.split('\n')
    chunks = ['\n'.join(lines[i:i+lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]
    return chunks[:5]  # LINEの仕様上、replyでは最大5通まで

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_json()
    events = body['events']

    for event in events:
        if event['type'] == 'message':
            user_message = event['message']['text']
            reply_token = event['replyToken']

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

            requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, data=json.dumps(payload))

    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

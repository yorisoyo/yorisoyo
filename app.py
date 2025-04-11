
from flask import Flask, request
import openai
import requests
import json

app = Flask(__name__)

# ↓ ここにあなたのAPIキーを貼り付けてね！
LINE_CHANNEL_ACCESS_TOKEN = 'ここにLINEのアクセストークン'
LINE_CHANNEL_SECRET = 'ここにLINEのチャネルシークレット'
OPENAI_API_KEY = 'ここにOpenAIのAPIキー（sk-から始まるやつ）'

openai.api_key = OPENAI_API_KEY

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
    app.run()

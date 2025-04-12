from flask import Flask, request
import openai
import requests
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

app = Flask(__name__)

# 環境変数の読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Google Sheetsログ保存用関数
def log_to_sheet(user_id, message_text):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
　　 credentials_dict = json.loads(credentials_json)
　　 creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("相談ログ").sheet1
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, user_id, message_text])

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_json()
    events = body.get('events', [])

    for event in events:
        if event['type'] == 'message':
            user_message = event['message']['text']
            reply_token = event['replyToken']
            user_id = event['source']['userId']  # ユーザーIDも取得

            log_to_sheet(user_id, user_message)  # ←ここがズレていた！

            gpt_reply = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたは『よりそ夜』のAIしずくです..."},
                    {"role": "user", "content": user_message}
                ]
            )


            reply_text = gpt_reply['choices'][0]['message']['content']

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

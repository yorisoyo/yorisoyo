from flask import Flask, request
import openai
import requests
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 「。」で区切り、200字以内かつ2〜4通に調整
def split_message_by_sentences(text, max_chars=200, min_messages=2, max_messages=4):
    sentences = text.split("。")
    sentences = [s.strip() + "。" for s in sentences if s.strip()]
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) <= max_chars:
            current += sentence
        else:
            if current:
                chunks.append(current.strip())
            current = sentence
        if len(chunks) >= max_messages:
            break
    if current and len(chunks) < max_messages:
        chunks.append(current.strip())

    # 最低2通になるよう調整
    if len(chunks) == 1:
        text = chunks[0]
        midpoint = len(text) // 2
        chunks = [text[:midpoint].strip(), text[midpoint:].strip()]

    return chunks[:max_messages]

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
                        {"role": "system", "content": "あなたは『よりそ夜』のAIしずくです。つらい人の話をやさしく聞き、安心できる言葉で返してください。死にたいと言われたら、『あなたの命は大切です』『ここにいていいんですよ』と伝えてください。返答は200字以内で、文を「。」で区切って自然な形で複数通にしてください。"},
                        {"role": "user", "content": user_message}
                    ]
                )

                reply_text = response.choices[0].message.content
                messages = split_message_by_sentences(reply_text)

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

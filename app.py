import json
import os

import qrcode
from PIL import Image, ImageFont
from PIL import ImageDraw
from uuid import uuid4

from barcode import EAN13, Code128
from barcode.writer import ImageWriter  # 載入 barcode.writer 的 ImageWriter

from flask import Flask, request, abort, render_template, jsonify, redirect
from dotenv import load_dotenv
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage, TemplateMessage, ButtonsTemplate, MessageAction, URIAction, ImageMessage, PostbackAction
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent, PostbackEvent
)

app = Flask(__name__, static_folder='static')
load_dotenv()

configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TemplateMessage(
                        alt_text='功能表',
                        template=ButtonsTemplate(
                            text='請選擇服務項目',
                            actions=[
                                PostbackAction(
                                    label='會員卡',
                                    displayText='顯示會員卡',
                                    data='action=member_card'
                                ),
                            ]
                        )
                    )
                ]
            )
        )


@handler.add(PostbackEvent)
def handle_postback(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        if event.postback.data == 'action=member_card':
            print(event.source)
            name = "王小明"
            uid = event.source.user_id
            gen_member_card(name, uid)

            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        ImageMessage(
                            original_content_url=f"https://sloth-robust-remarkably.ngrok-free.app/static/card/{uid}.png",
                            preview_image_url=f"https://sloth-robust-remarkably.ngrok-free.app/static/card/{uid}.png"
                        ),
                        ImageMessage(
                            original_content_url=f"https://sloth-robust-remarkably.ngrok-free.app/static/card/{uid}_qr.png",
                            preview_image_url=f"https://sloth-robust-remarkably.ngrok-free.app/static/card/{uid}_qr.png"
                        )
                    ]
                )
            )


def gen_member_card(name, uid):
    # Open an Image
    img = Image.open("static/card.png")

    if not os.path.exists("static/card"):
        os.makedirs("static/card")

    qr = qrcode.make(uid, border=1)
    qr.save(f"static/card/{uid}_qr.png")

    barcode = Code128(uid[1:].zfill(12), writer=ImageWriter())
    barcode.save(f"static/card/{uid}_barcode")

    avatar_path = f"static/avatar/{uid}.jpeg"
    if os.path.exists(avatar_path):
        avatar = Image.open(f"static/avatar/{uid}.jpeg")
        base_width = 800
        wpercent = (base_width / float(avatar.size[0]))
        hsize = int((float(avatar.size[1]) * float(wpercent)))
        avatar = avatar.resize((800, hsize))
        img.paste(avatar, (300, 600))

    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(img)
    # Add Text to an image
    I1.text((1800, 860), name, fill=(0, 0, 0), font=ImageFont.truetype('static/font.ttf', 64))
    I1.text((1800, 980), uid, fill=(0, 0, 0), font=ImageFont.truetype('static/font.ttf', 64))
    I1.text((1800, 1100), "綠星會員", fill=(0, 0, 0), font=ImageFont.truetype('static/font.ttf', 64))

    # Resize the QR code
    qr = qr.resize((400, 400))
    # Paste the QR code into the image
    img.paste(qr, (2400, 1300))

    barcode = Image.open(f"static/card/{uid}_barcode.png")
    img.paste(barcode, (1250, 1300))

    # Save the edited image
    img.save(f"static/card/{uid}.png")


@app.get('/api/admin/items')
def item_api_index():
    if not os.path.exists("static/item.json"):
        with open("static/item.json", "w") as f:
            f.write("[]")

    items = json.load(open("static/item.json"))
    return jsonify(items)


@app.post('/admin/items')
def item_create():
    if not os.path.exists("static/item.json"):
        with open("static/item.json", "w") as f:
            f.write("[]")

    items = json.load(open("static/item.json"))
    item_id = str(uuid4())

    request.files["image"].save(f"static/item/{item_id}.png")

    items.append({
        "id": item_id,
        "name": request.form["name"],
        "image": f"https://sloth-robust-remarkably.ngrok-free.app/static/item/{item_id}.png",
        "price": request.form["price"],
    })

    with open("static/item.json", "w") as f:
        json.dump(items, f)

    return redirect("https://sloth-robust-remarkably.ngrok-free.app/admin/items")


@app.post('/order')
def order_create():
    if not os.path.exists("static/order.json"):
        with open("static/order.json", "w") as f:
            f.write("[]")

    orders = json.load(open("static/order.json"))

    order_id = str(uuid4())
    orders.append({
        "id": order_id,
        "items": request.json["items"],
        "total": request.json["total"],
    })


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/admin')
def admin():
    return render_template('admin.html')


@app.get('/admin/items')
def item_index():
    return render_template('manage/items.html')


if __name__ == "__main__":
    app.run()

import datetime

from django.conf import settings

from linebot.models import FlexSendMessage
from linebot import LineBotApi

line_bot_api = LineBotApi(settings.CHANNEL_ACCESS_TOKEN)


# LINEメッセージ送信
def send_youtube_video_message(user_line_ids, video):
    dt_obj = datetime.datetime.fromisoformat(
        video["publish_time"].replace("Z", "+00:00")
    )
    content_json = {
        "type": "flex",
        "altText": video["title"],
        "contents": {
            "type": "bubble",
            "direction": "ltr",
            "hero": {
                "type": "image",
                "url": video["thumbnail"],
                "size": "full",
                "aspectRatio": "16:9",
                "aspectMode": "cover",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": video["title"],
                        "weight": "bold",
                        "align": "center",
                        "wrap": True,
                        "contents": [],
                    },
                    {
                        "type": "text",
                        "text": dt_obj.date().isoformat(),
                        "size": "sm",
                        "align": "center",
                        "margin": "sm",
                        "contents": [],
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "YouTube",
                            "uri": video["url"],
                        },
                        "style": "primary",
                    }
                ],
            },
        },
    }

    result = FlexSendMessage.new_from_json_dict(content_json)

    # 複数人同時
    # https://developers.line.biz/ja/reference/messaging-api/#send-multicast-message
    line_bot_api.multicast(user_line_ids, messages=result)

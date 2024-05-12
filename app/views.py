import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django.conf import settings
from apiclient.discovery import build

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    FollowEvent,
    MessageEvent,
    TextMessage,
    UnfollowEvent,
    PostbackEvent,
)
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseServerError,
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from app.line_message import send_youtube_video_message
from app.models import LineUser, Channel

line_bot_api = LineBotApi(settings.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.CHANNEL_SECRET)

YOUTUBE_API_KEY = settings.YOUTUBE_API_KEY


# LINEコールバック
class CallbackView(View):
    def get(self, request, *args, **kwargs):
        print("GET")
        return HttpResponse("OK")

    def post(self, request, *args, **kwargs):
        signature = request.META["HTTP_X_LINE_SIGNATURE"]
        body = request.body.decode("utf-8")

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseBadRequest()
        except LineBotApiError as e:
            print(e)
            return HttpResponseServerError()

        return HttpResponse("OK")

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CallbackView, self).dispatch(*args, **kwargs)

    # 友達追加
    @handler.add(FollowEvent)
    def handle_follow(event):
        line_id = event.source.user_id

        # 既存のユーザーをチェック
        if not LineUser.objects.filter(line_id=line_id).exists():
            try:
                profile = line_bot_api.get_profile(line_id)
                name = profile.display_name
                picture_url = profile.picture_url

                # LINEユーザー登録
                LineUser.objects.create(
                    name=name, picture_url=picture_url, line_id=line_id
                )
                print("新しい友達追加: ", name)
            except LineBotApiError as e:
                print("新しい友達追加エラー: ", e)
        else:
            print("ユーザーはすでに登録されています。")

    # 友達解除
    @handler.add(UnfollowEvent)
    def handle_unfollow(event):
        line_id = event.source.user_id
        # 対応するユーザーを見つけて削除
        try:
            user = LineUser.objects.get(line_id=line_id)
            user.delete()
            print("友達解除されたユーザーを削除しました: ", line_id)
        except LineUser.DoesNotExist:
            print("削除するユーザーが見つかりませんでした。", line_id)

    # テキストメッセージ
    @handler.add(MessageEvent, message=TextMessage)
    def text_message(event):
        line_id = event.source.user_id
        text = event.message.text
        print(line_id, text)

    # ポストバック
    @handler.add(PostbackEvent)
    def on_postback(event):
        print("ポストバック")


# 新しいYouTube動画を取得
def get_new_youtube_video_list(channel_ids, developerKey):
    # 1日前の日付を取得
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=1
    )
    # ISO形式に変換
    time_threshold = time_threshold.isoformat()

    video_list = []
    # YouTube APIを使用して登録されたチャンネルの新しい動画を取得
    youtube_api = build("youtube", "v3", developerKey=developerKey)

    for channel_id in channel_ids:
        response = (
            youtube_api.search()
            .list(
                part="snippet",
                channelId=channel_id,
                maxResults=2,
                order="date",
                publishedAfter=time_threshold,
                type="video",
            )
            .execute()
        )

        # レスポンスから必要な情報を取得
        for item in response["items"]:
            snippet_info = item["snippet"]
            channel_name = snippet_info["channelTitle"]
            publish_time = snippet_info["publishTime"]
            title = snippet_info["title"]
            thumbnail = snippet_info["thumbnails"]["high"]["url"]
            url = "https://www.youtube.com/watch?v=" + item["id"]["videoId"]

            video_list.append(
                {
                    "channel_name": channel_name,
                    "title": title,
                    "thumbnail": thumbnail,
                    "url": url,
                    "publish_time": publish_time,
                }
            )
    return video_list


# CSRF保護を無効化
@method_decorator(csrf_exempt, name="dispatch")
class YouTubeView(View):
    def post(self, request, *args, **kwargs):
        try:
            # トークン取得
            auth_header = request.headers.get("Authorization")

            # トークンがない場合
            if not auth_header:
                return JsonResponse({"error": "Token is missing"}, status=401)

            token_type, _, token = auth_header.partition(" ")

            # トークンチェック
            if token_type != "Bearer" or token != settings.ACCESS_TOKEN:
                return JsonResponse({"error": "Invalid token"}, status=401)

            user_line_ids = []
            # LINEユーザー取得
            user_data = LineUser.objects.all()

            # LINEIDをリストに追加
            for user in user_data:
                user_line_ids.append(user.line_id)

            # LINEユーザーがいない場合
            if len(user_line_ids) == 0:
                return JsonResponse({"error": "No user found"}, status=401)

            # チャンネルID取得
            channel_ids = Channel.objects.values_list("channel_id", flat=True)

            # チャンネルIDで新しいYouTube動画を取得
            video_list = get_new_youtube_video_list(channel_ids, YOUTUBE_API_KEY)

            # 新しい動画がない場合
            if len(video_list) == 0:
                return JsonResponse({"success": "No new video found"})

            # LINEユーザーに新しいYouTube動画を送信
            for video in video_list:
                send_youtube_video_message(user_line_ids, video)

            return JsonResponse({"success": "Data processed successfully"})
        except Exception as e:
            print(e)
            return JsonResponse({"error": e}, status=401)

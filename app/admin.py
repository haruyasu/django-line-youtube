from django.contrib import admin
from .models import LineUser, Channel


class LineUserCustom(admin.ModelAdmin):
    # 一覧
    list_display = ("id", "name", "line_id", "created_at")
    # 順番
    ordering = ("created_at",)
    list_display_links = ("id", "name", "line_id")


class ChannelCustom(admin.ModelAdmin):
    # 一覧
    list_display = ("id", "name", "channel_id", "created_at")
    # 順番
    ordering = ("created_at",)
    list_display_links = ("id", "name", "channel_id")


admin.site.register(LineUser, LineUserCustom)
admin.site.register(Channel, ChannelCustom)

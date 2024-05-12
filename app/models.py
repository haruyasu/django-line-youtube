from django.db import models


class LineUser(models.Model):
    name = models.CharField(max_length=255, verbose_name="名前")
    picture_url = models.URLField(
        max_length=1024, verbose_name="プロフィール画像URL", blank=True
    )
    line_id = models.CharField(max_length=255, unique=True, verbose_name="LINE ID")

    updated_at = models.DateTimeField("更新日", auto_now=True)
    created_at = models.DateTimeField("作成日", auto_now_add=True)

    class Meta:
        verbose_name = "LINEユーザー"
        verbose_name_plural = "LINEユーザー"

    def __str__(self):
        return self.name


class Channel(models.Model):
    name = models.CharField(max_length=255, verbose_name="名前")
    channel_id = models.CharField(
        max_length=255, unique=True, verbose_name="チャンネルID"
    )

    updated_at = models.DateTimeField("更新日", auto_now=True)
    created_at = models.DateTimeField("作成日", auto_now_add=True)

    class Meta:
        verbose_name = "登録チャンネル"
        verbose_name_plural = "登録チャンネル"

    def __str__(self):
        return self.name

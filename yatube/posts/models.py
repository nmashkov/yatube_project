from django.db import models
from django.contrib.auth import get_user_model

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='group_posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        help_text='Загрузите картинку',
        upload_to='posts/',
        blank=True,
        null=True,
        error_messages={'invalid_image': 'Не картинка'},
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-created']

    def short_text(self):
        characters = 100
        text_len = len(self.text)
        if text_len <= characters:
            text = self.text
        else:
            text = self.text[:characters] + '...'
        return text

    def short_title(self):
        characters = 30
        text_len = len(self.text)
        if text_len <= characters:
            title = 'Пост: ' + self.text
        else:
            title = 'Пост: ' + self.text[:characters] + '...'
        return title


class Comment(CreatedModel):
    text = models.TextField(
        'Комментарий',
        help_text='Комментарий'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Запись',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментатор'
    )

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписка на'
    )

    class Meta:
        unique_together = [['user', 'author']]

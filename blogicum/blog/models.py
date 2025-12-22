from django.contrib.auth import get_user_model
from django.db import models

from .constants import CHAR_MAX_LENGTH, MAX_DISPLAY_LENGTH


User = get_user_model()


class CreatedAtAbstract(models.Model):
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('created_at',)


class IsPublishedCreatedAtAbstract(CreatedAtAbstract):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        abstract = True


class Category(IsPublishedCreatedAtAbstract):
    title = models.CharField('Заголовок', max_length=CHAR_MAX_LENGTH)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; '
        'разрешены символы латиницы, цифры, дефис и подчёркивание.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:MAX_DISPLAY_LENGTH]


class Location(IsPublishedCreatedAtAbstract):
    name = models.CharField('Название места', max_length=CHAR_MAX_LENGTH)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:MAX_DISPLAY_LENGTH]


class Post(IsPublishedCreatedAtAbstract):
    title = models.CharField('Заголовок', max_length=CHAR_MAX_LENGTH)
    text = models.TextField('Текст')
    image = models.ImageField(
        'Картинка',
        upload_to='posts_images/',
        blank=True,
        null=True
    )
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text='Если установить дату и время в будущем — можно делать '
        'отложенные публикации.'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)
        default_related_name = 'posts'

    def __str__(self):
        return self.title[:MAX_DISPLAY_LENGTH]


class Comment(CreatedAtAbstract):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)
        default_related_name = 'comments'

    def __str__(self):
        return self.text[:MAX_DISPLAY_LENGTH]

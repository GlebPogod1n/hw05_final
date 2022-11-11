from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    slug = models.SlugField('Краткое название', max_length=200, unique=True)
    title = models.CharField('Название группы', max_length=200)
    description = models.TextField('Описание группы', max_length=200)

    class Meta:
        verbose_name = 'group'
        verbose_name_plural = 'groups'

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа сообщений',
        help_text='Группа, к которой будет относиться пост'
    )
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'post'
        verbose_name_plural = 'posts'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commentator',
        verbose_name='Автор комментария'
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комметария'
    )
    created = models.DateTimeField(
        'Комметарий добавлен',
        auto_now_add=True)

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'],
            name='unique_follow'
        )]

    def __str__(self):
        return (f'Пользователь {self.user} '
                f'подписан на пользователя {self.author}'
                )

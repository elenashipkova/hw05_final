from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Идентификатор')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации', db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts', verbose_name='Автор')
    group = models.ForeignKey(Group, related_name='posts',
                              on_delete=models.SET_NULL, blank=True, null=True,
                              verbose_name='Группа')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments', verbose_name='Комментарий')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments', verbose_name='Автор')
    text = models.CharField(max_length=500, verbose_name='Текст комментария')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата комментария')

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower",
                             verbose_name='Подписчик')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following",
                               verbose_name='Автор')

    def __str__(self):
        return f'user: {self.user.username} author: {self.author.username}'
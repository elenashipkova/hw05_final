from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'group': 'Выберите группу',
            'text': 'Введите текст',
            'image': 'Загрузите картинку',
        }
        help_texts = {
            'group': 'Можете выбрать группу для публикации',
            'text': 'Делитесь эмоциями с другими подписчиками!',
            'image': 'Можете загрузить одно фото с вашего компьютера',
        }


class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        label = {'text': 'Комментарий'}
        help_text = {'text': 'Оставьте комментарий'}

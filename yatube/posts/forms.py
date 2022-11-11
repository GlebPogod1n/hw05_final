from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'group': _('Group name'),
            'text': _('Post text')
        }
        help_texts = {
            'text': _('Enter your post here'),
            'group': _('The group can be omitted')
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Тект комментария',
        }
        help_texts = {
            'text': 'Введите текст вашего комментария',
        }

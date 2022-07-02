from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой принадлежит пост',
        }
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Текст комментария',
        }
        labels = {
            'text': 'Текст комментария',
        }

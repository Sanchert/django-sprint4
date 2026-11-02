from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Post, Comment

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации нового пользователя.

    Расширяет стандартную UserCreationForm, добавляя поля
    email, first_name и last_name.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class PostForm(forms.ModelForm):
    """
    Форма для создания и редактирования публикации.

    Включает поля: заголовок, текст, дату публикации, категорию,
    местоположение и изображение. Виджет pub_date настроен на HTML5
    datetime-local для удобного выбора даты в браузере.
    """

    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'category', 'location',
                  'image')
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CommentForm(forms.ModelForm):
    """
    Форма для добавления и редактирования комментария.

    Содержит единственное поле — текст комментария.
    """

    class Meta:
        model = Comment
        fields = ('text',)

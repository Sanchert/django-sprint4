from django.contrib import admin
from .models import Category, Comment, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Настройка отображения модели Category в админ-панели.

    Позволяет редактировать is_published прямо из списка,
    автоматически генерирует slug из заголовка.
    """

    list_display = ('title', 'is_published', 'slug')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Настройка отображения модели Location в админ-панели."""

    list_display = ('name', 'is_published')
    list_editable = ('is_published',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Настройка отображения модели Post в админ-панели.

    Добавляет фильтры по публикации, категории и автору,
    а также поиск по заголовку и тексту.
    """

    list_display = ('title', 'author', 'category', 'pub_date', 'is_published')
    list_filter = ('is_published', 'category', 'author')
    search_fields = ('title', 'text')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Настройка отображения модели Comment в админ-панели."""

    list_display = ('post', 'author', 'created_at')

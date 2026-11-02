from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import login, get_user_model
from django.core.paginator import Paginator
from .models import Post, Category
from .forms import CustomUserCreationForm


User = get_user_model()

def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    post_list = profile_user.posts.all().select_related('category', 'location')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile_user': profile_user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)

def get_published_posts():
    """
    Вспомогательная функция для фильтрации опубликованных постов.

    Учитывает дату публикации, флаг публикации поста и категории.
    select_related нужен для оптимизации запросов к БД (избегаем N+1).
    """
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).select_related('category', 'location', 'author')


def index(request):
    """Главная страница: 5 последних публикаций."""
    post_list = get_published_posts()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    """Страница отдельной публикации."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        if (not post.is_published or 
            post.pub_date > timezone.now() or 
            not post.category.is_published):
            raise Http404("Публикация не найдена")

    context = {'post': post}
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """Страница категории."""
    category = get_object_or_404(Category, slug=category_slug, is_published=True)
    post_list = category.posts.filter(
        is_published=True,
        pub_date__lte=timezone.now()
    ).select_related('location', 'author')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)

def registration(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически логиним пользователя после регистрации
            return redirect('blog:index')  # Или на страницу профиля
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/registration_form.html', {'form': form})

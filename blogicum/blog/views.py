from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import login, get_user_model
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse
from .models import Post, Category, Comment
from .forms import CustomUserCreationForm, PostForm, CommentForm

User = get_user_model()


def get_published_posts():
    """
    Возвращает QuerySet опубликованных постов, доступных всем посетителям.

    Фильтрует по трём условиям (is_published, pub_date, category),
    добавляет счётчик комментариев и сортирует «от новых к старым».
    Использует select_related для оптимизации запросов (избегаем N+1).
    """
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).annotate(comment_count=Count('comments')).select_related(
        'category', 'location', 'author'
    ).order_by('-pub_date')


def index(request):
    """
    Главная страница блога.

    Выводит по 10 опубликованных постов на страницу (пагинация).
    """
    post_list = get_published_posts()
    paginator = Paginator(post_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    """
    Страница отдельной публикации.

    Доступна всем для опубликованных постов. Автор может видеть
    свои посты, даже если они отложены или скрыты администратором.
    Выводит комментарии и форму для добавления нового.
    """
    post = get_object_or_404(
        Post.objects.annotate(comment_count=Count('comments')),
        pk=post_id
    )

    if post.author != request.user:
        if (
            not post.is_published
            or post.pub_date > timezone.now()
            or not post.category.is_published
        ):
            raise Http404("Публикация не найдена")

    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """
    Страница публикаций выбранной категории.

    Возвращает 404, если категория снята с публикации.
    Выводит по 10 постов с пагинацией.
    """
    category = get_object_or_404(Category,
                                 slug=category_slug,
                                 is_published=True)
    post_list = category.posts.filter(
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comments')).select_related(
        'location', 'author'
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {'category': category, 'page_obj': page_obj}
    return render(request, 'blog/category.html', context)


def profile(request, username):
    """
    Страница пользователя (профиль).

    Всем посетителям видны информация о пользователе и его опубликованные
    посты. Хозяину профиля — все посты (включая черновики и отложенные),
    а также ссылки на редактирование профиля и смену пароля.
    """
    profile_user = get_object_or_404(User, username=username)

    if request.user == profile_user:
        post_list = (
            profile_user.posts
            .annotate(comment_count=Count('comments'))
            .select_related('category', 'location')
            .order_by('-pub_date')
        )
    else:
        post_list = (
            profile_user.posts
            .filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True
            )
            .annotate(comment_count=Count('comments'))
            .select_related('category', 'location')
            .order_by('-pub_date')
        )

    paginator = Paginator(post_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'profile': profile_user,
        'page_obj': page_obj
    }
    return render(request, 'blog/profile.html', context)


def registration(request):
    """
    Страница регистрации нового пользователя.

    После успешной валидации формы автоматически логинит пользователя
    и перенаправляет на главную страницу.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/registration_form.html', {'form':
                                                                   form})


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Создание новой публикации.

    Доступно только авторизованным пользователям. Автор подставляется
    автоматически из request.user. После создания редирект в профиль.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username':
                                               self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Редактирование существующей публикации.

    Доступно только автору. При попытке редактирования чужого поста
    пользователь перенаправляется на страницу просмотра поста.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        return self.request.user == self.get_object().author

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().handle_no_permission()

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id':
                                                   self.kwargs['post_id']})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Удаление публикации с подтверждающей страницей.

    Переиспользует шаблон blog/create.html. Доступно только автору.
    После удаления редирект в профиль пользователя.
    """

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        return self.request.user == self.get_object().author

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username':
                                               self.request.user.username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    """
    Добавление комментария к публикации.

    Автор и пост подставляются автоматически. Доступно только
    авторизованным пользователям.
    """

    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id':
                                                   self.kwargs['post_id']})


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Редактирование собственного комментария.

    Доступно только автору комментария.
    Переиспользует шаблон blog/comment.html.
    """

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def test_func(self):
        return self.request.user == self.get_object().author

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().handle_no_permission()

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id':
                                                   self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Удаление собственного комментария с подтверждающей страницей.

    Доступно только автору комментария.
    Переиспользует шаблон blog/comment.html.
    """

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def test_func(self):
        return self.request.user == self.get_object().author

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().handle_no_permission()

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id':
                                                   self.kwargs['post_id']})


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование профиля текущего пользователя.

    Позволяет изменить имя, фамилию, логин и email. Пароль меняется
    через отдельную страницу django.contrib.auth.urls.
    """

    model = User
    template_name = 'blog/user.html'
    fields = ('first_name', 'last_name', 'username', 'email')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username':
                                               self.request.user.username})

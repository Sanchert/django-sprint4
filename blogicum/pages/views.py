from django.shortcuts import render
from django.views.generic import TemplateView


class AboutView(TemplateView):
    """
    Статическая страница «О проекте».

    Реализована через CBV (TemplateView) в соответствии с требованием ТЗ.
    """

    template_name = 'pages/about.html'


class RulesView(TemplateView):
    """
    Статическая страница «Правила».

    Реализована через CBV (TemplateView) в соответствии с требованием ТЗ.
    """

    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    """Кастомный обработчик ошибки 404 (страница не найдена)."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Кастомный обработчик ошибки 500 (внутренняя ошибка сервера)."""
    return render(request, 'pages/500.html', status=500)


def csrf_failure(request, reason=''):
    """
    Кастомный обработчик ошибки 403 (неверный CSRF-токен).

    Подключается через настройку CSRF_FAILURE_VIEW в settings.py.
    """
    return render(request, 'pages/403csrf.html', status=403)

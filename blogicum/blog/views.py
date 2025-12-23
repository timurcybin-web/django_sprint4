# Настраиваем пагинатор на 10 позиций
# Пагинатор на главную, страницу пользователя и страницу категории
# Для реализации функций используем FBV, CBV, миксины

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    DeleteView, DetailView, ListView, CreateView, UpdateView
)

from .models import Category, Comment, Post, User
from .forms import CommentForm, PostForm, UserForm

PAGINATOR_POST = 10
PAGINATOR_CATEGORY = 10
PAGINATOR_PROFILE = 10


def get_page_obj(request, queryset, per_page):
    """Возвращает страницу пагинатора для заданного queryset."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def get_posts_with_comments(
    queryset=None, *, filter_published=True, annotate_comments=True
):
    """
    Дополняет посты количеством комментариев и при необходимости
    фильтрует по опубликованности.
    """
    if queryset is None:
        queryset = Post.objects.all()

    queryset = queryset.select_related('author', 'location', 'category')

    if annotate_comments:
        queryset = queryset.annotate(comment_count=Count('comments'))

    if filter_published:
        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    return queryset.order_by(*Post._meta.ordering)


class PostListView(ListView):
    """Представление для отображения списка публикаций на главной странице"""

    paginate_by = PAGINATOR_POST
    template_name = 'blog/index.html'

    def get_queryset(self):
        """Получение списка публикаций с использованием фильтрации"""
        return get_posts_with_comments()


class PostDetailView(DetailView):
    """Представление для отображения деталей конкретной публикации"""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        """
        Дополнение контекста данными о комментариях и формой для добавления
                                                                    комментариев
        """
        return dict(
            **super().get_context_data(**kwargs),
            form=CommentForm(),
            comments=self.object.comments.select_related('author')
        )

    def get_object(self):
        """
        Получение объекта публикации с учётом её статуса публикации.
        Автор видит даже неопубликованные публикации
        """
        post = get_object_or_404(
            Post.objects.select_related('category', 'location', 'author'),
            pk=self.kwargs["post_id"],
        )
        if (not self.request.user.is_authenticated
                or self.request.user != post.author):
            post = get_object_or_404(
                Post.objects.select_related('category', 'location', 'author'),
                pk=self.kwargs["post_id"],
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now(),
            )
        return post


class PostCategoryView(ListView):
    """Представление для отображения списка публикаций в категории"""

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = PAGINATOR_CATEGORY

    def get_queryset(self):
        """Получение публикаций, отфильтрованных по категории"""
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return get_posts_with_comments(self.category.posts.all())

    def get_context_data(self, **kwargs):
        """Добавление информации о категории в контекст"""
        return dict(
            **super().get_context_data(**kwargs),
            category=self.category
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания публикации"""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Автоматическое назначение автором текущего пользователя"""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """
        Перенаправление на профиль автора после успешного создания
                                                                публикации
        """
        return reverse(
            'blog:profile', args=[self.request.user.username]
        )


class PostMixin(LoginRequiredMixin):
    """
    Миксин для проверки, что публикация принадлежит текущему пользователю
    Используется для обновления и удаления публикаций
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        """Проверка авторства публикации"""
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post.author != self.request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(PostMixin, UpdateView):
    """Представление для редактирования публикации"""

    def get_success_url(self):
        """Перенаправление на страницу деталей публикации после обновления"""
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])


class PostDeleteView(PostMixin, DeleteView):
    """Представление для удаления публикации"""

    def get_success_url(self):
        """Перенаправление на профиль пользователя после удаления публикации"""
        return reverse('blog:profile', args=[self.request.user.username])


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования данных профиля пользователя"""

    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self):
        """Получение текущего пользователя"""
        return self.request.user

    def get_success_url(self):
        """Перенаправление на профиль пользователя после обновления"""
        return reverse('blog:profile', args=[self.request.user.username])


class ProfileListView(ListView):
    """Представление для отображения профиля пользователя и его публикаций"""

    template_name = 'blog/profile.html'
    model = Post

    def get_object(self):
        """Получение объекта пользователя по имени пользователя"""
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        """Получение публикаций пользователя"""
        profile = self.get_object()
        filter_published = self.request.user != profile
        return get_posts_with_comments(
            profile.posts.all(),
            filter_published=filter_published
        )

    def get_context_data(self, **kwargs):
        """Добавление данных профиля в контекст"""
        profile = self.get_object()
        context = super().get_context_data(**kwargs)
        page_obj = get_page_obj(
            self.request,
            self.get_queryset(),
            PAGINATOR_PROFILE
        )
        context.update(
            profile=profile,
            page_obj=page_obj,
            object_list=page_obj
        )
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания комментария к публикации"""

    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def get_context_data(self, **kwargs):
        """Добавление формы в контекст"""
        return dict(**super().get_context_data(**kwargs), form=CommentForm())

    def form_valid(self, form):
        """Назначение автором текущего пользователя и привязка к публикации"""
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        """
        Перенаправление на страницу деталей публикации после добавления
                                                                    комментария
        """
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])


class CommentMixin(LoginRequiredMixin):
    """Миксин для проверки принадлежности комментария текущему пользователю"""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        """Перенаправление на детали публикации после выполнения действия"""
        return reverse('blog:post_detail', args=[self.kwargs['comment_id']])

    def dispatch(self, request, *args, **kwargs):
        """Проверка авторства комментария"""
        coment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        if coment.author != self.request.user:
            return redirect('blog:post_detail',
                            post_id=self.kwargs['comment_id']
                            )
        return super().dispatch(request, *args, **kwargs)


class CommentUpdateView(CommentMixin, UpdateView):
    """Представление для редактирования комментария"""

    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    """Представление для удаления комментария"""

    ...

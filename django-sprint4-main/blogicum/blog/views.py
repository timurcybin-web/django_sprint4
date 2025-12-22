from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .constants import COMMENTS_PER_PAGE, POSTS_PER_PAGE
from .forms import CreateCommentForm, CreatePostForm, UserEditForm
from .mixins import AuthorRequiredMixin, PostMixin, CommentMixin
from .models import Category, Post
from .services import annotate_posts, filter_published, paginate


def index(request):
    post_list = annotate_posts(
        filter_published(Post.objects.all())
    )
    page_obj = paginate(request, post_list, POSTS_PER_PAGE)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    queryset = Post.objects.select_related('category', 'location', 'author')
    post = get_object_or_404(queryset, id=post_id)
    if request.user != post.author:
        post = get_object_or_404(
            filter_published(queryset),
            id=post_id
        )
    comments = (
        post.comments
        .select_related('author')
        .all()
    )
    page_obj = paginate(request, comments, COMMENTS_PER_PAGE)
    form = CreateCommentForm() if request.user.is_authenticated else None
    return render(
        request,
        'blog/detail.html',
        {'post': post, 'page_obj': page_obj, 'form': form}
    )


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = annotate_posts(
        filter_published(category.posts.all())
    )
    page_obj = paginate(request, post_list, POSTS_PER_PAGE)
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj
    })


"""Классы работы с постами."""


class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = CreatePostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class EditPostView(PostMixin, UpdateView):
    form_class = CreatePostForm
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.id}
        )


class DeletePostView(PostMixin, DeleteView):
    pk_url_kwarg = 'post_id'


"""Классы работы с профилем."""


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_PER_PAGE

    def get_profile_user(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        profile_user = self.get_profile_user()
        post_list = profile_user.posts.all()
        post_list = annotate_posts(post_list)
        if self.request.user != profile_user:
            post_list = filter_published(post_list)
        return post_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_profile_user()
        return context


"""Сменид на FBV, тесты не проходили."""


@login_required
def edit_profile(request):
    form = UserEditForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/user.html', {'form': form})


"""Классы работы с комментариями."""


class AddCommentView(CommentMixin, CreateView):
    form_class = CreateCommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditCommentView(CommentMixin, AuthorRequiredMixin, UpdateView):
    form_class = CreateCommentForm


"""Без post не проходят тесты в DeleteCommentView."""


class DeleteCommentView(CommentMixin, AuthorRequiredMixin, DeleteView):
    pass


"""Регистрация."""


class RegistrationView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')

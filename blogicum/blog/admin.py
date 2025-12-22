from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import Category, Comment, Location, Post, User


"""Удаляем стандартную регистрацию пользователей и групп"""

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ('posts_count',)

    @admin.display(description='Кол-во постов у пользователя')
    def posts_count(self, obj):
        return obj.posts.count()


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'pub_date',
        'is_published',
        'image_post'
    )
    search_fields = ('title', 'text')
    list_filter = ('is_published', 'category', 'location')

    @admin.display(description='Картинка')
    def image_post(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="80" height="60">'
            )
        return 'нет картинки'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published')
    search_fields = ('title',)
    list_filter = ('is_published',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    search_fields = ('text',)
    list_filter = ('created_at',)

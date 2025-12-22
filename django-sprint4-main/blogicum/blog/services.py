from django.core.paginator import Paginator
from django.db.models import Count
from django.utils.timezone import now


def filter_published(queryset):
    return queryset.filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True
    )


def annotate_posts(queryset):
    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date').select_related('category', 'location', 'author')


def paginate(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get('page'))

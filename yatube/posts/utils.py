from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import QuerySet

from .models import Like


def pagination(request: str, post: QuerySet) -> dict:
    """return 'context' dictionary with Paginator 'page_obj' """
    paginator = Paginator(post, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def user_liked_posts(user) -> list:
    if user.is_authenticated:
        return [like.post.pk for like in Like.objects.filter(user=user)]
    else:
        return []

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import QuerySet


def pagination(request: str, post: QuerySet) -> dict:
    """return 'context' dictionary with Paginator 'page_obj' """
    paginator = Paginator(post, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)

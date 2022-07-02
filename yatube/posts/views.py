from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from posts.models import Follow, Group, Post, User

from .forms import CommentForm, PostForm
from .utils import pagination


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author')
    page_obj = pagination(request, posts)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    page_obj = pagination(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj, }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.select_related('group', 'author')
    number_of_posts = posts.count()
    page_obj = pagination(request, posts)
    if (request.user.is_authenticated
       and len(request.user.follower.filter(author=user)) == 0):
        following = False
    else:
        following = True
    context = {
        'page_obj': page_obj,
        'username': user,
        'number_of_posts': number_of_posts,
        'following': following, }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    number_of_posts = post.author.posts.count()
    comments = post.comments.select_related('post')
    form = CommentForm(request.POST)
    context = {
        'post': post,
        'number_of_posts': number_of_posts,
        'form': form,
        'comments': comments, }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:profile', username=request.user.username)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    current_user = request.user
    if post.author != current_user:
        return redirect('posts:post_detail', post_id)
    if request.method == 'GET':
        form = PostForm(instance=post)
        context = {'is_edit': True, 'form': form}
        return render(request, 'posts/create_post.html', context)
    if request.method == 'POST':
        form = PostForm(request.POST,
                        files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    following_authors = user.follower.values_list('author_id', flat=True)
    posts = Post.objects.filter(author_id__in=following_authors)
    page_obj = pagination(request, posts)
    context = {'page_obj': page_obj,
               'following_authors': following_authors, }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')

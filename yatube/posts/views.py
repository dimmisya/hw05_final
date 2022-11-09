from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from posts.models import Follow, Group, Post, User, Like

from .forms import CommentForm, PostForm
from .utils import pagination, user_liked_posts


@cache_page(20, key_prefix='index_page')
def index(request):
    order = request.GET.get('orderby', '-pub_date')
    posts = Post.objects.select_related('group', 'author').order_by(order)
    page_obj = pagination(request, posts)
    liked_posts = user_liked_posts(request.user)
    order_value = {
        '-pub_date': 'Дата',
        '-likes_count': 'Лайки',
        '-comments_count': 'Комментарии',
    }
    context = {
        'page_obj': page_obj,
        'liked_posts': liked_posts,
        'order_value': order_value[order],
    }
    return render(request, 'posts/index.html', context)


def search_result(request):
    text_search = request.GET.get('q', '/')
    posts = Post.objects.filter(text__icontains=text_search)
    page_obj = pagination(request, posts)
    liked_posts = user_liked_posts(request.user)
    context = {
        'page_obj': page_obj,
        'liked_posts': liked_posts,
    }
    return render(request, 'posts/search_result.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    page_obj = pagination(request, posts)
    liked_posts = user_liked_posts(request.user)
    context = {
        'group': group,
        'page_obj': page_obj,
        'liked_posts': liked_posts, }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.select_related('group', 'author')
    number_of_posts = posts.count()
    page_obj = pagination(request, posts)
    liked_posts = user_liked_posts(request.user)
    if (request.user.is_authenticated
       and request.user.follower.filter(author=user).exists()):
        following = True
    else:
        following = False
    context = {
        'page_obj': page_obj,
        'username': user,
        'number_of_posts': number_of_posts,
        'following': following,
        'liked_posts': liked_posts, }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    number_of_posts = post.author.posts.count()
    number_of_likes = post.likes.count()
    comments = post.comments.select_related('post')
    form = CommentForm(request.POST)
    if (request.user.is_authenticated
       and post.likes.filter(user=request.user).exists()):
        like = True
    else:
        like = False
    context = {
        'post': post,
        'number_of_posts': number_of_posts,
        'form': form,
        'comments': comments,
        'number_of_likes': number_of_likes,
        'like': like, }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
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
    elif request.method == 'POST':
        form = PostForm(request.POST,
                        files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
        else:
            return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        post.comments_count = post.comments.count()
        post.save()
        print(post.comments_count)
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = pagination(request, posts)
    context = {'page_obj': page_obj, }
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
    follow = Follow.objects.filter(user=request.user, author=author)
    if follow.exists():
        follow.delete()
    return redirect('posts:follow_index')


@login_required
def post_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        Like.objects.get_or_create(user=request.user, post=post)
        post.likes_count = post.likes.count()
        post.save()
    next = request.GET.get('next', '/')
    return HttpResponseRedirect(next)

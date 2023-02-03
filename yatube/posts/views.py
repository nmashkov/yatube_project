from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_page

from posts.models import Post, Group, Follow
from posts.forms import PostForm, CommentForm

POSTS_AMOUNT = 10


@cache_page(timeout=20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.group_posts.all()
    paginator = Paginator(group_posts, POSTS_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = f'Записи сообщества {str(group)}'
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if User.objects.filter(username=request.user).exists():
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    else:
        following = False
    post_list = author.posts.all()
    paginator = Paginator(post_list, POSTS_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    followers = author.following.count()
    title = f'Профайл пользователя {username}'
    context = {
        'author': author,
        'count': post_list.count(),
        'page_obj': page_obj,
        'title': title,
        'followers': followers,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user)
    followings = user.follower.all()
    if followings.count() == 0:
        title = 'У вас ещё нет подписок'
        page_obj = []
        context = {
            'title': title,
            'page_obj': page_obj,
        }
        return render(request, 'posts/follow.html', context)
    post_list = Post.objects.filter(author__following__user=user)
    if len(post_list) == 0:
        title = 'У ваших авторов ещё нет публикаций'
        page_obj = []
        context = {
            'title': title,
            'page_obj': page_obj,
        }
        return render(request, 'posts/follow.html', context)
    else:
        paginator = Paginator(post_list, POSTS_AMOUNT)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        title = 'Ваши подписки'
        context = {
            'title': title,
            'page_obj': page_obj,
        }
        return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follower = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    redirect_params = ['posts:profile', author.username]
    if author.username == follower.username:
        return redirect(*redirect_params)
    Follow.objects.get_or_create(user=follower, author=author)
    return redirect(*redirect_params)


@login_required
def profile_unfollow(request, username):
    unfollower = get_object_or_404(User, username=request.user)
    unfollower.follower.filter(author__username=username).delete()
    return redirect('posts:profile', username=username)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_list = post.author.posts.all()
    comments = post.comments.all()
    followers = post.author.following.count()
    if User.objects.filter(username=request.user).exists():
        following = Follow.objects.filter(user=request.user,
                                          author=post.author).exists()
    else:
        following = False
    form = CommentForm()
    title = post.short_title()
    context = {
        'title': title,
        'count': post_list.count(),
        'post': post,
        'comments': comments,
        'form': form,
        'followers': followers,
        'following': following,
    }
    return render(request, 'posts/post_detail.html', context)


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
def post_create(request):
    new_post = Post
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', username=request.user)
    form = PostForm()
    title = 'Новая запись'
    context = {
        'form': form,
        'title': title,
    }
    return render(request, 'posts/post_create.html', context)


def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, pk=post_id)
    if edit_post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=edit_post,
    )
    if form.is_valid():
        edit_post = form.save()
        return redirect('posts:post_detail', post_id=post_id)
    title = 'Редактировать запись'
    is_edit = True
    context = {
        'post_id': post_id,
        'form': form,
        'title': title,
        'is_edit': is_edit,
    }
    return render(request, 'posts/post_create.html', context)

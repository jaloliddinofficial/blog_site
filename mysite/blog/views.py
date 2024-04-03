from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity

def post_share(request, post_pk):
    post = get_object_or_404(Post,
                             pk=post_pk,
                             status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n{cd['name']}\' comments: {cd['comments']}"
            send_mail(
                subject=subject,
                message=message,
                from_email='btimur.mail@gmail.com',
                recipient_list=[cd['to']]
            )
            sent = True
    else:
        form = EmailPostForm()
    context = {
        "post": post,
        "form": form,
        'sent': sent
    }
    return render(request=request,
                  template_name="blog/post/share.html",
                  context=context)

# class PostListView(ListView):
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    paginator = Paginator(post_list, per_page=3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    context = {
        'posts': posts,
        'tag': tag
    }
    return render(
        request=request,
        template_name='blog/post/list.html',
        context=context
    )

def post_detail(request, year, month, day, post):
    # try:
    #     post = Post.objects.get(pk=id)
    # except Post.DoesNotExist:
    #     raise Http404("No found.")
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'similar_posts': similar_posts,
    }
    return render(
        request=request,
        template_name='blog/post/detail.html',
        context=context
    )

@require_POST
def post_comment(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk,
                             status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    context = {
        'post': post,
        'form': form,
        'comment': comment
    }
    return render(
        request=request,
        template_name='blog/post/comment.html',
        context=context
    )

def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight="A")+SearchVector('body', weight="B")
            search_query = SearchQuery(query)
            results = Post.published.annotate(similarity=TrigramSimilarity('title', query),
                                              ).filter(similarity__gt=0.1).order_by('-similarity')
    context = {
        'form': form,
        'query': query,
        'results': results,
    }
    return render(
        request=request,
        template_name='blog/post/search.html',
        context=context
    )
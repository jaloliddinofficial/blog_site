from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST

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

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


# def post_list(request):
#     post_list = Post.published.all()
#     paginator = Paginator(post_list, per_page=3)
#     page_number = request.GET.get('page', 1)
#     try:
#         posts = paginator.page(page_number)
#     except PageNotAnInteger:
#         posts = paginator.page(1)
#     except EmptyPage:
#         posts = paginator.page(paginator.num_pages)
#     context = {
#         'posts': posts,
#     }
#     return render(
#         request=request,
#         template_name='blog/post/list.html',
#         context=context
#     )

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
    context = {
        'post': post,
        'comments': comments,
        'form': form,
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
from django.shortcuts import render, get_object_or_404
from .models import Post
from django.http import Http404

def post_list(request):
    posts = Post.objects.all()
    context = {
        'posts': posts,
    }
    return render(
        request=request,
        template_name='blog/post/list.html',
        context=context
    )

def post_detail(request, id):
    # try:
    #     post = Post.objects.get(pk=id)
    # except Post.DoesNotExist:
    #     raise Http404("No found.")
    post = get_object_or_404(Post, pk=id,
                             status=Post.Status.PUBLISHED)
    context = {
        'post': post
    }
    return render(
        request=request,
        template_name='blog/post/detail.html',
        context=context
    )
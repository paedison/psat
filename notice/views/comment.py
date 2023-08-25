# Django Core Import
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from vanilla import DetailView, CreateView, UpdateView, ListView, TemplateView, DeleteView

# Custom App Import
from common.constants import icon, color
from ..forms import CommentForm, PostForm  # Should Change App Name
from ..models import Comment, Post  # Should Change App Name


class CommentViewMixIn:
    """
    Represent comment view mixin.
    view_type: one of [ postList, postListMain, postDetail,
         postCreate, postUpdate, postDelete, commentDetail,
         commentCreate, commentUpdate, commentDelete ]
    category(int): Category of Post model
    """
    kwargs: dict
    view_type: str
    category = 0
    object: any
    object_list: any

    # Default Settings
    app_name = 'notice'
    menu = app_name.capitalize()
    staff_menu = True  # Whether only admin or staff can create posts or not.
    model = Comment
    form_class = CommentForm
    paginate_by = 10
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'

    post_model = Post
    post_form = PostForm

    # Templates
    folder = 'board'
    list_template = f'{folder}/comment_list.html'  # CommentListView
    list_content_template = f'{list_template}#container'  # CommentListContentView
    detail_template = f'{folder}/comment_detail.html'  # CommentDetailView
    detail_content_template = f'{detail_template}#container'  # CommentDetailContentView
    create_template = f'{folder}/comment_create.html'  # CommentCreateView
    create_content_template = f'{create_template}#container'  # CommentCreateContentView
    template_dict = {
        'commentList': list_template,
        'commentListContent': list_content_template,
        'commentDetail': detail_template,
        'commentDetailContent': detail_content_template,
        'commentCreate': create_template,
        'commentCreateContent': create_content_template,
        'commentUpdate': create_template,
        'commentUpdateContent': create_content_template,
    }

    @property
    def template_name(self) -> str: return self.template_dict[self.view_type]

    @property
    def post_id(self) -> int:
        if self.comment_id:
            comment = self.model.objects.get(id=self.comment_id)
            return comment.post.id
        return self.kwargs.get('post_id')

    @property
    def comment_id(self) -> int: return self.kwargs.get('comment_id', '')
    @property
    def base_icon(self) -> str: return icon.MENU_ICON_SET[self.app_name]
    @property
    def base_color(self) -> str: return color.COLOR_SET[self.app_name]

    @property
    def title(self) -> str:
        string = self.menu
        string += f' {self.post_id}' if self.post_id else ''
        string += f' - {self.comment_id}' if self.comment_id else ''
        return string

    @property
    def target_id(self) -> str:
        category = self.category
        category = category if type(category) == int else category[0]
        string = f'{self.view_type}Content{category}'
        string += f'-post{self.post_id}' if self.post_id else ''
        string += f'-comment{self.comment_id}' if self.comment_id else ''
        return string

    @property
    def comment_list_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:comment_list', args=[self.post_id])

    @property
    def comment_list_content_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:comment_list_content', args=[self.post_id])

    @property
    def comment_create_url(self) -> reverse_lazy:
        return reverse_lazy(f'{self.app_name}:comment_create', args=[self.post_id])

    @property
    def info(self):
        return {
            'app_name': self.app_name,
            'menu': self.menu,
            'category': self.category,
            'type': self.view_type,
            'title': self.title,
            'pagination_url': self.comment_list_content_url,
            'target_id': self.target_id,
            'icon': self.base_icon,
            'color': self.base_color,
            'post_id': self.post_id,
            'comment_id': self.comment_id,
            'comment_list_url': self.comment_list_url,
            'comment_list_content_url': self.comment_list_content_url,
            'comment_create_url': self.comment_create_url,
        }

    # def get_success_url(self):
    #     if self.view_type == 'postDelete':
    #         return reverse_lazy(f'{self.app_name}:list')
    #     elif self.view_type in ['postUpdate', 'commentCreate', 'commentDelete']:
    #         return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])
    #     elif self.view_type == 'commentUpdate':
    #         return reverse_lazy(f'{self.app_name}:comment_detail', args=[self.comment_id])


class CommentListView(TemplateView):
    post_model = Post
    comment_model = Comment
    lookup_field = 'id'
    lookup_url_kwarg = 'post_id'
    template_name = 'board/comment_list.html'
    context_object_name = 'comments'
    paginate_by = 10
    view_type = 'commentList'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_id = self.kwargs.get('post_id')
        # post = self.post_model.objects.get(id=self.post_id)
        comments = self.comment_model.objects.filter(post_id=post_id)
        context['comments'] = comments
        return context

    # def get_queryset(self):
    #     queryset = self.model.objects.get(id=self.post_id)
    #     return queryset

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['info'] = self.info
    #     return context


class CommentListContentView(TemplateView):
    pass


class CommentDetailView(CommentViewMixIn, DetailView):
    view_type = 'commentDetail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class CommentCreateView(LoginRequiredMixin, CommentViewMixIn, CreateView):
    view_type = 'commentCreate'

    def get_success_url(self):
        super().get_success_url()

    def get(self, request, *args, **kwargs):
        return redirect(reverse_lazy(f'{self.app_name}:detail', args=[self.post_id]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        return context


class CommentUpdateView(LoginRequiredMixin, CommentViewMixIn, UpdateView):
    view_type = 'commentUpdate'

    def get_success_url(self):
        return reverse_lazy(f'{self.app_name}:comment_list', args=[self.post_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = self.info
        context['comment'] = self.object
        context['info']['target_id'] = f'commentUpdateContent{self.post_id}'
        return context


class CommentDeleteView(LoginRequiredMixin, CommentViewMixIn, DeleteView):
    view_type = 'commentDelete'

    def get_success_url(self):
        return reverse_lazy(f'{self.app_name}:detail', args=[self.post_id])

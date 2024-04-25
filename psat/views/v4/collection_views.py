import django.contrib.auth.mixins as auth_mixins
import vanilla
from django.urls import reverse_lazy

from . import problem_views
from .viewmixins import collection_view_mixins


class ListView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for loading collection card."""
    template_name = 'psat/v4/snippets/collection_list.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        collection_ids = self.get_post_getlist_variable('collection')
        if collection_ids:
            collections = self.get_sorted_collections(collection_ids)
        else:
            collections = self.get_all_collections()
        context['collections'] = collections
        return context


class ItemView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    problem_views.ListView
):
    template_name = 'psat/v4/snippets/collection_item_card.html'

    def get_template_names(self):
        return self.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_id = self.get_user_id()
        pk = self.get_collection_pk()
        item_ids = self.get_post_getlist_variable('item')

        target_collection = self.get_all_collections().get(pk=pk)
        if item_ids:
            items = self.get_sorted_items(item_ids, target_collection)
        else:
            items = self.get_all_items_by_collection(target_collection)
        custom_data = self.get_custom_data(user_id)
        context.update({
            'target_collection': target_collection,
            'items': items,
            'like_data': custom_data['like'],
            'rate_data': custom_data['rate'],
            'solve_data': custom_data['solve'],
            'memo_data': custom_data['memo'],
            'tag_data': custom_data['tag'],
            'collection_data': custom_data['collection'],
            'comment_data': custom_data['comment'],
        })
        return context


class ModalItemAddView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#add_item'

    def get_context_data(self, **kwargs):
        problem_id = self.request.GET.get('problem_id')
        icon_id = self.request.GET.get('icon_id')
        collection_ids = self.get_collection_ids_by_problem_id(problem_id)
        collections = self.get_collections_for_modal_item_add(collection_ids)
        return super().get_context_data(
            problem_id=problem_id,
            icon_id=icon_id,
            collections=collections,
            **kwargs,
        )


class ModalUpdateView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#update_collection'

    def get_context_data(self, **kwargs):
        pk = self.request.GET.get('collection')
        collection = self.get_all_collections().get(pk=pk)
        return super().get_context_data(collection=collection, **kwargs)


class CreateView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.CreateView,
):
    template_name = 'psat/v4/snippets/collection_create.html'

    def get_success_url(self):
        return reverse_lazy('psat:collection_list')

    def form_valid(self, form):
        form = form.save(commit=False)
        form = self.set_collection_order_for_create(form)
        return super().form_valid(form)


class CreateInModalView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.CreateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#create_collection'

    def get_success_url(self):
        problem_id = self.request.POST.get('problem_id')
        icon_id = self.request.POST.get('icon_id')
        base_url = reverse_lazy('psat:collection_modal_item_add')
        return f'{base_url}problem_id={problem_id}&icon_id={icon_id}'

    def form_valid(self, form):
        form = form.save(commit=False)
        form = self.set_collection_order_for_create(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        problem_id = self.request.GET.get('problem_id')
        return super().get_context_data(problem_id=problem_id, **kwargs)


class UpdateView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.UpdateView,
):
    template_name = 'psat/v4/snippets/collection_list.html#update_collection'

    def get_success_url(self):
        return reverse_lazy('psat:collection_list')

    def get_context_data(self, **kwargs):
        return super().get_context_data(collection_id=self.object.id, **kwargs)


class DeleteView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.DeleteView,
):
    def get_success_url(self):
        return reverse_lazy('psat:collection_list')

    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        self.update_collection_ordering_after_delete()
        return res


class ItemAddView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/icon_container.html#collection'

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        target_collection = self.get_all_collections().get(pk=pk)
        problem_id = self.request.POST.get('problem_id')
        is_checked = self.request.POST.get('is_checked')
        collections, is_active = self.update_item_add_status(
            target_collection, problem_id, is_checked)
        context = self.get_context_data(
            is_active=is_active,
            icon_collection=self.ICON_COLLECTION,
            **kwargs,
        )
        return self.render_to_response(context)

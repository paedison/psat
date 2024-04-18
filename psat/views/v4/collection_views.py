import django.contrib.auth.mixins as auth_mixins
import vanilla

from .viewmixins import collection_view_mixins as mixins


class IndexView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for loading collection card."""
    template_name = 'psat/v4/snippets/collection.html'

    def get_context_data(self, **kwargs):
        collections = self.get_all_collections()
        target_collection = collections[0] if collections else None
        items = self.get_all_items_for_collection(target_collection)
        return super().get_context_data(
            icon_image=self.ICON_IMAGE,
            collections=collections,
            target_collection=target_collection,
            items=items,
            **kwargs,
        )


class ItemView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection.html#reload_card_item'

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk')
        target_collection = self.get_all_collections().get(pk=pk)
        items = self.get_all_items_for_collection(target_collection)
        return super().get_context_data(
            icon_image=self.ICON_IMAGE,
            target_collection=target_collection,
            items=items,
            **kwargs,
        )


class ReloadView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection.html#reload_card'

    def get_context_data(self, **kwargs):
        collections = self.get_all_collections()
        target_collection = collections[0]
        items = self.get_all_items_for_collection(target_collection)
        return super().get_context_data(
            icon_image=self.ICON_IMAGE,
            collections=collections,
            target_collection=target_collection,
            items=items,
            **kwargs,
        )


class SortListView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for sorting collection list."""
    template_name = 'psat/v4/snippets/collection.html#reload_card_list'

    def post(self, request, *args, **kwargs):
        collection_ids_order = self.request.POST.getlist('collection')
        collections = self.get_collections_for_sort_list(collection_ids_order)
        context = self.get_context_data(collections=collections, **kwargs)
        return self.render_to_response(context)


class SortItemView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for sorting collection list."""
    template_name = 'psat/v4/snippets/collection.html#reload_card_item'

    def post(self, request, *args, **kwargs):
        item_ids_order = self.request.POST.getlist('item')
        pk = self.request.POST.get('collection')
        target_collection = self.get_all_collections().get(pk=pk)
        items = self.get_collections_for_sort_item(item_ids_order, target_collection)
        context = self.get_context_data(
            icon_image=self.ICON_IMAGE,
            target_collection=target_collection,
            items=items,
            **kwargs,
        )
        return self.render_to_response(context)


class ModalItemAddView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#add_item'

    def get_context_data(self, **kwargs):
        problem_id = self.request.GET.get('problem_id')
        icon_id = self.request.GET.get('icon_id')
        collections = self.get_collections_for_modal_item_add(problem_id)
        return super().get_context_data(
            problem_id=problem_id,
            icon_id=icon_id,
            collections=collections,
            **kwargs,
        )


class ModalUpdateView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#update_collection'

    def get_context_data(self, **kwargs):
        pk = self.request.GET.get('collection')
        collection = self.get_all_collections().get(pk=pk)
        return super().get_context_data(collection=collection, **kwargs)


class CreateView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.CreateView,
):
    template_name = 'psat/v4/snippets/collection.html#create_collection'

    def get_success_url(self):
        return self.get_url('collection_reload')

    def form_valid(self, form):
        form = form.save(commit=False)
        form = self.set_collection_order_for_create(form)
        return super().form_valid(form)


class CreateInModalView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.CreateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#create_collection'

    def get_success_url(self):
        problem_id = self.request.POST.get('problem_id')
        icon_id = self.request.POST.get('icon_id')
        base_url = self.get_url('collection_modal_item_add')
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
    mixins.BaseMixIn,
    vanilla.UpdateView,
):
    template_name = 'psat/v4/snippets/collection.html#update_collection'

    def get_success_url(self):
        return self.get_url('collection_reload')

    def get_context_data(self, **kwargs):
        return super().get_context_data(collection_id=self.object.id, **kwargs)


class DeleteView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
    vanilla.DeleteView,
):
    def get_success_url(self):
        return self.get_url('collection_reload')

    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        self.update_collection_ordering_after_delete()
        return res


class ItemAddView(
    auth_mixins.LoginRequiredMixin,
    mixins.BaseMixIn,
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

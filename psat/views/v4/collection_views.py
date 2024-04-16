import django.contrib.auth.mixins as auth_mixins
import vanilla
from django.db import transaction
from django.db.models import Case, When, BooleanField
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from psat import models as custom_models
from psat.utils import get_max_order, get_new_ordering
from .viewmixins import collection_view_mixins


class IndexView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for loading collection card."""
    template_name = 'psat/v4/snippets/collection.html'

    def get(self, request, *args, **kwargs):
        self.get_properties()

        collections = self.get_collection_qs()
        target_collection = collections[0] if collections else None
        items = self.get_collection_items_qs(
            collection_id=target_collection.id) if target_collection else None
        context = self.get_context_data(
            icon_image=self.ICON_IMAGE,
            collections=collections,
            target_collection=target_collection,
            items=items,
        )
        return self.render_to_response(context)


class ItemView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection.html#reload_card_item'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        target_collection = self.collection
        context = self.get_context_data(
            icon_image=self.ICON_IMAGE,
            target_collection=target_collection,
            items=self.collection_items,
        )
        return self.render_to_response(context)


class ReloadView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection.html#reload_card'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        collections = self.get_collection_qs()
        items = self.get_collection_items_qs(collection_id=collections[0].id)
        context = self.get_context_data(
            icon_image=self.ICON_IMAGE,
            collections=collections,
            target_collection=collections[0],
            items=items,
        )
        return self.render_to_response(context)


class SortListView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for sorting collection list."""
    template_name = 'psat/v4/snippets/collection.html#reload_card_list'

    def post(self, request, *args, **kwargs):
        self.get_properties()
        collection_ids_order = self.request.POST.getlist('collection')
        collections = []
        for idx, pk in enumerate(collection_ids_order, start=1):
            collection = self.collection_model.objects.get(pk=pk)
            collection.order = idx
            collection.save()
            collections.append(collection)
        context = self.get_context_data(
            collections=collections,
        )
        return self.render_to_response(context)


class SortItemView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for sorting collection list."""
    template_name = 'psat/v4/snippets/collection.html#reload_card_item'

    def post(self, request, *args, **kwargs):
        self.get_properties()
        item_ids_order = self.request.POST.getlist('item')
        collection_id = self.request.POST.get('collection')
        target_collection = self.collection_model.objects.get(id=collection_id)
        items = []
        for idx, pk in enumerate(item_ids_order, start=1):
            item = self.get_collection_item_qs(pk)
            item.order = idx
            item.save()
            items.append(item)
        context = self.get_context_data(
            icon_image=self.ICON_IMAGE,
            target_collection=target_collection,
            items=items,
        )
        return self.render_to_response(context)


class ModalItemAddView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#add_item'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        problem_id = self.request.GET.get('problem_id')
        icon_id = self.request.GET.get('icon_id')

        target_collections = (
            self.item_model.objects
            .filter(collection__user_id=self.user_id, problem_id=problem_id, is_active=True)
            .values_list('collection_id', flat=True).distinct()
        )
        collections = (
            self.get_collection_qs()
            .annotate(item_exists=Case(
                When(id__in=target_collections, then=1),
                default=0,
                output_field=BooleanField())
            )
        )
        context = self.get_context_data(
            problem_id=problem_id,
            icon_id=icon_id,
            collections=collections,
        )
        return self.render_to_response(context)


class ModalUpdateView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#update_collection'

    def get(self, request, *args, **kwargs):
        self.get_properties()

        collection_id = self.request.GET.get('collection')
        collection = self.collection_model.objects.get(id=collection_id)
        context = self.get_context_data(
            collection=collection,
        )
        return self.render_to_response(context)


class CreateView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.CreateView,
):
    success_url = reverse_lazy('psat:collection_reload')
    template_name = 'psat/v4/snippets/collection.html#create_collection'

    def form_valid(self, form):
        self.get_properties()

        form = form.save(commit=False)
        existing_collections = self.get_collection_qs()
        max_order = get_max_order(existing_collections)

        with transaction.atomic():
            form.user_id = self.user_id
            form.order = max_order
            self.object = form.save()
        return HttpResponseRedirect(self.success_url)


class CreateInModalView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.CreateView,
):
    template_name = 'psat/v4/snippets/collection_modal.html#create_collection'

    def form_valid(self, form):
        self.get_properties()
        form = form.save(commit=False)
        problem_id = self.request.POST.get('problem_id')

        existing_collections = self.get_collection_qs()
        max_order = get_max_order(existing_collections)

        with transaction.atomic():
            form.user_id = self.user_id
            form.order = max_order
            self.object = form.save()
            collection_modal_url = reverse_lazy('psat:collection_modal_item_add')
            success_url = f'{collection_modal_url}?problem_id={ problem_id }&icon_id=psatCollection{ problem_id }"'
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        problem_id = self.request.GET.get('problem_id')
        return super().get_context_data(problem_id=problem_id, **kwargs)


class UpdateView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.UpdateView,
):
    success_url = reverse_lazy('psat:collection_reload')
    template_name = 'psat/v4/snippets/collection.html#update_collection'

    def get_context_data(self, **kwargs):
        return super().get_context_data(collection_id=self.object.id, **kwargs)


class DeleteView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.DeleteView,
):
    def post(self, request, *args, **kwargs):
        self.get_properties()
        self.object = self.get_object()
        self.object.delete()

        collections = self.get_collection_qs()
        new_ordering = get_new_ordering(collections)
        for order, collection in zip(new_ordering, collections):
            collection.order = order
            collection.save()

        success_url = reverse_lazy('psat:collection_reload')
        return HttpResponseRedirect(success_url)


class ItemAddView(
    auth_mixins.LoginRequiredMixin,
    collection_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    template_name = 'psat/v4/snippets/icon_container.html#collection'

    def post(self, request, *args, **kwargs):
        self.get_properties()
        collection_id = self.kwargs.get('collection_id')
        problem_id = self.request.POST.get('problem_id')
        is_checked = self.request.POST.get('is_checked')

        existing_items = self.get_collection_items_qs()
        max_order = get_max_order(existing_items)

        if is_checked:
            try:
                collection_item = custom_models.CollectionItem.objects.get(
                    collection_id=collection_id, problem_id=problem_id)
                collection_item.is_active = True
                collection_item.save()
            except custom_models.CollectionItem.DoesNotExist:
                custom_models.CollectionItem.objects.create(
                    collection_id=collection_id, problem_id=problem_id, order=max_order)
        else:
            try:
                collection_item = custom_models.CollectionItem.objects.get(
                    collection_id=collection_id, problem_id=problem_id)
                collection_item.is_active = False
                collection_item.save()
            except custom_models.CollectionItem.DoesNotExist:
                pass
        collection = custom_models.Collection.objects.filter(
            collection_items__problem_id=problem_id,
            collection_items__is_active=True,
        )
        is_active = True if collection else False
        context = self.get_context_data(
            is_active=is_active,
            icon_collection=self.ICON_COLLECTION,
        )
        return self.render_to_response(context)

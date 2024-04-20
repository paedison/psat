from django.db.models import Case, When, BooleanField, F

from psat import forms, models
from psat import utils
from . import base_mixins


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    """Setting mixin for Collection views."""

    model = models.Collection
    form_class = forms.CollectionForm

    def get_all_collections(self):
        return (
            self.collection_model.objects
            .filter(user_id=self.request.user.id, is_active=True)
        )

    def get_all_items_for_collection(self, collection):
        if collection:
            return (
                self.item_model.objects
                .filter(collection=collection, is_active=True)
                .select_related(
                    'problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
                .annotate(
                    year=F('problem__psat__year'), ex=F('problem__psat__exam__abbr'),
                    sub=F('problem__psat__subject__abbr'), number=F('problem__number'),
                    question=F('problem__question')))

    def get_post_getlist_variable(self, variable: str):
        return self.request.POST.getlist(variable)

    def get_collections_for_sort_list(self, collection_ids):
        collections = []
        for idx, pk in enumerate(collection_ids, start=1):
            collection = self.collection_model.objects.get(pk=pk)
            collection.order = idx
            collection.save()
            collections.append(collection)
        return collections

    def get_collections_for_sort_item(self, item_ids, collection):
        items = []
        for idx, pk in enumerate(item_ids, start=1):
            item = self.get_all_items_for_collection(collection).get(pk=pk)
            item.order = idx
            item.save()
            items.append(item)
        return items

    def get_collection_ids_by_problem_id(self, problem_id):
        return (
            self.item_model.objects
            .filter(
                collection__user_id=self.request.user.id,
                problem_id=problem_id, is_active=True)
            .values_list('collection_id', flat=True).distinct()
        )

    def get_collections_for_modal_item_add(self, collection_ids):
        item_exists_case = Case(
            When(id__in=collection_ids, then=1),
            default=0,
            output_field=BooleanField()
        )
        return self.get_all_collections().annotate(item_exists=item_exists_case)

    def set_collection_order_for_create(self, form):
        existing_collections = self.get_all_collections()
        max_order = utils.get_max_order(existing_collections)
        form.user_id = self.request.user.id
        form.order = max_order
        return form

    def update_collection_ordering_after_delete(self):
        collections = self.get_all_collections()
        new_ordering = utils.get_new_ordering(collections)
        for order, collection in zip(new_ordering, collections):
            collection.order = order
            collection.save()

    def update_item_add_status(self, target_collection, problem_id, is_checked):
        existing_items = self.get_all_items_for_collection(target_collection)
        max_order = utils.get_max_order(existing_items)

        def get_item_for_add():
            return self.item_model.objects.get(
                collection=target_collection, problem_id=problem_id)

        def get_active_collections_for_problem_id():
            return self.collection_model.objects.filter(
                collection_items__problem_id=problem_id,
                collection_items__is_active=True,
            )

        if is_checked:
            try:
                item = get_item_for_add()
                item.is_active = True
                item.save()
            except self.item_model.DoesNotExist:
                self.item_model.objects.create(
                    collection=target_collection, problem_id=problem_id, order=max_order)
        else:
            try:
                item = get_item_for_add()
                item.is_active = False
                item.save()
            except self.item_model.DoesNotExist:
                pass
        collections = get_active_collections_for_problem_id()
        is_active = True if collections else False
        return collections, is_active

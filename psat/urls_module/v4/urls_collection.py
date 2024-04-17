from django.urls import path

from psat.views.v4 import collection_views as v

# basic url: 'psat/collection/'

urlpatterns = [
    path('', v.IndexView.as_view(), name='collection_index'),
    path('<int:pk>/', v.ItemView.as_view(), name='collection_item'),
    path('reload/', v.ReloadView.as_view(), name='collection_reload'),

    path('sort/list/', v.SortListView.as_view(), name='collection_list_sort'),
    path('sort/item/', v.SortItemView.as_view(), name='collection_item_sort'),

    path('modal/item/add/', v.ModalItemAddView.as_view(), name='collection_modal_item_add'),
    path('modal/update/', v.ModalUpdateView.as_view(), name='collection_modal_update'),

    path('create/', v.CreateView.as_view(), name='collection_create'),
    path('create/in_modal/', v.CreateInModalView.as_view(), name='collection_create_in_modal'),

    path('<int:pk>/update/', v.UpdateView.as_view(), name='collection_update'),
    path('<int:pk>/delete/', v.DeleteView.as_view(), name='collection_delete'),
    path('<int:pk>/item/add/', v.ItemAddView.as_view(), name='collection_item_add'),
]

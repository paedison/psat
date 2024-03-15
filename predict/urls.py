from django.urls import path, include

urlpatterns = [
    path('', include('predict.urls_module.normal_urls_v1')),  # Predict normal current version
    path('admin/', include('predict.urls_module.admin_urls_v1')),  # Predict admin current version
    path('analysis/', include('predict.urls_module.analysis_urls_v1')),  # Predict admin current version
]

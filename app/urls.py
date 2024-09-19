from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_image, name='upload_image'),
    path('map/', views.map_view, name='map_view'),
    path('delete_all/', views.delete_all_items, name='delete_all_items'),
    path('detect_labels_api/', views.detect_labels_api, name='detect_labels_api'),
]

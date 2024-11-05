from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('return_upload/', views.return_upload_image, name='return_upload_image'),
    path('upload/', views.upload_image, name='upload_image'),
    # path('upload_result/', views.upload_result, name='upload_result'),
    path('result/', views.upload_image_result, name='upload_image_result'),
    path('warning/', views.warning_page, name='warning_page'),
    path('map/', views.map_view, name='map_view'),
    path('delete_all/', views.delete_all_items, name='delete_all_items'),
    path('resize_image_api/', views.resize_image_api, name='resize_image_api'),
    path('detect_labels_api/', views.detect_labels_api, name='detect_labels_api'),
    path('search/', views.search_items, name='search_items')
]
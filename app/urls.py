from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('return_upload/', views.return_upload_image, name='return_upload_image'),
    path('upload/', views.upload_image, name='upload_image'),
    path('result/', views.upload_image_result, name='upload_image_result'),
    path('warning/', views.warning_page, name='warning_page'),
    path('map/', views.map_view, name='map_view'),
    path('delete_all/', views.delete_all_items, name='delete_all_items'),
    # path('detect_labels_api/', views.detect_labels_api, name='detect_labels_api'),
    path('search/', views.search_items, name='search_items'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('User_register/', views.User_register, name='User_register'),
    path('User_register_confirm/', views.User_register_confirm, name='User_register_confirm'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('chat_room_list/', views.chat_room_list, name='chat_room_list'),
    path('chat-room_check/', views.chat_room_check, name='chat_room_check'),
    path('chat-room_create/', views.chat_room_create, name='chat_room_create'),
    path('chat-room/<int:chat_room_id>/', views.chat_room, name='chat-room'),
    path('chat/send_message/<int:chatroom_id>/', views.send_message, name='send_message'),
    path('block_user/<str:user_nickname>/', views.block_user, name='block_user'),
    path('unblock_user/<str:user_nickname>/', views.unblock_user, name='unblock_user'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
      path('delete_file/', views.delete_file, name='delete_file'),
          path('download/<str:folder_name>/', views.download_folder, name='download_folder'),
]

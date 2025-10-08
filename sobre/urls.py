# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.sobre_nos, name='sobre'),
    path('admin/videos/upload/', views.upload_video_historia, name='upload_video_historia'),
    path('admin/videos/', views.lista_videos_historia, name='lista_videos_historia'),
    path('admin/videos/editar/<int:video_id>/', views.editar_video_historia, name='editar_video_historia'),
    path('admin/videos/excluir/<int:video_id>/', views.excluir_video_historia, name='excluir_video_historia'),
]
# admin.py
from django.contrib import admin
from .models import VideoHistoria

@admin.register(VideoHistoria)
class VideoHistoriaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'ativo', 'ordem_exibicao', 'data_criacao']
    list_filter = ['ativo', 'data_criacao']
    search_fields = ['titulo', 'descricao']
    list_editable = ['ativo', 'ordem_exibicao']
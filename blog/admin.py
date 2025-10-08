from django.contrib import admin
from .models import Publicacao, Categoria, Comentario, Avaliacao

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(Publicacao)
class PublicacaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'categoria', 'data_publicacao', 'publicado', 'visualizacoes']
    list_filter = ['publicado', 'categoria', 'data_publicacao']
    search_fields = ['titulo', 'conteudo']
    prepopulated_fields = {'slug': ('titulo',)}
    date_hierarchy = 'data_publicacao'

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['autor', 'publicacao', 'data_criacao', 'total_likes']
    list_filter = ['data_criacao']
    search_fields = ['autor__email', 'texto', 'publicacao__titulo']
    # ✅ REMOVIDO: ações de aprovação
    
    def total_likes(self, obj):
        return obj.total_likes()
    total_likes.short_description = 'Likes'
    
@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['publicacao', 'usuario', 'nota', 'data_criacao']
    list_filter = ['nota', 'data_criacao']
    search_fields = ['publicacao__titulo', 'usuario__username']
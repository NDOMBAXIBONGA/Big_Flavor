from django.urls import path
from . import views

urlpatterns = [
    #path("",views.Contacto, name="contacto"),
    path('', views.ContactoView.as_view(), name="contacto"),
    path('sucesso/', views.contacto_sucesso, name='contacto_sucesso'),
    
    # Alternativa com função-based view
    # path('contacto/', views.contacto_view, name='contacto'),
]

# views.py - VERSÃO CORRIGIDA
from django.shortcuts import render
from menu.models import Produto

def IndexView(request):
    return render(request, 'index.html')
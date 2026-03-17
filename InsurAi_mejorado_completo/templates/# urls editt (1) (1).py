# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ... tus otras rutas ...
    path('api/guardar-perfil/', views.guardar_perfil, name='api_guardar_perfil'),
    path('api/listar-perfiles/', views.listar_perfiles, name='api_listar_perfiles'),
]
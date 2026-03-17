from django.urls import path
from . import views

# Esto le da un "apellido" a tus rutas para que no choquen con otras


urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfiles/usuarios/', views.crear_perfiles_view, name='usuarios'),
    path('perfiles/usuarios/', views.crear_perfiles_view, name='usuarios'), # La tabla/lista
    path('perfiles/nuevo/', views.perfil_nuevo_view, name='perfil_nuevo'),
    path('administracion/perfiles/', views.perfiles_view, name='perfiles'), 
    path('api/guardar-perfil/', views.guardar_perfil, name='api_guardar_perfil'),
    path('api/listar-perfiles/', views.listar_perfiles, name='api_listar_perfiles'),
    path('crear-usuario/', views.crear_usuario_view, name='crear_usuario'),
]

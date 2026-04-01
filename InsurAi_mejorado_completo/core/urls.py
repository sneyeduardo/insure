from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include

# 1. Asegúrate de tener estas dos importaciones
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ==========================================
    # AUTENTICACIÓN Y DASHBOARD
    # ==========================================
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('recuperar-password/', views.recuperar_password_view, name='recuperar_password'),
    path('cambiar-password/<str:token>/', views.cambiar_password_view, name='cambiar_password'),

    # ==========================================
    # USUARIOS (Personas)
    # ==========================================
    # ¡AQUÍ ESTABA EL ERROR! Ahora apunta a views.usuarios_view
    path('usuarios/', views.usuarios_view, name='usuarios'), 
    path('usuarios/crear/', views.vista_crear_editar_usuario, name='crear_usuario'),
    path('usuarios/editar/<str:cedula>/', views.vista_crear_editar_usuario, name='editar_usuario'),

    # ==========================================
    # PERFILES (Roles)
    # ==========================================
    path('perfiles/', views.perfiles_view, name='perfiles'),
    path('perfiles/nuevo/', views.perfil_nuevo_view, name='perfil_nuevo'),
    path('perfiles/editar/<int:id_perfil>/', views.vista_perfil_editar, name='perfil_editar'),

    # ==========================================
    # RUTAS API (Fetch desde JavaScript)
    # ==========================================
    # APIs de Perfiles
    path('api/listar-perfiles/', views.api_listar_perfiles, name='api_listar_perfiles'),
    path('api/guardar-perfil/', views.api_guardar_perfil, name='api_guardar_perfil'),
    path('api/eliminar-perfil/', views.api_eliminar_perfil, name='api_eliminar_perfil'),
    path('api/actualizar-estados/', views.api_actualizar_estados, name='api_actualizar_estados'),
    
    # APIs de Usuarios
    path('api/listar-usuarios/', views.api_listar_usuarios, name='api_listar_usuarios'),
    path('api/guardar-usuario/', views.api_guardar_usuario, name='api_guardar_usuario'),
    path('api/eliminar-usuario/', views.api_eliminar_usuario, name='api_eliminar_usuario'),
    path('api/actualizar-estados-usuarios/', views.api_actualizar_estados_usuarios, name='api_actualizar_estados_usuarios'),
    
    # Otras APIs
    path('api/enviar-correo/', views.enviar_correo_compartir, name='enviar_correo_compartir'),
    path('api/obtener-catalogos/', views.api_obtener_catalogos, name='api_obtener_catalogos'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path
from . import views

# Esto le da un "apellido" a tus rutas para que no choquen con otras


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfiles/usuarios/', views.crear_perfiles_view, name='usuarios'),
    path('perfiles/usuarios/', views.crear_perfiles_view, name='usuarios'), # La tabla/lista
    path('perfiles/nuevo/', views.perfil_nuevo_view, name='perfil_nuevo'),
    path('administracion/perfiles/', views.perfiles_view, name='perfiles'), 
    path('perfiles/', views.vista_perfiles, name='perfiles'),
    path('perfiles/nuevo/', views.vista_perfil_nuevo, name='perfil_nuevo'),
    # Rutas API que llama tu JavaScript
    path('api/listar-perfiles/', views.api_listar_perfiles, name='api_listar_perfiles'),
    path('api/guardar-perfil/', views.api_guardar_perfil, name='api_guardar_perfil'),
    path('api/eliminar-perfil/', views.api_eliminar_perfil, name='api_eliminar_perfil'),
    path('api/actualizar-estados/', views.api_actualizar_estados),
    path('perfiles/editar/<int:id_perfil>/', views.vista_perfil_editar, name='perfil_editar'),
    path('usuarios/crear/', views.vista_crear_usuario, name='crear_usuario'),
    path('api/listar-usuarios/', views.api_listar_usuarios, name='api_listar_usuarios'),
    path('api/guardar-usuario/', views.api_guardar_usuario, name='api_guardar_usuario'),
    path('api/eliminar-usuario/', views.api_eliminar_usuario, name='api_eliminar_usuario'),
    path('api/actualizar-estados-usuarios/', views.api_actualizar_estados_usuarios, name='api_actualizar_estados_usuarios'),
    path('usuarios/crear/', views.vista_crear_editar_usuario, name='crear_usuario'), # ¡Ojo con esta coma!
    path('usuarios/editar/<int:id>/', views.vista_crear_editar_usuario, name='editar_usuario'),
    path('recuperar-password/', views.recuperar_password_view, name='recuperar_password'),
    path('cambiar-password/<str:token>/', views.cambiar_password_view, name='cambiar_password'), # <-- La apuntamos al login temporalmente
    path('api/enviar-correo/', views.enviar_correo_compartir, name='enviar_correo_compartir'),
]

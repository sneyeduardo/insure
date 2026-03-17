# views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PerfilUsuario

# 1. Vista para guardar un perfil nuevo
def guardar_perfil(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_perfil = PerfilUsuario.objects.create(
                nombre=data.get('nombre'),
                descripcion=data.get('descripcion'),
                estado=data.get('estado')
            )
            return JsonResponse({'status': 'success', 'mensaje': 'Perfil guardado con éxito'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

# 2. Vista para obtener los perfiles y mostrarlos en la tabla
def listar_perfiles(request):
    perfiles = PerfilUsuario.objects.all()
    datos = []
    for p in perfiles:
        datos.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            # Formateamos las fechas a DD/MM/YYYY para que coincida con tu diseño
            'fecha_creacion': p.fecha_creacion.strftime("%d/%m/%Y"),
            'fecha_actualizacion': p.fecha_actualizacion.strftime("%d/%m/%Y"),
            'estado': p.estado.upper()
        })
    return JsonResponse({'perfiles': datos})
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Polizas, Clientes, Siniestros
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PerfilUsuario
import json
from django.shortcuts import render


@login_required
def dashboard_view(request):
    # Contamos los datos de tu base de datos MySQL
    total_polizas = Polizas.objects.filter(activo=True).count()
    total_clientes = Clientes.objects.count()
    siniestros_pendientes = Siniestros.objects.filter(id_estatus__nombre='Pendiente').count()
    
    context = {
        'total_polizas': total_polizas,
        'total_clientes': total_clientes,
        'siniestros_pendientes': siniestros_pendientes,
    }
    return render(request, 'dashboard.html', context)

@login_required
def crear_perfiles_view(request):
    # Esta vista solo muestra el formulario de perfiles
    return render(request, 'usuarios.html')
@login_required
def perfil_nuevo_view(request):
    # Esta vista carga tu nuevo archivo perfil_nuevo.html
    return render(request, 'perfil_nuevo.html')
@login_required
def perfiles_view(request):
    # Esta vista carga tu nuevo archivo perfil_nuevo.html
    return render(request, 'perfiles.html')
def login_view(request):
    # 1. Si el usuario presiona el botón "Ingresar"
    if request.method == 'POST':
        usuario = request.POST.get('username')
        clave = request.POST.get('password')

        # 2. Django comprueba en la base de datos si los datos coinciden
        user = authenticate(request, username=usuario, password=clave)

        if user is not None:
            # 3. Datos correctos: Inicia sesión y lo envía adentro de la plataforma
            login(request, user)
            return redirect('dashboard') # Cambia 'dashboard' por el nombre de tu URL interna
        else:
            # 4. DATOS INCORRECTOS: Aquí es donde disparamos el mensaje de error
            messages.error(request, 'La información de inicio de sesión que ingresaste es incorrecta.')

    # 5. Carga la página vacía la primera vez, o la recarga si hubo un error
def guardar_perfil(request):
    if request.method == 'POST':
        try:
            # 1. Leemos los datos que envía tu fetch (HTML)
            data = json.loads(request.body)
            
            # 2. Traducimos el estado de texto a Booleano para MySQL
            estado_texto = data.get('estado')
            es_activo = True if estado_texto == 'activo' else False

            # 3. Guardamos usando los nombres exactos de TU modelo
            nuevo_perfil = PerfilUsuario.objects.create(
                nombre_perfil=data.get('nombre'),     # Frontend manda 'nombre', BD recibe 'nombre_perfil'
                descripcion=data.get('descripcion'),  # Este coincide perfecto
                estatus=es_activo                     # Le pasamos el True o False
            )
            
            return JsonResponse({'status': 'success', 'mensaje': 'Perfil guardado con éxito'})
            
        except Exception as e:
            # Si MySQL rechaza algo (ej. nombre_perfil duplicado), le avisamos al frontend
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=400)
            
    return JsonResponse({'status': 'invalid method'}, status=405)
def __str__(self):
        return self.nombre_perfil # <--- Corregido aquí

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
def crear_usuario_view(request):
    # Simplemente renderizamos el HTML
    return render(request, 'crear_usuarios.html')


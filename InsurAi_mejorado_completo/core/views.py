from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Polizas, Clientes, Siniestros
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

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
    return render(request, 'crear_perfiles.html')
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
   
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
from django.http import JsonResponse
from .models import PerfilUsuario
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Usuarios, Roles
import json
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.hashers import make_password

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
    
def vista_perfiles(request):
    return render(request, 'perfiles.html')

def vista_perfil_nuevo(request):
    return render(request, 'perfil_nuevo.html')

# 1. EL QUE LLENA LA TABLA (AHORA LEE DE 'ROLES')
def api_listar_perfiles(request):
    perfiles = Roles.objects.all()
    lista_datos = []
    
    for p in perfiles:
        # Formateamos las fechas a texto. Si son None (vacías), ponemos "N/A"
        f_creacion = p.fecha_creacion.strftime('%d/%m/%Y') if p.fecha_creacion else "N/A"
        f_actualizacion = p.fecha_actualizacion.strftime('%d/%m/%Y') if p.fecha_actualizacion else "N/A"
        
        lista_datos.append({
            'id': p.id_rol,
            'nombre': p.nombre_rol,
            'descripcion': p.descripcion if p.descripcion else "Sin descripción",
            'fecha_creacion': f_creacion,      # <--- Nombre exacto 1
            'fecha_actualizacion': f_actualizacion, # <--- Nombre exacto 2
            'estado': 'ACTIVO' if p.activo == 1 else 'INACTIVO'
        })
        
    return JsonResponse({'perfiles': lista_datos})

# 2. EL QUE ELIMINA (AHORA BORRA DE 'ROLES')
@require_http_methods(["POST"])
def api_eliminar_perfil(request):
    try:
        data = json.loads(request.body)
        perfiles_ids = data.get('ids', []) 
        
        if not perfiles_ids:
            return JsonResponse({'status': 'error', 'mensaje': 'No seleccionaste ningún perfil'})

        eliminados, _ = Roles.objects.filter(id_rol__in=perfiles_ids).delete()
        
        return JsonResponse({
            'status': 'success', 
            'mensaje': f'Se eliminaron {eliminados} perfil(es) correctamente'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})

# 3. EL QUE CAMBIA ESTATUS (AHORA ACTUALIZA 'ROLES')
@require_http_methods(["POST"])
def api_actualizar_estados(request):
    try:
        data = json.loads(request.body)
        cambios = data.get('cambios', {}) 
        
        for perfil_id, nuevo_estado in cambios.items():
            perfil = Roles.objects.get(id_rol=perfil_id)
            perfil.activo = 1 if nuevo_estado == 'ACTIVO' else 0
            perfil.save()
            
        return JsonResponse({'status': 'success', 'mensaje': 'Estados actualizados'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})
# --- 2. EL API QUE GUARDA (CREA O ACTUALIZA) ---
@require_http_methods(["POST"])
def api_guardar_perfil(request):
    try:
        data = json.loads(request.body)
        p_id = data.get('id')
        nombre = data.get('nombre').strip() 
        descripcion = data.get('descripcion')
        
        estado_str = data.get('estado', 'activo') 
        activo_val = 1 if estado_str.lower() == 'activo' else 0


        # --- AQUI ESTAN LOS MICROFONOS ---
        print("======== INTENTO DE GUARDAR PERFIL ========")
        print(f"ID recibido: '{p_id}'")
        print(f"Nombre: '{nombre}'")
        print(f"Descripción: '{descripcion}'")
        print("===========================================")

        busqueda_duplicado = Roles.objects.filter(nombre_rol__iexact=nombre)
        if p_id and str(p_id).strip() != "":
            busqueda_duplicado = busqueda_duplicado.exclude(id_rol=p_id)
            
        if busqueda_duplicado.exists():
            return JsonResponse({'status': 'error', 'mensaje': f'El perfil "{nombre}" ya existe.'})
        

        # Evaluar si realmente va a crear o editar
        if p_id and str(p_id).strip() != "" and str(p_id) != "undefined":
            print("✏️  MODO EDICIÓN ACTIVADO")
            perfil = Roles.objects.get(id_rol=p_id) 
            perfil.descripcion = descripcion
            perfil.activo = activo_val
            perfil.save()
            msg = "Perfil actualizado correctamente"
        else:
            print("🆕 MODO CREACIÓN ACTIVADO")
            Roles.objects.create(
                nombre_rol=nombre,
                descripcion=descripcion,
                activo=activo_val
            )
            msg = "Perfil creado con éxito"
            print("✅ CREADO EN LA BASE DE DATOS EXITOSAMENTE")
            
        return JsonResponse({'status': 'success', 'mensaje': msg})
    except Exception as e:
        print(f"🔥 EXPLOTÓ PYTHON: {str(e)}")
        return JsonResponse({'status': 'error', 'mensaje': str(e)})
def vista_crear_usuario(request):
    # Asumiendo que tu archivo HTML para el formulario se llama así
    return render(request, 'crear_usuarios.html')

def vista_crear_usuario(request, id_usuario=None):
    usuario_obj = None
    if id_usuario:
        try:
            usuario_obj = Usuarios.objects.get(id_usuario=id_usuario)
        except Usuarios.DoesNotExist:
            return redirect('usuarios')
    
    return render(request, 'crear_usuarios.html', {
        'usuario': usuario_obj
    })

# --- API PARA LISTAR USUARIOS ---
def api_listar_usuarios(request):
    # Traemos los usuarios de la tabla 'usuarios' en Aiven
    usuarios_list = Usuarios.objects.all().order_by('-fecha_creacion')
    data = []
    for u in usuarios_list:
        data.append({
            'id': u.id_usuario,
            'nombre': u.nombre_completo, # Enviamos el nombre completo aquí
            'username': u.username,      # Enviamos el username real
            'email': u.email,
            'ultimo_login': u.ultimo_login.strftime('%d/%m/%Y %H:%M') if u.ultimo_login else 'Sin ingreso',
            'estado': 'ACTIVO' if u.activo == 1 else 'INACTIVO'
        })
    return JsonResponse({'usuarios': data})
# --- API PARA GUARDAR (CREAR/EDITAR) ---
@require_http_methods(["POST"])
def api_guardar_usuario(request):
    try:
        data = json.loads(request.body)
        u_id = data.get('id')
        nombre = data.get('nombre').strip()
        username_f = data.get('username').strip()
        email = data.get('email')
        estado_str = data.get('estado')
        password_plana = data.get('password')
        
        activo_val = 1 if estado_str.lower() == 'activo' else 0

        # --- 🛡️ DETECTOR DE DUPLICADOS (NOMBRE Y USERNAME) ---
        # Verificamos Nombre Completo
        check_nombre = Usuarios.objects.filter(nombre_completo__iexact=nombre)
        # Verificamos Username
        check_user = Usuarios.objects.filter(username__iexact=username_f)

        if u_id:
            # Si editamos, ignoramos al usuario actual en la búsqueda
            check_nombre = check_nombre.exclude(id_usuario=u_id)
            check_user = check_user.exclude(id_usuario=u_id)

        if check_nombre.exists():
            return JsonResponse({'status': 'error', 'mensaje': f'El nombre "{nombre}" ya está registrado.'})
        
        if check_user.exists():
            return JsonResponse({'status': 'error', 'mensaje': f'El username "@{username_f}" ya está en uso.'})
        # ---------------------------------------------------

        if u_id:
            # --- MODO EDICIÓN ---
            usuario = Usuarios.objects.get(id_usuario=u_id)
            # Aunque el HTML sea readonly, por seguridad solo actualizamos lo permitido
            usuario.email = email
            usuario.activo = activo_val
            if password_plana:
                usuario.password_hash = make_password(password_plana)
            usuario.save()
            msg = "Usuario actualizado con éxito"
        else:
            # --- MODO CREACIÓN ---
            rol_defecto = Roles.objects.first() 
            
            if not rol_defecto:
                return JsonResponse({'status': 'error', 'mensaje': 'Debe existir al menos un rol en el sistema'})

            if not password_plana:
                return JsonResponse({'status': 'error', 'mensaje': 'La contraseña es obligatoria para nuevos usuarios'})

            # Aseguramos que intentos_fallidos y bloqueado NUNCA sean None
            Usuarios.objects.create(
                nombre_completo=nombre,
                email=email,
                username=username_f,
                activo=activo_val,
                id_rol=rol_defecto,
                fecha_creacion=timezone.now(),
                intentos_fallidos=0,  # <-- Forzamos el 0 aquí
                bloqueado=0,          # <-- Forzamos el 0 aquí
                password_hash=make_password(password_plana) 
            )
            msg = "Usuario creado con éxito"
            
        return JsonResponse({'status': 'success', 'mensaje': msg})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})

# --- API PARA ELIMINAR ---
@require_http_methods(["POST"])
def api_eliminar_usuario(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        Usuarios.objects.filter(id_usuario__in=ids).delete()
        return JsonResponse({'status': 'success', 'mensaje': f'Se eliminaron {len(ids)} usuarios'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})
@require_http_methods(["POST"])
def api_actualizar_estados_usuarios(request):
    try:
        data = json.loads(request.body)
        cambios = data.get('cambios', {}) # Recibe algo como: {'3': 'INACTIVO', '5': 'ACTIVO'}
        
        if not cambios:
            return JsonResponse({'status': 'error', 'mensaje': 'No hay cambios para guardar'})

        # Recorremos cada cambio y actualizamos la base de datos
        for u_id, nuevo_estado in cambios.items():
            try:
                usuario = Usuarios.objects.get(id_usuario=u_id)
                # Tu base de datos usa 1 para ACTIVO y 0 para INACTIVO
                usuario.activo = 1 if nuevo_estado.upper() == 'ACTIVO' else 0
                usuario.save()
            except Usuarios.DoesNotExist:
                continue # Si por alguna razón no encuentra el ID, salta al siguiente

        return JsonResponse({'status': 'success', 'mensaje': 'Estados actualizados correctamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})
def vista_crear_editar_usuario(request, id=None):
    contexto = {}
    
    if id:
        # MODO EDICIÓN: Buscamos al usuario en la base de datos
        try:
            u = Usuarios.objects.get(id_usuario=id)
            contexto['usuario'] = {
                'id': u.id_usuario,
                'nombre': u.nombre_completo,
                'username': u.username,
                'email': u.email,
                'estado': 'activo' if u.activo == 1 else 'inactivo',
                'fecha_creacion': u.fecha_creacion
            }
        except Usuarios.DoesNotExist:
            # Si el usuario no existe, puedes redirigir a la tabla o devolver un error
            pass 

    # MODO CREACIÓN: El contexto va vacío y el HTML mostrará los campos limpios
    return render(request, 'crear_usuarios.html', contexto)
# --- LA FUNCIÓN RESCATADA Y ACTUALIZADA A LA TABLA ROLES ---
def vista_perfil_editar(request, id_perfil):
    try:
        # CAMBIO: Usamos Roles e id_rol para que coincida con el resto del sistema
        perfil_a_editar = Roles.objects.get(id_rol=id_perfil)
        return render(request, 'perfil_nuevo.html', {
            'perfil': perfil_a_editar 
        })
    except Roles.DoesNotExist:
        return redirect('perfiles')
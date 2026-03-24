from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Polizas, Clientes, Siniestros
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from functools import wraps
from .models import Usuarios, Roles
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags




def requiere_autenticacion(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verificamos si existe la variable de sesión que creamos en el login
        if 'usuario_id' not in request.session:
            return redirect('login') # Lo mandamos pa' fuera si no está logueado
        return view_func(request, *args, **kwargs)
    return _wrapped_view

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

@requiere_autenticacion
def crear_perfiles_view(request):
    # Esta vista solo muestra el formulario de perfiles
    return render(request, 'usuarios.html')
@requiere_autenticacion
def perfil_nuevo_view(request):
    # Esta vista carga tu nuevo archivo perfil_nuevo.html
    return render(request, 'perfil_nuevo.html')
@requiere_autenticacion
def perfiles_view(request):
    # Esta vista carga tu nuevo archivo perfil_nuevo.html
    return render(request, 'perfiles.html')
def login_view(request):
    # Si la persona solo entra a la página (GET) o refresca, mostramos todo limpio
    if request.method == 'GET':
        return render(request, 'login.html')

    # Si la persona le dio al botón de "Ingresar" (POST)
    if request.method == 'POST':
        usuario_ingresado = request.POST.get('username')
        clave_ingresada = request.POST.get('password')

        try:
            user_obj = Usuarios.objects.get(username=usuario_ingresado)
            if check_password(clave_ingresada, user_obj.password_hash):
                
                if user_obj.estatus == 'ACTIVO' and user_obj.bloqueado == 0:
                    request.session['usuario_id'] = user_obj.id_usuario
                    request.session['username'] = user_obj.username
                    request.session['nombre_completo'] = user_obj.nombre_completo
                    return redirect('dashboard') 
                else:
                    messages.error(request, '⚠️ Tu cuenta está inactiva o bloqueada.')
            else:
                messages.error(request, '❌ Usuario o contraseña incorrectos.')
                
        except Usuarios.DoesNotExist:
            messages.error(request, '❌ Usuario o contraseña incorrectos.')

        # EL TRUCO ESTÁ AQUÍ: Redirigimos a la ruta del login para limpiar el POST
        return redirect('login')
def vista_perfiles(request):
    return render(request, 'perfiles.html')

def vista_perfil_nuevo(request):
    return render(request, 'perfil_nuevo.html')

# 1. EL QUE LLENA LA TABLA (AHORA LEE DE 'ROLES')
def api_listar_perfiles(request):
    perfiles = Roles.objects.all().order_by('id_rol') # Agregamos orden para que sea profesional
    lista_datos = []
    
    for p in perfiles:
        f_creacion = p.fecha_creacion.strftime('%d/%m/%Y') if p.fecha_creacion else "N/A"
        f_actualizacion = p.fecha_actualizacion.strftime('%d/%m/%Y') if p.fecha_actualizacion else "N/A"
        
        lista_datos.append({
            'id': p.id_rol,
            'nombre': p.nombre_rol,
            'descripcion': p.descripcion if p.descripcion else "Sin descripción",
            'fecha_creacion': p.fecha_creacion.strftime('%d/%m/%Y') if p.fecha_creacion else "N/A",
            'fecha_actualizacion': p.fecha_actualizacion.strftime('%d/%m/%Y') if p.fecha_actualizacion else "N/A",
            # CAMBIO: Usamos 'estatus' que es Booleano (True/False)
            'estado': p.estatus 
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
            # CAMBIO: Guardamos True si es 'ACTIVO', False si no
            perfil.estatus = nuevo_estado.upper() # Lo forzamos a mayúsculas para ser consistentes
            perfil.save()
            
        return JsonResponse({'status': 'success', 'mensaje': 'Estados actualizados'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})
# --- 2. EL API QUE GUARDA (CREA O ACTUALIZA) ---

@require_http_methods(["POST"])
def api_guardar_perfil(request): # Verifica si el nombre en tu urls.py es api_guardar_perfil
    try:
        data = json.loads(request.body)
        p_id = data.get('id')
        nombre = data.get('nombre').strip() 
        descripcion = data.get('descripcion')
        
        estado_recibido = data.get('estado', 'activo')
        
        # 2. 🚀 CORRECCIÓN: Lo convertimos a Booleano (True/False) usando la variable correcta
        estatus_val = True if estado_recibido.lower() == 'activo' else False

        busqueda_duplicado = Roles.objects.filter(nombre_rol__iexact=nombre)
        if p_id and str(p_id).strip() != "":
            busqueda_duplicado = busqueda_duplicado.exclude(id_rol=p_id)
            
        if busqueda_duplicado.exists():
            return JsonResponse({'status': 'error', 'mensaje': f'El perfil "{nombre}" ya existe.'})
        
        if p_id and str(p_id).strip() != "" and str(p_id) != "undefined":
            # MODO EDICIÓN
            perfil = Roles.objects.get(id_rol=p_id) 
            perfil.descripcion = descripcion
            perfil.estatus = estatus_val # Guardamos el True o False
            perfil.save()
            msg = "Perfil actualizado correctamente"
        else:
            # MODO CREACIÓN
            Roles.objects.create(
                nombre_rol=nombre,
                descripcion=descripcion,
                estatus=estatus_val # CAMBIO: Nombre del campo
            )
            msg = "Perfil creado con éxito"
            
        return JsonResponse({'status': 'success', 'mensaje': msg})
    except Exception as e:
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
# views.py

def api_listar_usuarios(request):
    # Traemos los usuarios de la tabla
    usuarios_list = Usuarios.objects.all().order_by('-fecha_creacion')
    data = []
    
    for u in usuarios_list:
        data.append({
            'id': u.id_usuario,
            'nombre': u.nombre_completo,
            'username': u.username,
            'email': u.email,
            'ultimo_login': u.ultimo_login.strftime('%d/%m/%Y %H:%M') if u.ultimo_login else 'Sin ingreso',
            # CORRECCIÓN: Ahora leemos directamente el texto de 'estatus'
            'estado': u.estatus if hasattr(u, 'estatus') else 'ACTIVO'
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
        password_plana = data.get('password')
        
        # --- NUEVOS CAMPOS ---
        estado_val = data.get('estado', 'ACTIVO').upper()
        rol_id_seleccionado = data.get('id_rol') # El ID que mandará el HTML

        # --- 🛡️ DETECTOR DE DUPLICADOS (NOMBRE Y USERNAME) ---
        check_nombre = Usuarios.objects.filter(nombre_completo__iexact=nombre)
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
            usuario.email = email
            usuario.estatus = estado_val # <-- CORRECCIÓN: Usamos estatus y estado_val
            
            # Si el formulario también envía el rol al editar, lo actualizamos
            if rol_id_seleccionado:
                usuario.id_rol = Roles.objects.get(id_rol=rol_id_seleccionado)

            if password_plana:
                usuario.password_hash = make_password(password_plana)
            usuario.save()
            msg = "Usuario actualizado con éxito"
        else:
            # --- MODO CREACIÓN ---
            # 1. Validamos que nos hayan enviado un rol
            if not rol_id_seleccionado:
                return JsonResponse({'status': 'error', 'mensaje': 'Debe seleccionar un rol para el usuario'})
                
            # 2. Buscamos el rol específico en la base de datos
            rol_asignado = Roles.objects.get(id_rol=rol_id_seleccionado) 

            if not password_plana:
                return JsonResponse({'status': 'error', 'mensaje': 'La contraseña es obligatoria para nuevos usuarios'})

            Usuarios.objects.create(
                nombre_completo=nombre,
                email=email,
                username=username_f,
                estatus=estado_val,      # <-- CORRECCIÓN: Guardamos el texto
                id_rol=rol_asignado,     # <-- CORRECCIÓN: Guardamos el rol seleccionado
                fecha_creacion=timezone.now(),
                intentos_fallidos=0,
                bloqueado=0,
                password_hash=make_password(password_plana) 
            )
            msg = "Usuario creado con éxito"
            
        return JsonResponse({'status': 'success', 'mensaje': msg})
    
    except Roles.DoesNotExist:
        return JsonResponse({'status': 'error', 'mensaje': 'El rol seleccionado no existe en la base de datos.'})
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
    contexto['roles'] = Roles.objects.all()
    if id:
        # MODO EDICIÓN: Buscamos al usuario en la base de datos
        try:
            u = Usuarios.objects.get(id_usuario=id)
            contexto['usuario'] = {
                'id': u.id_usuario,
                'nombre': u.nombre_completo,
                'username': u.username,
                'email': u.email,
                'estado': 'activo' if u.estatus == 'ACTIVO' else 'inactivo', # Actualizado al nuevo campo
                'fecha_creacion': u.fecha_creacion,
                'id_rol': u.id_rol.id_rol if u.id_rol else None # Extraemos el ID del rol para pre-seleccionarlo
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
def recuperar_password_view(request):
    if request.method == 'GET':
        return render(request, 'recuperar_password.html')

    if request.method == 'POST':
        usuario_ingresado = request.POST.get('username')
        email_ingresado = request.POST.get('email')
        
        try:
            usuario = Usuarios.objects.get(username=usuario_ingresado, email=email_ingresado)
            
            signer = TimestampSigner()
            token = signer.sign(usuario.id_usuario) 
            link_recuperacion = request.build_absolute_uri(reverse('cambiar_password', args=[token]))
            
            # Renderizamos el HTML del correo
            html_content = render_to_string('email_recuperacion.html', {
                'nombre_usuario': usuario.nombre_completo,
                'link': link_recuperacion,
                'logo_url': request.build_absolute_uri('/static/imagenes/inzur.png')
            })

            # --- ENVÍO A TRAVÉS DEL PUENTE DE GOOGLE ---
            url_puente = "https://script.google.com/macros/s/AKfycbywyfHwYo-S-MDAr9OdUxYp0RVD8-PXMCGSxcyk5U-M_aflxEQ54zt5OaP9utqRvvGosw/exec"
            
            payload = {
                "to": usuario.email,
                "subject": "Recuperar Contraseña - InzurAi+",
                "htmlBody": html_content
            }
            
            # Enviamos la petición al script (Puerto 443, no bloqueado)
            # Nota: Google Apps Script requiere seguir redirecciones (allow_redirects=True)
            respuesta = requests.post(url_puente, data=json.dumps(payload), allow_redirects=True)
            
            if respuesta.status_code == 200:
                print("🚀 ¡CORREO ENVIADO VÍA GOOGLE APPS SCRIPT!")
            else:
                print(f"🔥 ERROR EN EL PUENTE: {respuesta.text}")

        except Usuarios.DoesNotExist:
            print("🛑 Usuario no encontrado.")
        except Exception as e:
            print(f"🔥 ERROR FATAL: {str(e)}")

        messages.success(request, 'Si los datos son correctos, te hemos enviado un enlace de recuperación.')
        return redirect('recuperar_password')
def cambiar_password_view(request, token):
    signer = TimestampSigner()
    
    try:
        # Intentamos desencriptar el token. Le damos un tiempo de vida de 15 minutos (900 segundos)
        id_usuario = signer.unsign(token, max_age=900)
        usuario = Usuarios.objects.get(id_usuario=id_usuario)
        
    except SignatureExpired:
        messages.error(request, '❌ El enlace de recuperación ha expirado por seguridad (duración: 15 min). Solicita uno nuevo.')
        return redirect('recuperar_password')
    except (BadSignature, Usuarios.DoesNotExist):
        messages.error(request, '❌ El enlace de recuperación no es válido o está corrupto.')
        return redirect('recuperar_password')

    # Si el token es válido y es GET, mostramos el formulario
    if request.method == 'GET':
        return render(request, 'cambiar_password.html', {'token': token, 'nombre': usuario.nombre_completo})

    # Si el usuario envía la nueva contraseña (POST)
    if request.method == 'POST':
        nueva_clave = request.POST.get('password')
        confirmar_clave = request.POST.get('confirm_password')

        # Verificamos que coincidan por seguridad
        if nueva_clave and nueva_clave == confirmar_clave:
            usuario.password_hash = make_password(nueva_clave)
            usuario.save()
            
            # Mandamos un mensaje de éxito al login
            messages.success(request, '✅ ¡Contraseña actualizada con éxito! Ya puedes iniciar sesión.')
            return redirect('login')
        else:
            error_msg = '❌ Las contraseñas no coinciden.'
            return render(request, 'cambiar_password.html', {'token': token, 'nombre': usuario.nombre_completo, 'error_msg': error_msg})

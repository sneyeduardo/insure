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
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.urls import reverse
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import requests
from django.conf import settings
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# ==========================================
# DECORADOR DE SEGURIDAD
# ==========================================
def requiere_autenticacion(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login') 
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ==========================================
# VISTAS DE PÁGINAS (HTML)
# ==========================================
@requiere_autenticacion
def dashboard_view(request):
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
def usuarios_view(request):
    """Muestra la tabla principal de usuarios (Personas)"""
    return render(request, 'usuarios.html')

@requiere_autenticacion
def perfiles_view(request):
    """Muestra la tabla de Administración de Perfiles (Roles)"""
    return render(request, 'perfiles.html')

@requiere_autenticacion
def perfil_nuevo_view(request):
    """Carga el formulario para crear un nuevo perfil"""
    return render(request, 'perfil_nuevo.html')

@requiere_autenticacion
def vista_perfil_editar(request, id_perfil):
    """Carga el formulario para editar un perfil existente"""
    try:
        perfil_a_editar = Roles.objects.get(id_rol=id_perfil)
        return render(request, 'perfil_nuevo.html', {'perfil': perfil_a_editar})
    except Roles.DoesNotExist:
        return redirect('perfiles')

@requiere_autenticacion
def vista_crear_editar_usuario(request, cedula=None): 
    """Carga el formulario para crear o editar un Usuario (Persona)"""
    contexto = {}
    contexto['roles'] = Roles.objects.all()
    
    if cedula:
        try:
            u = Usuarios.objects.get(cedula=cedula)
            
            # Separamos el nombre completo para el frontend ("Jose Perez" -> "Jose" y "Perez")
            partes = u.nombre_completo.split(' ') if u.nombre_completo else ['', '']
            nombre_solo = partes[0]
            apellido_solo = ' '.join(partes[1:]) if len(partes) > 1 else ''

            # Extraemos la letra (V/E) y el número
            letra_cedula = u.cedula.split('-')[0] if '-' in u.cedula else 'V'
            numero_cedula = u.cedula.split('-')[1] if '-' in u.cedula else u.cedula

            contexto['usuario'] = {
                'cedula': numero_cedula,
                'letra_cedula': letra_cedula,
                'nombre': nombre_solo,
                'apellido': apellido_solo,
                'username': u.username,
                'email': u.email,
                'estado': 'activo' if u.estatus == 'ACTIVO' else 'inactivo', 
                'tipo_cliente': u.tipo_cliente,
                'sexo': u.sexo,
                'nacionalidad_pais': u.nacionalidad_pais,
                'actividad_economica': u.actividad_economica,
                'profesion': u.profesion,
                'direccion_fiscal': u.direccion_fiscal,
                'telefono_movil': u.telefono_movil,
                'telefono_oficina': u.telefono_oficina,
                'cuenta_bancaria': u.cuenta_bancaria,
                'banco': u.banco,
                'ingreso_promedio': u.ingreso_promedio,
                'fecha_nacimiento_constitucion': u.fecha_nacimiento_constitucion,
                'id_rol': u.id_rol.id_rol if u.id_rol else None 
            }
        except Usuarios.DoesNotExist:
            pass 

    return render(request, 'crear_usuarios.html', contexto)

# ==========================================
# AUTENTICACIÓN Y LOGIN
# ==========================================
def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    if request.method == 'POST':
        cedula_ingresada = request.POST.get('cedula') 
        clave_ingresada = request.POST.get('password')

        try:
            user_obj = Usuarios.objects.get(cedula=cedula_ingresada)
            
            if check_password(clave_ingresada, user_obj.password_hash):
                if user_obj.estatus == 'ACTIVO' and user_obj.bloqueado == 0:
                    request.session['usuario_id'] = user_obj.cedula 
                    request.session['username'] = user_obj.username
                    request.session['nombre_completo'] = user_obj.nombre_completo
                    
                    # Guardar la imagen en la sesión si existe
                    if hasattr(user_obj, 'imagen_perfil') and user_obj.imagen_perfil:
                        request.session['imagen_perfil'] = user_obj.imagen_perfil.url
                    else:
                        request.session['imagen_perfil'] = None
                    
                    user_obj.ultimo_login = timezone.now()
                    user_obj.save()
                
                    return redirect('dashboard') 
                else:
                    messages.error(request, '⚠️ Tu cuenta está inactiva o bloqueada.')
            else:
                messages.error(request, '❌ Cédula o contraseña incorrectos.')
                
        except Usuarios.DoesNotExist:
            messages.error(request, '❌ Cédula o contraseña incorrectos.')

        return redirect('login')

# ==========================================
# APIs DE PERFILES (ROLES)
# ==========================================
def api_listar_perfiles(request):
    perfiles = Roles.objects.all().order_by('id_rol') 
    lista_datos = []
    
    for p in perfiles:
        lista_datos.append({
            'id': p.id_rol,
            'nombre': p.nombre_rol,
            'descripcion': p.descripcion if p.descripcion else "Sin descripción",
            'fecha_creacion': p.fecha_creacion.strftime('%d/%m/%Y') if p.fecha_creacion else "N/A",
            'fecha_actualizacion': p.fecha_actualizacion.strftime('%d/%m/%Y') if p.fecha_actualizacion else "N/A",
            'estado': p.estatus 
        })
        
    return JsonResponse({'perfiles': lista_datos})

@require_http_methods(["POST"])
def api_guardar_perfil(request): 
    try:
        data = json.loads(request.body)
        p_id = data.get('id')
        nombre = data.get('nombre').strip() 
        descripcion = data.get('descripcion')
        
        estado_recibido = data.get('estado', 'activo')
        estatus_val = True if estado_recibido.lower() == 'activo' else False

        busqueda_duplicado = Roles.objects.filter(nombre_rol__iexact=nombre)
        if p_id and str(p_id).strip() != "":
            busqueda_duplicado = busqueda_duplicado.exclude(id_rol=p_id)
            
        if busqueda_duplicado.exists():
            return JsonResponse({'status': 'error', 'mensaje': f'El perfil "{nombre}" ya existe.'})
        
        if p_id and str(p_id).strip() != "" and str(p_id) != "undefined":
            perfil = Roles.objects.get(id_rol=p_id) 
            perfil.descripcion = descripcion
            perfil.estatus = estatus_val 
            perfil.save()
            msg = "Perfil actualizado correctamente"
        else:
            Roles.objects.create(
                nombre_rol=nombre,
                descripcion=descripcion,
                estatus=estatus_val 
            )
            msg = "Perfil creado con éxito"
            
        return JsonResponse({'status': 'success', 'mensaje': msg})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})

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

@require_http_methods(["POST"])
def api_actualizar_estados(request):
    try:
        data = json.loads(request.body)
        cambios = data.get('cambios', {}) 
        
        for perfil_id, nuevo_estado in cambios.items():
            perfil = Roles.objects.get(id_rol=perfil_id)
            perfil.estatus = nuevo_estado.upper()
            perfil.save()
            
        return JsonResponse({'status': 'success', 'mensaje': 'Estados actualizados'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})

# ==========================================
# APIs DE USUARIOS (PERSONAS)
# ==========================================
def api_listar_usuarios(request):
    usuarios_list = Usuarios.objects.all().order_by('-fecha_creacion')
    data = []
    
    for u in usuarios_list:
        data.append({
            'id': u.cedula,
            'nombre_completo': u.nombre_completo,
            'username': u.username,
            'email': u.email,
            'ultimo_login': u.ultimo_login.strftime('%d/%m/%Y %H:%M') if u.ultimo_login else 'Sin ingreso',
            'estado': u.estatus if hasattr(u, 'estatus') else 'ACTIVO',
            # --- CAMPOS PARA FILTROS Y REPORTES ---
            'tipo_cliente': getattr(u, 'tipo_cliente', 'N/A'),
            'sexo': getattr(u, 'sexo', 'N/A'),
            'nacionalidad': getattr(u, 'nacionalidad_pais', 'N/A'),
            'actividad': getattr(u, 'actividad_economica', 'N/A'),
            'profesion': getattr(u, 'profesion', 'N/A'),
            'telefono_movil': getattr(u, 'telefono_movil', 'N/A'),
            'telefono_oficina': getattr(u, 'telefono_oficina', 'N/A'),
            'banco': getattr(u, 'banco', 'N/A'),
            'cuenta_bancaria': getattr(u, 'cuenta_bancaria', 'N/A'),
            'direccion_fiscal': getattr(u, 'direccion_fiscal', 'No registrada'),
            'ingreso_promedio': str(u.ingreso_promedio) if u.ingreso_promedio else '0.00',
            'fecha_nacimiento_constitucion': u.fecha_nacimiento_constitucion.strftime('%Y-%m-%d') if u.fecha_nacimiento_constitucion else ''
        })
    return JsonResponse({'usuarios': data})
@require_http_methods(["POST"])
def api_guardar_usuario(request):
    try:
        post = request.POST
        # Sincronizamos con los nombres exactos que envía tu JavaScript
        cedula_f = post.get('cedula', '').strip()
        nombre_completo = post.get('nombre_completo')
        username_f = post.get('username', '').strip()
        email = post.get('email')
        password_plana = post.get('password')
        
        # CORRECCIÓN: Tu JS envía 'estatus', no 'estado'
        estado_val = post.get('estatus', 'ACTIVO').upper() 
        rol_id_seleccionado = post.get('id_rol')
        
        # Captura de todos los campos adicionales
        banco = post.get('banco')
        tipo_cliente = post.get('tipo_cliente')
        sexo = post.get('sexo')
        nacionalidad = post.get('nacionalidad_pais')
        actividad = post.get('actividad_economica')
        profesion = post.get('profesion')
        direccion = post.get('direccion_fiscal')
        movil = post.get('telefono_movil')
        oficina = post.get('telefono_oficina')
        cuenta = post.get('cuenta_bancaria')
        
        # Manejo de Fecha (Vital para la edad)
        fecha_nac = post.get('fecha_nacimiento_constitucion')
        if not fecha_nac: fecha_nac = None
        
        # Manejo de Ingreso Promedio (Decimal)
        ingreso_raw = post.get('ingreso_promedio', '').replace(',', '').strip()
        try:
            ingreso_final = Decimal(ingreso_raw) if ingreso_raw else None
        except (InvalidOperation, ValueError):
            ingreso_final = None

        imagen_perfil = request.FILES.get('imagen_perfil')
        
        # LÓGICA DE DETECCIÓN MEJORADA
        # Si el usuario ya existe en la BD, lo tratamos como edición
        usuario = Usuarios.objects.filter(cedula=cedula_f).first()

        if usuario:
            # --- MODO EDICIÓN ---
            usuario.nombre_completo = nombre_completo 
            usuario.email = email
            usuario.estatus = estado_val
            usuario.banco = banco
            usuario.tipo_cliente = tipo_cliente
            usuario.sexo = sexo
            usuario.nacionalidad_pais = nacionalidad
            usuario.actividad_economica = actividad
            usuario.profesion = profesion
            usuario.direccion_fiscal = direccion
            usuario.telefono_movil = movil
            usuario.telefono_oficina = oficina
            usuario.cuenta_bancaria = cuenta
            usuario.ingreso_promedio = ingreso_final
            usuario.fecha_nacimiento_constitucion = fecha_nac
            
            if rol_id_seleccionado:
                usuario.id_rol = Roles.objects.get(id_rol=rol_id_seleccionado)
            if password_plana:
                usuario.password_hash = make_password(password_plana)
            if imagen_perfil:
                usuario.imagen_perfil = imagen_perfil
            
            usuario.save()
            msg = "Usuario actualizado con éxito"
        else:
            # --- MODO CREACIÓN ---
            rol_asignado = Roles.objects.get(id_rol=rol_id_seleccionado) 
            nuevo_usuario = Usuarios.objects.create(
                cedula=cedula_f,
                nombre_completo=nombre_completo,
                email=email,
                username=username_f,
                estatus=estado_val,      
                id_rol=rol_asignado,     
                fecha_creacion=timezone.now(),
                intentos_fallidos=0,
                bloqueado=0,
                tipo_cliente=tipo_cliente,
                sexo=sexo,
                nacionalidad_pais=nacionalidad,
                actividad_economica=actividad,
                profesion=profesion,
                direccion_fiscal=direccion,
                telefono_movil=movil,
                telefono_oficina=oficina,
                cuenta_bancaria=cuenta,
                banco=banco,
                ingreso_promedio=ingreso_final,
                fecha_nacimiento_constitucion=fecha_nac,
                password_hash=make_password(password_plana) 
            )
            if imagen_perfil:
                nuevo_usuario.imagen_perfil = imagen_perfil
                nuevo_usuario.save()
            msg = "Usuario creado con éxito"
            
        return JsonResponse({'status': 'success', 'mensaje': msg})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})
    
@require_http_methods(["POST"])
def api_actualizar_estados_usuarios(request):
    try:
        data = json.loads(request.body)
        cambios = data.get('cambios', {}) 
        
        if not cambios:
            return JsonResponse({'status': 'error', 'mensaje': 'No hay cambios para guardar'})

        for u_id, nuevo_estado in cambios.items():
            try:
                usuario = Usuarios.objects.get(cedula=u_id)
                usuario.estatus = nuevo_estado.upper()
                usuario.save()
            except Usuarios.DoesNotExist:
                continue 

        return JsonResponse({'status': 'success', 'mensaje': 'Estados actualizados correctamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'mensaje': str(e)})

# ==========================================
# RECUPERACIÓN DE CONTRASEÑA Y CORREOS
# ==========================================
def recuperar_password_view(request):
    if request.method == 'GET':
        return render(request, 'recuperar_password.html')

    if request.method == 'POST':
        cedula_ingresada = request.POST.get('cedula')
        email_ingresado = request.POST.get('email')
        
        try:
            usuario = Usuarios.objects.get(cedula=cedula_ingresada, email=email_ingresado)
            
            signer = TimestampSigner()
            token = signer.sign(usuario.cedula) 
            link_recuperacion = request.build_absolute_uri(reverse('cambiar_password', args=[token]))
            
            html_content = render_to_string('email_recuperacion.html', {
                'nombre_usuario': usuario.nombre_completo,
                'link': link_recuperacion,
                'logo_url': request.build_absolute_uri('/static/imagenes/inzur.png')
            })

            url_puente = "https://script.google.com/macros/s/AKfycbywyfHwYo-S-MDAr9OdUxYp0RVD8-PXMCGSxcyk5U-M_aflxEQ54zt5OaP9utqRvvGosw/exec"
            
            payload = {
                "to": usuario.email,
                "subject": "Recuperar Contraseña - InzurAi+",
                "htmlBody": html_content
            }
            
            respuesta = requests.post(url_puente, data=json.dumps(payload), allow_redirects=True, timeout=15)
            
            if respuesta.status_code == 200:
                print("🚀 ¡CORREO ENVIADO VÍA GOOGLE APPS SCRIPT!")
            else:
                print(f"🔥 Error en el puente de Google: {respuesta.status_code} - {respuesta.text}")

        except Usuarios.DoesNotExist:
            print("🛑 Usuario no encontrado en la DB.")
        except Exception as e:
            print(f"🔥 ERROR FATAL EN LA VISTA: {str(e)}")

        messages.success(request, 'Si los datos son correctos, te hemos enviado un enlace de recuperación.')
        return redirect('recuperar_password')

def cambiar_password_view(request, token):
    signer = TimestampSigner()
    
    try:
        id_usuario = signer.unsign(token, max_age=900)
        usuario = Usuarios.objects.get(cedula=id_usuario) 
        
    except SignatureExpired:
        messages.error(request, '❌ El enlace de recuperación ha expirado por seguridad (duración: 15 min). Solicita uno nuevo.')
        return redirect('recuperar_password')
    except (BadSignature, Usuarios.DoesNotExist):
        messages.error(request, '❌ El enlace de recuperación no es válido o está corrupto.')
        return redirect('recuperar_password')

    if request.method == 'GET':
        return render(request, 'cambiar_password.html', {'token': token, 'nombre': usuario.nombre_completo})

    if request.method == 'POST':
        nueva_clave = request.POST.get('password')
        confirmar_clave = request.POST.get('confirm_password')

        if nueva_clave and nueva_clave == confirmar_clave:
            usuario.password_hash = make_password(nueva_clave)
            usuario.save()
            
            messages.success(request, '✅ ¡Contraseña actualizada con éxito! Ya puedes iniciar sesión.')
            return redirect('login')
        else:
            error_msg = '❌ Las contraseñas no coinciden.'
            return render(request, 'cambiar_password.html', {'token': token, 'nombre': usuario.nombre_completo, 'error_msg': error_msg})

def enviar_correo_compartir(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            correo_destino = data.get('correo')
            formato = data.get('formato', 'pdf')
            
            if not correo_destino:
                return JsonResponse({'status': 'error', 'mensaje': 'El correo es obligatorio.'})

            url_puente = "https://script.google.com/macros/s/AKfycbywyfHwYo-S-MDAr9OdUxYp0RVD8-PXMCGSxcyk5U-M_aflxEQ54zt5OaP9utqRvvGosw/exec"

            asunto = f"InzurAI+ - Reporte de Datos ({formato.upper()})"
            mensaje_html = f"""
            <div style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
                <h2 style="color: #52247d;">InzurAI+</h2>
                <p>Hola,</p>
                <p>Se ha solicitado compartir la información de la tabla contigo en formato <strong>{formato.upper()}</strong>.</p>
                <br>
                <p>Saludos,</p>
                <p><strong>Equipo InzurAI+</strong></p>
            </div>
            """

            datos_correo = {
                "correo": correo_destino,
                "asunto": asunto,
                "html": mensaje_html 
            }

            respuesta = requests.post(url_puente, json=datos_correo)

            if respuesta.status_code == 200:
                return JsonResponse({'status': 'success', 'mensaje': f'Correo enviado exitosamente a {correo_destino}'})
            else:
                return JsonResponse({'status': 'error', 'mensaje': 'El servidor de Google no respondió correctamente.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': f'Error interno: {str(e)}'})
            
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)
def api_eliminar_usuario(request):
    if request.method == 'POST':
        try:
            # Leemos los IDs que vienen del fetch en JavaScript
            data = json.loads(request.body)
            ids = data.get('ids', [])
            
            if not ids:
                return JsonResponse({'status': 'error', 'mensaje': 'No se seleccionaron usuarios.'})
            
            # Borramos todos los usuarios cuyas cédulas estén en la lista
            Usuarios.objects.filter(cedula__in=ids).delete()
            
            return JsonResponse({'status': 'success', 'mensaje': f'{len(ids)} usuario(s) eliminado(s) correctamente.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)})
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'})
def api_actualizar_estados_usuarios(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cambios = data.get('cambios', {}) # Es un diccionario {cedula: estado}
            
            for cedula, nuevo_estado in cambios.items():
                Usuarios.objects.filter(cedula=cedula).update(estatus=nuevo_estado)
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)})
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'})
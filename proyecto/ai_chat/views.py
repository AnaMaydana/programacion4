import json
import os
from decimal import Decimal
from django.db import models
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError

from .models import ChatSession, Message, Categoria, Producto, ConsultaIA
from .inventory_service import InventoryService
from .forms import ProductoForm, AjusteStockForm
from .services.report_strategies import ReporteContext
from .services.ollama_service import AILocalServiceFactory, OllamaLocalService

ROLES_METADATA = [
    {
        'id': 'inventario',
        'name': 'InvenBot (IA Local Supermercado)',
        'desc': 'Asistente oficial para consultas en tiempo real sobre inventario, precios (Bs.) y existencias.',
        'icon': 'InvenBot',
        'placeholder': 'Pregunta sobre precios en Bs., productos agotados, categorías o stock...',
        'templates': [
            '¿Cuál es el producto más caro?',
            '¿Qué productos están agotados?',
            '¿Cuáles tienen pocas existencias?',
            '¿Cuál es el valor total del inventario?',
            '¿Qué productos pertenecen a Lácteos y Huevos?'
        ]
    }
]

def chat(request):
    """
    Vista del chatbot de inventario con soporte de sesiones, exportación y tema claro/oscuro.
    """
    sessions = ChatSession.objects.order_by('-created_at')
    model_name = os.getenv('OLLAMA_MODEL', 'invenbot')
    host_ip = request.get_host().split(':')[0]
    session_id = request.GET.get('session')
    active_session = None
    initial_messages = []
    if session_id:
        active_session = ChatSession.objects.filter(id=session_id).first()
        if active_session:
            initial_messages = list(active_session.message.order_by('timestamp'))
    return render(request, 'chat.html', {
        'sessions': sessions,
        'model_name': model_name,
        'host_ip': host_ip,
        'roles': ROLES_METADATA,
        'roles_json': json.dumps(ROLES_METADATA),
        'active_session': active_session,
        'initial_messages': initial_messages,
    })

@csrf_exempt
def api_send_message(request):
    """
    Endpoint para procesar un mensaje del usuario y obtener la respuesta de la IA 100% local.
    Cumple con el flujo de RF-08 e invoca al modelo local 'invenbot' servido en Ollama.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Utilice POST.'}, status=405)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            prompt = data.get('message', '').strip()
            session_id = data.get('session_id')
        else:
            prompt = request.POST.get('message', '').strip()
            session_id = request.POST.get('session_id')

        if not prompt:
            return JsonResponse({'error': 'El mensaje no puede estar vacío.'}, status=400)

        if session_id in ['', 'null', 'None']:
            session_id = None
        elif session_id is not None:
            session_id = int(session_id)

        # Obtener o crear sesión
        session = None
        if session_id:
            session = ChatSession.objects.filter(id=session_id).first()
        if not session:
            session = ChatSession.objects.create(user='Usuario')
            session_id = session.id

        # Guardar mensaje del usuario
        Message.objects.create(
            session=session,
            sender='Usuario',
            message=prompt
        )

        # Instanciar servicio local mediante Factory Pattern
        ia_service = AILocalServiceFactory.crear_servicio('ollama')
        
        # Procesar con IA local
        resultado_ia = ia_service.consultar(prompt, usuario='Usuario')
        reply = resultado_ia.get('respuesta', '')
        latencia = resultado_ia.get('latencia', 0.5)
        modelo_usado = resultado_ia.get('modelo', 'invenbot')

        # Si Ollama devolvió error de conexión, usamos el servicio estructurado como fallback
        if not resultado_ia.get('exito') and resultado_ia.get('error') == 'OLLAMA_OFFLINE':
            es_inv, _, _, fallback_texto = InventoryService.procesar_consulta(prompt)
            if es_inv:
                reply = f"{fallback_texto}\n\n*(Nota: Respuesta generada desde la base de datos local mientras Ollama inicia).* "

        # Guardar respuesta del bot
        Message.objects.create(
            session=session,
            sender='Asistente',
            message=reply
        )

        return JsonResponse({
            'status': 'ok',
            'reply': reply,
            'session_id': session.id,
            'latency': latencia,
            'model': modelo_usado,
            'role': 'inventario',
        })
    except Exception as e:
        return JsonResponse({'error': f'Error interno en el servidor: {str(e)}'}, status=500)

def api_export_session(request, session_id):
    """
    Endpoint para exportar una conversación en formato TXT, JSON o Markdown.
    """
    session = get_object_or_404(ChatSession, id=session_id)
    messages = session.message.order_by('timestamp')
    fmt = request.GET.get('format', 'txt').lower()

    if fmt == 'json':
        data = {
            'session_id': session.id,
            'title': session.title,
            'created_at': session.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'messages': [
                {
                    'sender': m.sender,
                    'message': m.message,
                    'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                } for m in messages
            ]
        }
        response = HttpResponse(json.dumps(data, indent=2, ensure_ascii=False), content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="conversacion_{session.id}.json"'
        return response

    elif fmt == 'md':
        content = f"# {session.title}\n\n"
        content += f"*Fecha de creación: {session.created_at.strftime('%d/%m/%Y %H:%M')}*\n\n---\n\n"
        for m in messages:
            rol = "**Usuario**" if m.sender in ['Usuario', 'User', 'user'] else "**InvenBot (IA Local)**"
            content += f"### {rol} ({m.timestamp.strftime('%H:%M')})\n\n{m.message}\n\n---\n\n"
        response = HttpResponse(content, content_type='text/markdown; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="conversacion_{session.id}.md"'
        return response

    else:
        content = f"CONVERSACIÓN: {session.title}\n"
        content += f"Fecha: {session.created_at.strftime('%d/%m/%Y %H:%M')}\n"
        content += "=" * 50 + "\n\n"
        for m in messages:
            content += f"[{m.timestamp.strftime('%H:%M')}] {m.sender}:\n{m.message}\n\n"
            content += "-" * 50 + "\n\n"
        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="conversacion_{session.id}.txt"'
        return response

def api_get_sessions(request):
    sessions = ChatSession.objects.order_by('-created_at')
    data = []
    for s in sessions:
        data.append({
            'id': s.id,
            'title': s.title,
            'created_at': s.created_at.strftime('%d/%m/%Y %H:%M'),
        })
    return JsonResponse({'sessions': data})

def api_get_session_messages(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    messages = session.message.order_by('timestamp')
    data = []
    for m in messages:
        data.append({
            'id': m.id,
            'sender': m.sender,
            'message': m.message,
            'timestamp': m.timestamp.strftime('%H:%M'),
        })
    return JsonResponse({
        'session_id': session.id,
        'title': session.title,
        'messages': data
    })

@csrf_exempt
def api_new_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Utilice POST.'}, status=405)
    
    session = ChatSession.objects.create(user='Usuario')
    return JsonResponse({
        'status': 'ok',
        'session_id': session.id,
        'title': f'Conversación #{session.id}',
    })

@csrf_exempt
def api_delete_session(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Utilice POST.'}, status=405)

    session = get_object_or_404(ChatSession, id=session_id)
    session.delete()
    return JsonResponse({'status': 'ok', 'mensaje': 'Conversación eliminada correctamente.'})


# ==============================================================================
# VISTAS DEL SISTEMA DE INVENTARIO (CRUD COMPLETO Y CONTROL DE EXISTENCIAS)
# ==============================================================================

def inventario_vista(request):
    """
    Vista principal del panel de inventario de supermercado con CRUD, reportes y asistente IA.
    """
    categoria_filtro = request.GET.get('categoria', 'todas')
    estado_filtro = request.GET.get('estado', 'todos')
    busqueda = request.GET.get('q', '').strip()

    productos = Producto.objects.select_related('categoria').all()

    if categoria_filtro and categoria_filtro != 'todas':
        productos = productos.filter(categoria__id=categoria_filtro)

    if estado_filtro == 'activos':
        productos = productos.filter(estado=True)
    elif estado_filtro == 'inactivos':
        productos = productos.filter(estado=False)

    if busqueda:
        productos = productos.filter(
            models.Q(nombre__icontains=busqueda) | 
            models.Q(codigo__icontains=busqueda) |
            models.Q(descripcion__icontains=busqueda) |
            models.Q(categoria__nombre__icontains=busqueda)
        )

    categorias = Categoria.objects.all()
    kpis = InventoryService.obtener_resumen_inventario()
    host_ip = request.get_host().split(':')[0]
    model_name = os.getenv('OLLAMA_MODEL', 'invenbot')

    return render(request, 'inventario.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_filtro': categoria_filtro,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
        'kpis': kpis,
        'host_ip': host_ip,
        'model_name': model_name,
    })

def reportes_vista(request):
    """
    Vista de pantalla completa y pestaña dedicada para los 8 Reportes Predefinidos (RF-06).
    Implementa el Patrón de Diseño Strategy con visualización completa, KPIs y exportación.
    """
    host_ip = request.get_host().split(':')[0]
    model_name = os.getenv('OLLAMA_MODEL', 'invenbot')
    kpis = InventoryService.obtener_resumen_inventario()
    categorias = Categoria.objects.all()

    # Reporte inicial por defecto: valor_total
    contexto = ReporteContext(tipo_reporte='valor_total')
    datos_iniciales = contexto.generar()
    resumen_inicial = contexto.generar_texto_resumen(datos_iniciales)

    return render(request, 'reportes.html', {
        'host_ip': host_ip,
        'model_name': model_name,
        'kpis': kpis,
        'categorias': categorias,
        'datos_iniciales': datos_iniciales,
        'resumen_inicial': resumen_inicial,
    })

def api_producto_detalle(request, producto_id):
    """
    Endpoint API para consultar el detalle completo de un producto (Subpunto 1.3 - CRUD: Detalle).
    """
    producto = get_object_or_404(Producto, id=producto_id)
    return JsonResponse({
        'status': 'ok',
        'producto': {
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'categoria': producto.categoria.nombre,
            'categoria_id': producto.categoria.id,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'stock_minimo': producto.stock_minimo,
            'unidad_medida': producto.unidad_medida,
            'estado': producto.estado,
            'estado_stock': producto.estado_stock,
            'fecha_registro': producto.fecha_registro.strftime('%d/%m/%Y %H:%M'),
            'fecha_actualizacion': producto.fecha_actualizacion.strftime('%d/%m/%Y %H:%M'),
            'valor_inventario': round(float(producto.precio * producto.stock), 2)
        }
    })

@csrf_exempt
def api_producto_crear(request):
    """
    Endpoint API para crear un producto en el inventario con validaciones (RF-01).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else dict(request.POST.items())
        if isinstance(data, dict):
            data = dict(data)
            if 'categoria_id' in data and 'categoria' not in data:
                data['categoria'] = data['categoria_id']
        form = ProductoForm(data)
        if not form.is_valid():
            # Extraer el primer error para mostrar mensaje amigable
            errores = [f"{campo}: {', '.join(errs)}" for campo, errs in form.errors.items()]
            return JsonResponse({'error': ' | '.join(errores)}, status=400)

        producto = form.save()
        return JsonResponse({
            'status': 'ok',
            'mensaje': f'Producto "{producto.nombre}" registrado exitosamente.',
            'producto': {
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre,
                'precio': float(producto.precio),
                'stock': producto.stock,
                'stock_minimo': producto.stock_minimo,
                'unidad_medida': producto.unidad_medida,
                'estado': producto.estado,
                'estado_stock': producto.estado_stock
            }
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al registrar producto: {str(e)}'}, status=500)

@csrf_exempt
def api_producto_editar(request, producto_id):
    """
    Endpoint API para actualizar un producto existente con validaciones (RF-03).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        # Validaciones de valores no negativos
        precio_val = data.get('precio')
        if precio_val is not None:
            precio_dec = Decimal(str(precio_val).replace(',', '.'))
            if precio_dec < 0:
                return JsonResponse({'error': 'El precio no puede ser negativo.'}, status=400)
            producto.precio = precio_dec

        stock_val = data.get('stock')
        if stock_val is not None and str(stock_val).strip() != '':
            stock_int = int(stock_val)
            if stock_int < 0:
                return JsonResponse({'error': 'La cantidad existente no puede ser negativa.'}, status=400)
            producto.stock = stock_int

        stock_min_val = data.get('stock_minimo')
        if stock_min_val is not None and str(stock_min_val).strip() != '':
            stock_min_int = int(stock_min_val)
            if stock_min_int < 0:
                return JsonResponse({'error': 'El stock mínimo no puede ser negativo.'}, status=400)
            producto.stock_minimo = stock_min_int

        if 'nombre' in data and str(data['nombre']).strip():
            producto.nombre = str(data['nombre']).strip()
        if 'descripcion' in data:
            producto.descripcion = str(data['descripcion']).strip()
        if 'categoria_id' in data and data['categoria_id']:
            producto.categoria = get_object_or_404(Categoria, id=int(data['categoria_id']))
        if 'unidad_medida' in data and str(data['unidad_medida']).strip():
            producto.unidad_medida = str(data['unidad_medida']).strip()
        if 'estado' in data:
            producto.estado = bool(data['estado'])

        producto.save()
        return JsonResponse({
            'status': 'ok',
            'mensaje': f'Producto "{producto.nombre}" actualizado correctamente.',
            'producto': {
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre,
                'precio': float(producto.precio),
                'stock': producto.stock,
                'stock_minimo': producto.stock_minimo,
                'unidad_medida': producto.unidad_medida,
                'estado': producto.estado,
                'estado_stock': producto.estado_stock
            }
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al editar producto: {str(e)}'}, status=500)

@csrf_exempt
def api_producto_eliminar(request, producto_id):
    """
    Endpoint API para eliminar físicamente un producto del inventario (RF-04).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        nombre = producto.nombre
        producto.delete()
        return JsonResponse({
            'status': 'ok',
            'mensaje': f'El producto "{nombre}" fue eliminado exitosamente.'
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al eliminar producto: {str(e)}'}, status=500)

@csrf_exempt
def api_producto_toggle_estado(request, producto_id):
    """
    Endpoint API para alternar el estado del producto entre Activo e Inactivo (Borrado lógico RF-04).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        producto.estado = not producto.estado
        producto.save()
        estado_txt = "activado" if producto.estado else "desactivado (borrado lógico)"
        return JsonResponse({
            'status': 'ok',
            'mensaje': f'El producto "{producto.nombre}" fue {estado_txt}.',
            'estado': producto.estado
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al cambiar estado del producto: {str(e)}'}, status=500)

@csrf_exempt
def api_producto_ajustar_stock(request, producto_id):
    """
    Endpoint API para aumentar o disminuir la cantidad disponible de un producto (RF-05).
    Impide estrictamente que la cantidad disponible resulte negativa.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        accion = data.get('accion', 'aumentar') # 'aumentar' o 'disminuir'
        delta = int(data.get('delta', 1))

        if delta <= 0:
            return JsonResponse({'error': 'La cantidad de ajuste debe ser un entero positivo.'}, status=400)

        if accion == 'aumentar':
            producto.stock += delta
        elif accion == 'disminuir':
            if producto.stock - delta < 0:
                return JsonResponse({'error': f'No es posible disminuir {delta} unidades. El stock actual es {producto.stock} y no puede ser negativo.'}, status=400)
            producto.stock -= delta
        else:
            return JsonResponse({'error': 'Acción no reconocida. Use "aumentar" o "disminuir".'}, status=400)

        producto.save()
        return JsonResponse({
            'status': 'ok',
            'mensaje': f'Stock de "{producto.nombre}" actualizado a {producto.stock} {producto.unidad_medida}.',
            'nuevo_stock': producto.stock,
            'estado_stock': producto.estado_stock
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al ajustar stock: {str(e)}'}, status=500)


# ==============================================================================
# REPORTES PREDEFINIDOS CON PATRÓN STRATEGY Y EXPLICACIÓN CON IA LOCAL (RF-06)
# ==============================================================================

def api_reportes(request):
    """
    Endpoint para generar los 8 reportes predefinidos utilizando el Patrón STRATEGY (RF-06).
    Opcionalmente envía los resultados a Ollama para generar una explicación en lenguaje natural.
    """
    tipo_reporte = request.GET.get('tipo', 'valor_total')
    explicar_con_ia = request.GET.get('explicar', '0') in ['1', 'true', 'True']
    categoria_id = request.GET.get('categoria_id')

    try:
        contexto = ReporteContext(tipo_reporte=tipo_reporte)
        datos = contexto.generar(categoria_id=categoria_id)
        resumen_texto = contexto.generar_texto_resumen(datos)

        explicacion_ia = None
        if explicar_con_ia:
            ia_service = AILocalServiceFactory.crear_servicio('ollama')
            explicacion_ia = ia_service.explicar_reporte(datos.get('titulo', 'Reporte'), resumen_texto)

        return JsonResponse({
            'status': 'ok',
            'tipo': tipo_reporte,
            'datos': datos,
            'resumen_texto': resumen_texto,
            'explicacion_ia': explicacion_ia
        })
    except Exception as e:
        return JsonResponse({'error': f'Error al generar reporte: {str(e)}'}, status=500)

def api_inventario_kpis(request):
    """
    Endpoint para obtener métricas y KPIs en tiempo real del inventario.
    """
    kpis = InventoryService.obtener_resumen_inventario()
    return JsonResponse(kpis)

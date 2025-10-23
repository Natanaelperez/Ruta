from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Ruta, DetalleRuta
from apps.destinos.models import Destino
from apps.servicios.models import Servicio
import json
import os
from django.conf import settings

@login_required
def crear_ruta(request):
    """
    Vista para consultar y planificar rutas (solo lectura)
    """
    # Verificar permisos: permitir administradores, proveedores y turistas
    if not request.user.rol or request.user.rol.nombre not in ['administrador', 'proveedor', 'turista']:
        messages.error(request, 'No tienes permisos para acceder a esta vista')
        return redirect('rutas:lista_rutas')
    
    # GET request
    destinos = Destino.objects.filter(activo=True).order_by('nombre')
    
    # Preparar datos JSON para JavaScript
    destinos_json = json.dumps([{
        'id': d.id,
        'nombre': d.nombre,
        'latitud': float(d.latitud),
        'longitud': float(d.longitud),
        'provincia': d.provincia,
        'ciudad': d.ciudad if d.ciudad else d.provincia,
        'region': d.region,
        'region_display': d.get_region_display(),
        'precio_promedio_minimo': float(d.precio_promedio_minimo),
        'precio_promedio_maximo': float(d.precio_promedio_maximo)
    } for d in destinos])
    
    # ← CORREGIDO + DEBUG: Cargar servicios de transporte desde DB
    servicios_qs = Servicio.objects.filter(
        tipo=Servicio.TRANSPORTE,
        activo=True,
        disponible=True
    ).select_related('destino').values(
        'nombre', 'precio', 'destino__nombre', 'destino__ciudad'  # Asegura todos los campos
    ).order_by('destino__nombre')

    transporte_services = [
        {
            'nombre': item['nombre'],
            'precio': float(item['precio']),
            'destino__nombre': item.get('destino__nombre', ''),  # ← SAFE: Si no existe, vacío
            'destino__ciudad': item['destino__ciudad']
        }
        for item in servicios_qs
    ]

    transporte_services_json = json.dumps(transporte_services)
    
    # Cargar datos de transporte (estructura de puntos/rutas, sin precios)
    transporte_json_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'transporte_ecuador.json')
    try:
        with open(transporte_json_path, 'r', encoding='utf-8') as f:
            transporte_data = json.load(f)
            # ← CAMBIO: No usamos precios del JSON, solo estructura
            # Si quieres remover precios del JSON, edítalo manualmente
            transporte_json = json.dumps(transporte_data)
    except FileNotFoundError:
        transporte_json = json.dumps({})
        messages.warning(request, 'No se encontró el archivo de datos de transporte')
    
    context = {
        'destinos': destinos,
        'destinos_json': destinos_json,
        'transporte_json': transporte_json,
        # ← NUEVO: Pasar servicios de DB a JS
        'transporte_services_json': transporte_services_json,
        'titulo': 'Planificador de Rutas'
    }
    
    return render(request, 'rutas/crear_ruta.html', context)
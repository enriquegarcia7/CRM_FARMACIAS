#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartPharm.settings')
django.setup()

from core.models import OfertaLaboratorio
from django.db.models import Count

# Obtener todas las ofertas
ofertas = OfertaLaboratorio.objects.all().select_related('producto_catalogo__proveedor', 'laboratorio')

print('=== ANÁLISIS DE OFERTAS EN BASE DE DATOS ===\n')
print(f'Total ofertas: {ofertas.count()}\n')

# Mostrar primeras 20 ofertas con sus detalles
print('=== PRIMERAS 20 OFERTAS ===')
for oferta in ofertas[:20]:
    producto = oferta.producto_catalogo
    if producto:
        print(f'\nProducto: {producto.nombre[:50]}')
        print(f'Código: {producto.codigo}')
        print(f'Proveedor: {producto.proveedor.nombre if producto.proveedor else "N/A"}')
        print(f'Laboratorio: {oferta.laboratorio.nombre if oferta.laboratorio else "N/A"}')
        print(f'Precio Normal: ${oferta.precio_normal}')
        print(f'Precio Oferta: ${oferta.precio_oferta}')
        print(f'Descuento: {oferta.descuento}%')
        print('-' * 80)

# Estadísticas de descuentos
print('\n=== ESTADÍSTICAS DE DESCUENTOS ===')
total = ofertas.count()
sin_descuento = ofertas.filter(descuento=0).count()
con_descuento = ofertas.filter(descuento__gt=0).count()

print(f'Ofertas SIN descuento (0%): {sin_descuento} ({sin_descuento*100/total if total > 0 else 0:.1f}%)')
print(f'Ofertas CON descuento (>0%): {con_descuento} ({con_descuento*100/total if total > 0 else 0:.1f}%)')

# Mostrar ofertas con descuento
if con_descuento > 0:
    print(f'\n=== OFERTAS CON DESCUENTO (primeras 10) ===')
    for oferta in ofertas.filter(descuento__gt=0)[:10]:
        producto = oferta.producto_catalogo
        if producto:
            print(f'{producto.nombre[:40]} | Desc: {oferta.descuento}% | Normal: ${oferta.precio_normal} | Oferta: ${oferta.precio_oferta}')

# Verificar códigos de barras vs códigos normales
print('\n=== ANÁLISIS DE CÓDIGOS (primeras 15) ===')
for oferta in ofertas[:15]:
    producto = oferta.producto_catalogo
    if producto:
        prov_nombre = producto.proveedor.nombre if producto.proveedor else "N/A"
        print(f'{prov_nombre}: {producto.codigo} (len={len(str(producto.codigo))}) - {producto.nombre[:40]}')

# Agrupar por proveedor
print('\n=== OFERTAS POR PROVEEDOR ===')
proveedores = OfertaLaboratorio.objects.filter(producto_catalogo__proveedor__isnull=False).values('producto_catalogo__proveedor__nombre').annotate(total=Count('id'))
for prov in proveedores:
    print(f"{prov['producto_catalogo__proveedor__nombre']}: {prov['total']} ofertas")

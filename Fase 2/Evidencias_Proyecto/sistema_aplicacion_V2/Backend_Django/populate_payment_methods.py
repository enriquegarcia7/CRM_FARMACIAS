#!/usr/bin/env python
"""
Script para poblar datos iniciales de MetodoPago y EstadoVenta
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartPharm.settings')
django.setup()

from core.models import MetodoPago, EstadoVenta, Proveedor

def poblar_metodos_pago():
    """Crear métodos de pago iniciales"""
    metodos = [
        {'codigo': 'efectivo', 'nombre': 'Efectivo', 'orden': 1, 'descripcion': 'Pago en efectivo'},
        {'codigo': 'tarjeta', 'nombre': 'Tarjeta de Crédito/Débito', 'orden': 2, 'descripcion': 'Pago con tarjeta'},
        {'codigo': 'transferencia', 'nombre': 'Transferencia Bancaria', 'orden': 3, 'descripcion': 'Transferencia electrónica'},
    ]

    for metodo_data in metodos:
        metodo, created = MetodoPago.objects.get_or_create(
            codigo=metodo_data['codigo'],
            defaults={
                'nombre': metodo_data['nombre'],
                'orden': metodo_data['orden'],
                'descripcion': metodo_data.get('descripcion', ''),
                'activo': True
            }
        )
        if created:
            print(f"✅ Método de pago creado: {metodo.nombre}")
        else:
            print(f"ℹ️  Método de pago ya existe: {metodo.nombre}")


def poblar_estados_venta():
    """Crear estados de venta iniciales"""
    estados = [
        {'codigo': 'completada', 'nombre': 'Completada', 'orden': 1, 'color': 'green', 'es_final': True, 'descripcion': 'Venta completada exitosamente'},
        {'codigo': 'pendiente', 'nombre': 'Pendiente', 'orden': 2, 'color': 'yellow', 'es_final': False, 'descripcion': 'Venta pendiente de pago'},
        {'codigo': 'cancelada', 'nombre': 'Cancelada', 'orden': 3, 'color': 'red', 'es_final': True, 'descripcion': 'Venta cancelada'},
    ]

    for estado_data in estados:
        estado, created = EstadoVenta.objects.get_or_create(
            codigo=estado_data['codigo'],
            defaults={
                'nombre': estado_data['nombre'],
                'orden': estado_data['orden'],
                'color': estado_data.get('color', ''),
                'es_final': estado_data.get('es_final', False),
                'descripcion': estado_data.get('descripcion', ''),
                'activo': True
            }
        )
        if created:
            print(f"✅ Estado de venta creado: {estado.nombre}")
        else:
            print(f"ℹ️  Estado de venta ya existe: {estado.nombre}")


def configurar_proveedores():
    """Configurar montos mínimos y preferencias para proveedores existentes"""
    configuraciones = {
        'MEDIVEN': {'monto_minimo': 50000, 'es_preferente': True},
        'SOCOFAR': {'monto_minimo': 100000, 'es_preferente': False},
    }

    for nombre_prov, config in configuraciones.items():
        try:
            proveedor = Proveedor.objects.get(nombre__iexact=nombre_prov)
            proveedor.monto_minimo_pedido = config['monto_minimo']
            proveedor.es_preferente = config['es_preferente']
            proveedor.save()
            print(f"✅ Proveedor configurado: {proveedor.nombre} - Mínimo: ${config['monto_minimo']:,} - Preferente: {config['es_preferente']}")
        except Proveedor.DoesNotExist:
            print(f"⚠️  Proveedor {nombre_prov} no encontrado")


if __name__ == '__main__':
    print("=" * 60)
    print("POBLAR DATOS INICIALES - MetodoPago y EstadoVenta")
    print("=" * 60)

    print("\n📋 Creando métodos de pago...")
    poblar_metodos_pago()

    print("\n📊 Creando estados de venta...")
    poblar_estados_venta()

    print("\n🏢 Configurando proveedores...")
    configurar_proveedores()

    print("\n" + "=" * 60)
    print("✅ PROCESO COMPLETADO")
    print("=" * 60)

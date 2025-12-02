"""
Comando para limpiar datos incorrectos de Provefarma cargados antes de las correcciones.

Este comando elimina:
1. Proveedores con nombres que parecen archivos (contienen "Catalogo", "Oferta", etc.)
2. Productos con nombres que parecen headers de categoría (ej: "BIENESTAR OCTUBRE 2025")
3. Ofertas asociadas a estos registros incorrectos

Uso:
    python manage.py cleanup_bad_provefarma --dry-run  # Ver qué se eliminaría
    python manage.py cleanup_bad_provefarma            # Ejecutar limpieza
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Proveedor, ProductoCatalogo, OfertaLaboratorio, Laboratorio
import re


class Command(BaseCommand):
    help = 'Limpia datos incorrectos de Provefarma de la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminaría sin hacer cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== MODO DRY-RUN: No se harán cambios ===\n'))
        else:
            self.stdout.write(self.style.WARNING('=== LIMPIANDO DATOS INCORRECTOS ===\n'))

        # 1. Buscar proveedores con nombres que parecen archivos
        self.stdout.write('\n📋 Buscando proveedores incorrectos...')
        bad_proveedor_patterns = [
            r'[Cc]atalogo.*[Oo]ferta',
            r'[Ll]ista.*[Pp]recio',
            r'\.(xlsx?|csv|pdf)',  # Extensiones de archivo
            r'[Oo]ctubre\s+\d{4}',  # Patrones de fecha en nombre
            r'[Nn]oviembre\s+\d{4}',
            r'[Dd]iciembre\s+\d{4}',
        ]

        bad_proveedores = []
        for proveedor in Proveedor.objects.all():
            for pattern in bad_proveedor_patterns:
                if re.search(pattern, proveedor.nombre):
                    bad_proveedores.append(proveedor)
                    break

        self.stdout.write(f'  Encontrados: {len(bad_proveedores)} proveedores incorrectos')
        for prov in bad_proveedores:
            self.stdout.write(f'    - {prov.nombre}')

        # 2. Buscar productos con nombres que parecen headers de categoría
        self.stdout.write('\n📋 Buscando productos incorrectos (headers de categoría)...')
        bad_producto_patterns = [
            r'^[A-Z\s]+\d{4}$',  # Todo mayúsculas + año
            r'^[A-Z\s]+(OCTUBRE|NOVIEMBRE|DICIEMBRE)\s+\d{4}$',  # Categoría + mes + año
        ]

        bad_productos = []
        for producto in ProductoCatalogo.objects.all():
            for pattern in bad_producto_patterns:
                if re.search(pattern, producto.nombre):
                    bad_productos.append(producto)
                    break

        self.stdout.write(f'  Encontrados: {len(bad_productos)} productos incorrectos')
        for prod in bad_productos[:10]:  # Mostrar solo los primeros 10
            self.stdout.write(f'    - {prod.nombre}')
        if len(bad_productos) > 10:
            self.stdout.write(f'    ... y {len(bad_productos) - 10} más')

        # 3. Contar ofertas que serán eliminadas
        ofertas_from_bad_prov = OfertaLaboratorio.objects.filter(
            producto_catalogo__proveedor__in=bad_proveedores
        ).count()

        ofertas_from_bad_prod = OfertaLaboratorio.objects.filter(
            producto_catalogo__in=bad_productos
        ).count()

        total_ofertas_to_delete = ofertas_from_bad_prov + ofertas_from_bad_prod

        self.stdout.write(f'\n📊 Resumen de eliminación:')
        self.stdout.write(f'  - Proveedores incorrectos: {len(bad_proveedores)}')
        self.stdout.write(f'  - Productos incorrectos: {len(bad_productos)}')
        self.stdout.write(f'  - Ofertas a eliminar: {total_ofertas_to_delete}')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('\n✓ DRY-RUN completado. No se hicieron cambios.'))
            self.stdout.write('Para ejecutar la limpieza, ejecuta sin --dry-run')
            return

        # Confirmar antes de eliminar
        self.stdout.write(self.style.WARNING('\n⚠️  ¿Estás seguro de eliminar estos registros?'))
        confirm = input('Escribe "SI" para confirmar: ')

        if confirm != 'SI':
            self.stdout.write(self.style.ERROR('❌ Operación cancelada'))
            return

        # Ejecutar eliminación en transacción atómica
        with transaction.atomic():
            # Eliminar ofertas asociadas a productos incorrectos
            deleted_ofertas_prod = OfertaLaboratorio.objects.filter(
                producto_catalogo__in=bad_productos
            ).delete()

            # Eliminar ofertas asociadas a proveedores incorrectos
            deleted_ofertas_prov = OfertaLaboratorio.objects.filter(
                producto_catalogo__proveedor__in=bad_proveedores
            ).delete()

            # Eliminar productos incorrectos
            deleted_productos = ProductoCatalogo.objects.filter(
                id__in=[p.id for p in bad_productos]
            ).delete()

            # Eliminar proveedores incorrectos (esto también eliminará en cascada)
            deleted_proveedores = Proveedor.objects.filter(
                id__in=[p.id for p in bad_proveedores]
            ).delete()

        self.stdout.write(self.style.SUCCESS('\n✅ Limpieza completada:'))
        self.stdout.write(f'  - Ofertas eliminadas: {deleted_ofertas_prod[0] + deleted_ofertas_prov[0]}')
        self.stdout.write(f'  - Productos eliminados: {deleted_productos[0]}')
        self.stdout.write(f'  - Proveedores eliminados: {deleted_proveedores[0]}')
        self.stdout.write(self.style.SUCCESS('\n🎉 Base de datos limpia!'))
        self.stdout.write('Ahora puedes ejecutar el ETL para recargar los datos corregidos.')

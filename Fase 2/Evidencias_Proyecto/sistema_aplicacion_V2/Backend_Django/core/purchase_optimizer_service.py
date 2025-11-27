# core/purchase_optimizer_service.py
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from .models import (
    Producto, ProductoCatalogo, ProductoProveedorMapping,
    OfertaLaboratorio, SugerenciaCompra, Proveedor
)
from .stock_service import stock_service
from .mapping_service import mapping_service


class PurchaseOptimizerService:
    """
    Servicio de optimización de compras.

    Funcionalidades:
    1. Genera sugerencias desde productos críticos
    2. Encuentra mejor proveedor por producto (precio + ofertas)
    3. Valida mínimos de pedido por proveedor
    4. Redistribuye productos si no cumplen mínimos
    """

    def __init__(self):
        # Mínimos de pedido por proveedor (en pesos chilenos)
        self.MINIMOS_PROVEEDOR = {
            'MEDIVEN': Decimal('50000'),
            'SOCOFAR': Decimal('100000'),
        }

        # Proveedor preferente (cuando hay empate de precios)
        self.PROVEEDOR_PREFERENTE = 'MEDIVEN'  # Configurable

    def generar_sugerencias_desde_criticos(self, limite=100, forzar_mapeo=True):
        """
        Genera sugerencias de compra desde productos críticos.

        Args:
            limite: Número máximo de productos críticos a procesar
            forzar_mapeo: Si True, intenta mapear productos sin mapping

        Returns:
            dict con estadísticas del proceso
        """
        # Limpiar sugerencias antiguas no procesadas (más de 7 días)
        fecha_limite = timezone.now() - timezone.timedelta(days=7)
        SugerenciaCompra.objects.filter(
            procesada=False,
            fecha_creacion__lt=fecha_limite
        ).delete()

        # Obtener productos críticos
        productos_criticos = self._get_productos_criticos(limite)

        stats = {
            'total_criticos': len(productos_criticos),
            'sugerencias_creadas': 0,
            'productos_sin_mapeo': 0,
            'productos_sin_proveedor': 0,
            'errores': []
        }

        for producto_info in productos_criticos:
            try:
                # Verificar si ya existe sugerencia no procesada
                if SugerenciaCompra.objects.filter(
                    producto=producto_info['producto'],
                    procesada=False
                ).exists():
                    continue  # Ya tiene sugerencia pendiente

                # Buscar mappings activos
                mappings = ProductoProveedorMapping.objects.filter(
                    producto_interno=producto_info['producto'],
                    activo=True
                ).select_related('proveedor')

                # Si no tiene mappings y forzar_mapeo=True, intentar mapeo automático
                if not mappings.exists() and forzar_mapeo:
                    print(f"🔍 Mapeando automáticamente: {producto_info['codigo']}")
                    mapping_service.auto_map_product(
                        producto_info['producto'],
                        min_confidence=70,
                        auto_create=True
                    )
                    # Recargar mappings
                    mappings = ProductoProveedorMapping.objects.filter(
                        producto_interno=producto_info['producto'],
                        activo=True
                    ).select_related('proveedor')

                if not mappings.exists():
                    stats['productos_sin_mapeo'] += 1
                    print(f"⚠️ Sin mapping: {producto_info['codigo']}")
                    continue

                # Encontrar mejor proveedor
                mejor_opcion = self._encontrar_mejor_proveedor(
                    producto_info['producto'],
                    mappings,
                    producto_info['cantidad_sugerida']
                )

                if not mejor_opcion:
                    stats['productos_sin_proveedor'] += 1
                    print(f"⚠️ Sin proveedor disponible: {producto_info['codigo']}")
                    continue

                # Crear sugerencia de compra
                sugerencia = SugerenciaCompra.objects.create(
                    producto=producto_info['producto'],
                    tipo='bajo_stock',
                    cantidad_sugerida=producto_info['cantidad_sugerida'],
                    prioridad=self._mapear_prioridad(producto_info['nivel_riesgo']),
                    razon=f"{producto_info['razon']}. Cobertura: {producto_info['dias_cobertura']} días.",
                    fuente_datos=producto_info['fuente_datos'],
                    proveedor_recomendado=mejor_opcion['proveedor'],
                    codigo_proveedor=mejor_opcion['codigo_proveedor'],
                    precio_unitario=mejor_opcion['precio_final'],
                    tiene_oferta=mejor_opcion['tiene_oferta'],
                    precio_oferta=mejor_opcion['precio_oferta'] if mejor_opcion['tiene_oferta'] else None,
                    descuento_porcentaje=mejor_opcion['descuento'] if mejor_opcion['tiene_oferta'] else Decimal('0'),
                    dias_cobertura=producto_info['dias_cobertura'],
                    procesada=False,
                    incluida_en_orden=False
                )

                stats['sugerencias_creadas'] += 1
                print(f"✅ Sugerencia creada: {producto_info['codigo']} → {mejor_opcion['proveedor'].nombre} (${mejor_opcion['precio_final']})")

            except Exception as e:
                stats['errores'].append({
                    'producto': producto_info['codigo'],
                    'error': str(e)
                })
                print(f"❌ Error procesando {producto_info['codigo']}: {str(e)}")

        return stats

    def _get_productos_criticos(self, limite):
        """Obtiene productos críticos con su información de stock"""
        productos = Producto.objects.filter(activo=True).select_related(
            'proveedor_principal', 'categoria'
        )[:min(limite * 3, 1000)]

        criticos = []

        for producto in productos:
            try:
                metricas = stock_service.obtener_metricas_producto(producto)
                nivel_riesgo = metricas.get('nivel_riesgo', '')

                # Solo productos críticos o de alto riesgo
                if nivel_riesgo not in ['critico', 'alto', 'sin_datos_stock_critico']:
                    continue

                stock_calc = stock_service.calcular_stock_minimo(producto)
                cantidad_sugerida = max(0, stock_calc - producto.stock_actual)

                if cantidad_sugerida == 0:
                    continue  # No necesita reposición

                dias_cob = metricas.get('dias_cobertura')

                criticos.append({
                    'producto': producto,
                    'codigo': producto.codigo,
                    'cantidad_sugerida': cantidad_sugerida,
                    'nivel_riesgo': nivel_riesgo,
                    'dias_cobertura': round(dias_cob, 1) if dias_cob is not None else None,
                    'fuente_datos': metricas.get('fuente_datos', 'desconocido'),
                    'razon': f"Stock crítico. Actual: {producto.stock_actual}, Mínimo: {stock_calc}"
                })

                if len(criticos) >= limite:
                    break

            except Exception as e:
                print(f"Error obteniendo métricas para {producto.codigo}: {str(e)}")
                continue

        # Ordenar por criticidad
        criticos.sort(key=lambda x: (
            0 if x['dias_cobertura'] is not None else 1,
            x['dias_cobertura'] if x['dias_cobertura'] is not None else 999
        ))

        return criticos

    def _encontrar_mejor_proveedor(self, producto, mappings, cantidad):
        """
        Encuentra el mejor proveedor para un producto.

        Criterio de selección:
        1. Precio más bajo (considerando ofertas)
        2. Si hay empate, preferir proveedor preferente
        3. Verificar disponibilidad en catálogo
        """
        opciones = []

        for mapping in mappings:
            try:
                # Buscar producto en catálogo
                prod_catalogo = ProductoCatalogo.objects.filter(
                    codigo=mapping.codigo_proveedor,
                    proveedor=mapping.proveedor,
                    activo=True
                ).first()

                if not prod_catalogo:
                    continue

                # Buscar ofertas activas
                hoy = timezone.now().date()
                oferta = OfertaLaboratorio.objects.filter(
                    producto_catalogo=prod_catalogo,
                    activa=True,
                    fecha_inicio__lte=hoy,
                    fecha_fin__gte=hoy
                ).order_by('precio_oferta').first()

                if oferta:
                    # Tiene oferta
                    precio_final = oferta.precio_oferta
                    tiene_oferta = True
                    precio_oferta = oferta.precio_oferta
                    descuento = oferta.descuento
                else:
                    # Sin oferta - usar precio del producto interno
                    precio_final = producto.precio_costo
                    tiene_oferta = False
                    precio_oferta = None
                    descuento = Decimal('0')

                opciones.append({
                    'proveedor': mapping.proveedor,
                    'codigo_proveedor': mapping.codigo_proveedor,
                    'precio_final': precio_final,
                    'tiene_oferta': tiene_oferta,
                    'precio_oferta': precio_oferta,
                    'descuento': descuento,
                    'confianza_mapeo': mapping.confianza,
                    'es_preferente': mapping.proveedor.nombre.upper() == self.PROVEEDOR_PREFERENTE
                })

            except Exception as e:
                print(f"Error evaluando mapping {mapping.id}: {str(e)}")
                continue

        if not opciones:
            return None

        # Ordenar por: precio (asc), proveedor preferente (desc), confianza (desc)
        opciones.sort(key=lambda x: (
            float(x['precio_final']),
            not x['es_preferente'],
            -float(x['confianza_mapeo'])
        ))

        return opciones[0]

    def _mapear_prioridad(self, nivel_riesgo):
        """Mapea nivel de riesgo a prioridad de sugerencia"""
        mapeo = {
            'critico': 'critica',
            'alto': 'alta',
            'medio': 'media',
            'bajo': 'baja',
            'sin_datos_stock_critico': 'alta',
            'sin_datos_stock_bajo': 'media',
            'sin_movimiento': 'baja'
        }
        return mapeo.get(nivel_riesgo, 'media')

    def consolidar_por_proveedor(self, incluir_solo_activas=True):
        """
        Consolida sugerencias de compra por proveedor.

        Valida mínimos de pedido y redistribuye si es necesario.

        Returns:
            dict: {
                'proveedor_nombre': {
                    'sugerencias': [list],
                    'total': Decimal,
                    'cumple_minimo': bool,
                    'minimo_requerido': Decimal
                }
            }
        """
        # Obtener sugerencias
        query = SugerenciaCompra.objects.filter(procesada=False)
        if incluir_solo_activas:
            query = query.filter(incluida_en_orden=False)

        sugerencias = query.select_related(
            'producto', 'proveedor_recomendado'
        ).order_by('proveedor_recomendado__nombre', '-prioridad')

        # Agrupar por proveedor
        por_proveedor = {}

        for sug in sugerencias:
            if not sug.proveedor_recomendado:
                continue

            prov_nombre = sug.proveedor_recomendado.nombre.upper()

            if prov_nombre not in por_proveedor:
                por_proveedor[prov_nombre] = {
                    'proveedor': sug.proveedor_recomendado,
                    'sugerencias': [],
                    'total': Decimal('0'),
                    'minimo_requerido': self.MINIMOS_PROVEEDOR.get(prov_nombre, Decimal('0')),
                    'cumple_minimo': False
                }

            por_proveedor[prov_nombre]['sugerencias'].append(sug)
            por_proveedor[prov_nombre]['total'] += Decimal(str(sug.total))

        # Validar mínimos
        for prov_nombre, data in por_proveedor.items():
            data['cumple_minimo'] = data['total'] >= data['minimo_requerido']

        return por_proveedor

    def optimizar_ordenes(self):
        """
        Optimiza órdenes para cumplir mínimos de pedido.

        Si un proveedor no cumple el mínimo, redistribuye productos al otro.
        """
        consolidado = self.consolidar_por_proveedor()

        # Identificar proveedores que no cumplen mínimo
        no_cumplen = {
            k: v for k, v in consolidado.items()
            if not v['cumple_minimo'] and v['total'] > 0
        }

        if not no_cumplen:
            return {
                'optimizado': False,
                'mensaje': 'Todos los proveedores cumplen mínimos',
                'consolidado': consolidado
            }

        # Redistribuir productos
        # Por ahora, simple: si MEDIVEN no cumple mínimo, pasar todo a SOCOFAR
        # TODO: Implementar algoritmo más sofisticado

        return {
            'optimizado': True,
            'mensaje': f'{len(no_cumplen)} proveedores no cumplen mínimo',
            'no_cumplen': list(no_cumplen.keys()),
            'consolidado': consolidado
        }


# Instancia global
purchase_optimizer = PurchaseOptimizerService()

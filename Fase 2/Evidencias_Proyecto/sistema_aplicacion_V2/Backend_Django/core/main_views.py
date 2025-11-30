from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Sum, Q, F, Max
from django.db.models.functions import TruncMonth, TruncDate, Coalesce
from django.utils import timezone
from datetime import timedelta
from .models import (
    Cliente, Transaccion, Producto, Proveedor,
    OfertaLaboratorio, SugerenciaCompra, Venta, DetalleVenta
)
from .serializers import (
    ClienteSerializer, TransaccionSerializer, ProductoSerializer,
    ProveedorSerializer, OfertaLaboratorioSerializer,
    OfertaLaboratorioDetalladaSerializer,
    SugerenciaCompraSerializer, VentaSerializer
)


class OfertasPagination(PageNumberPagination):
    """Paginación optimizada para ofertas - 50 items por página"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    pagination_class = OfertasPagination  # 50 clientes por página
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'rut', 'correo', 'telefono']
    ordering_fields = ['nombre', 'rut', 'correo', 'total_compras', 'monto_total', 'ultima_compra']
    ordering = ['nombre']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Anotar campos calculados para permitir ordenamiento
        from django.db.models import Value
        from django.db.models.functions import Coalesce
        from decimal import Decimal

        queryset = queryset.annotate(
            total_compras=Count('ventas', filter=Q(ventas__estado='completada')),
            monto_total=Coalesce(Sum('ventas__total', filter=Q(ventas__estado='completada')), Value(Decimal('0'))),
            ultima_compra=Max('ventas__fecha', filter=Q(ventas__estado='completada'))
        )

        # Búsqueda personalizada con normalización de RUT
        search = self.request.query_params.get('search', '')
        if search:
            search_normalized = search.replace('.', '').replace('-', '').strip()
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(rut__icontains=search_normalized) |
                Q(correo__icontains=search)
            )

        # Filtro por tipo de cliente
        tipo = self.request.query_params.get('tipo', '')
        if tipo == 'frecuentes':
            queryset = queryset.filter(total_compras__gte=5)
        elif tipo == 'normales':
            queryset = queryset.filter(total_compras__lt=5)

        return queryset

    def list(self, request, *args, **kwargs):
        if request.query_params.get('search'):
            self.filter_backends = [filters.OrderingFilter]
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def frecuentes(self, request):
        """Obtiene clientes frecuentes (con 5 o más compras)"""
        clientes = Cliente.objects.annotate(
            total_ventas=Count('ventas', filter=Q(ventas__estado='completada'))
        ).filter(total_ventas__gte=5)

        serializer = self.get_serializer(clientes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtiene estadísticas globales de clientes"""
        total_clientes = Cliente.objects.count()

        # Anotar todos los clientes con su total de compras
        clientes_anotados = Cliente.objects.annotate(
            total_compras=Count('ventas', filter=Q(ventas__estado='completada'))
        )

        # Clientes frecuentes (>= 5 compras)
        clientes_frecuentes = clientes_anotados.filter(total_compras__gte=5).count()

        # Clientes normales (< 5 compras)
        clientes_normales = clientes_anotados.filter(total_compras__lt=5).count()

        # Elegibles para ofertas (frecuentes con >= 5 compras)
        elegibles_ofertas = clientes_anotados.filter(total_compras__gte=5).count()

        return Response({
            'total_clientes': total_clientes,
            'clientes_frecuentes': clientes_frecuentes,
            'clientes_normales': clientes_normales,
            'elegibles_ofertas': elegibles_ofertas
        })


class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de transacciones"""
        total = Transaccion.objects.count()
        return Response({'total': total})


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('proveedor_principal', 'categoria').all()
    serializer_class = ProductoSerializer
    pagination_class = OfertasPagination  # 50 productos por página
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['codigo', 'nombre', 'descripcion', 'stock_actual', 'stock_minimo', 'precio_venta']
    ordering = ['codigo']

    def get_queryset(self):
        """Query optimizado con filtros"""
        queryset = super().get_queryset()

        # FILTRO PRINCIPAL: Solo productos activos
        queryset = queryset.filter(activo=True)

        # Filtro de búsqueda
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search) |
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(categoria__nombre__icontains=search)
            )

        # Filtro de stock
        filtro_stock = self.request.query_params.get('filtro_stock', None)
        if filtro_stock == 'bajo':
            queryset = queryset.filter(stock_actual__lt=F('stock_minimo'))
        elif filtro_stock == 'normal':
            queryset = queryset.filter(stock_actual__gte=F('stock_minimo'))

        return queryset

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Productos con stock bajo"""
        productos = Producto.objects.filter(
            stock_actual__lt=F('stock_minimo')
        )
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top_selling(self, request):
        """Top productos más vendidos"""
        limit = int(request.query_params.get('limit', 10))

        # Obtener top productos desde DetalleVenta
        top_productos = DetalleVenta.objects.values('producto__codigo', 'producto__descripcion').annotate(
            total_vendido=Sum('cantidad'),
            total_ventas=Sum('subtotal')
        ).order_by('-total_vendido')[:limit]

        return Response(top_productos)

    @action(detail=False, methods=['get'])
    def criticos(self, request):
        """
        Productos críticos ordenados por prioridad de reposición.

        Retorna productos con nivel de riesgo crítico o alto, ordenados por:
        1. Días de cobertura (menor a mayor) - los que se agotan primero
        2. Sin datos pero con stock crítico

        Query params:
            - limit: Número máximo de productos (default: 100)
        """
        from .stock_service import stock_service

        limit = int(request.query_params.get('limit', 100))

        # Obtener productos activos
        productos = Producto.objects.filter(activo=True).select_related(
            'proveedor_principal', 'categoria'
        )[:min(limit * 3, 1000)]  # Procesar más para filtrar después

        criticos = []

        for producto in productos:
            try:
                # Obtener métricas del producto
                metricas = stock_service.obtener_metricas_producto(producto)
                nivel_riesgo = metricas.get('nivel_riesgo', 'desconocido')

                # Filtrar solo productos críticos o de alto riesgo
                if nivel_riesgo in ['critico', 'alto', 'sin_datos_stock_critico']:
                    stock_calc = stock_service.calcular_stock_minimo(producto)
                    dias_cob = metricas.get('dias_cobertura')

                    # Calcular cantidad sugerida para reposición
                    cantidad_sugerida = max(0, stock_calc - producto.stock_actual)

                    criticos.append({
                        'id': producto.id,
                        'codigo': producto.codigo,
                        'nombre': producto.nombre,
                        'descripcion': producto.descripcion,
                        'stock_actual': producto.stock_actual,
                        'stock_minimo_calculado': stock_calc,
                        'cantidad_sugerida': cantidad_sugerida,
                        'dias_cobertura': round(dias_cob, 1) if dias_cob is not None else None,
                        'nivel_riesgo': nivel_riesgo,
                        'demanda_promedio_diaria': metricas.get('demanda_promedio_diaria', 0),
                        'fuente_datos': metricas.get('fuente_datos', 'desconocido'),
                        'requiere_revision': metricas.get('requiere_revision', False),
                        'proveedor': producto.proveedor_principal.nombre if producto.proveedor_principal else 'Sin proveedor',
                        'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                        'precio_costo': float(producto.precio_costo) if producto.precio_costo else 0,
                    })

                    # Si ya tenemos suficientes, salir
                    if len(criticos) >= limit:
                        break

            except Exception as e:
                print(f"Error procesando producto {producto.codigo}: {str(e)}")
                continue

        # Ordenar por prioridad de criticidad
        # 1. Primero los que tienen días de cobertura (por días asc)
        # 2. Luego los sin datos pero con stock crítico
        criticos_ordenados = sorted(
            criticos,
            key=lambda x: (
                0 if x['dias_cobertura'] is not None else 1,  # Con días primero
                x['dias_cobertura'] if x['dias_cobertura'] is not None else 999,  # Menor días primero
                x['stock_actual']  # Si no hay días, menor stock primero
            )
        )

        return Response({
            'total': len(criticos_ordenados),
            'productos': criticos_ordenados[:limit],
            'timestamp': timezone.now().isoformat(),
            'niveles_riesgo_incluidos': ['critico', 'alto', 'sin_datos_stock_critico'],
            'descripcion': {
                'critico': '< 7 días de cobertura',
                'alto': '7-13 días de cobertura',
                'sin_datos_stock_critico': 'Sin ventas históricas, stock < 5 unidades'
            }
        })

    @action(detail=False, methods=['get'], url_path='ultima-carga')
    def ultima_carga(self, request):
        """Obtiene la fecha y hora de la última carga de inventario"""
        # Buscar el producto más reciente (por fecha de registro)
        producto_reciente = Producto.objects.filter(
            activo=True
        ).order_by('-fecha_registro').first()

        if producto_reciente:
            return Response({
                'fecha_ultima_carga': producto_reciente.fecha_registro.isoformat(),
                'tiene_inventario': True
            })
        else:
            return Response({
                'fecha_ultima_carga': None,
                'tiene_inventario': False
            })

    @action(detail=False, methods=['post'])
    def cargar_excel(self, request):
        """Cargar productos desde archivo Excel"""
        archivo = request.FILES.get('archivo')

        if not archivo:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar extensión
        if not archivo.name.endswith(('.xlsx', '.xls', '.XLS', '.XLSX')):
            return Response(
                {'error': 'El archivo debe ser Excel (.xlsx o .xls)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from core.parsers.product_excel_parser import ProductExcelParser

            parser = ProductExcelParser(archivo)
            result = parser.parse_and_load()

            return Response({
                'message': 'Archivo procesado correctamente',
                'productos_insertados': result.get('insertados', 0),
                'productos_actualizados': result.get('actualizados', 0),
                'errores': result.get('errores', [])
            })

        except Exception as e:
            return Response(
                {'error': f'Error procesando archivo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer


class OfertaLaboratorioViewSet(viewsets.ModelViewSet):
    queryset = OfertaLaboratorio.objects.filter(activa=True)
    serializer_class = OfertaLaboratorioSerializer

    @action(detail=False, methods=['get'])
    def por_laboratorio(self, request):
        """
        Obtiene ofertas agrupadas por laboratorio con paginación backend.
        Query params:
            - laboratorio: Filtrar por nombre de laboratorio (opcional)
            - proveedor: Filtrar por nombre de proveedor (opcional)
            - activas: Filtrar solo activas (default: true)
            - page: Número de página (default: 1)
            - page_size: Items por página (default: 50, max: 100)
            - search: Búsqueda en código, descripción, laboratorio
        """
        import logging
        logger = logging.getLogger(__name__)

        laboratorio = request.query_params.get('laboratorio', None)
        proveedor = request.query_params.get('proveedor', None)
        solo_activas = request.query_params.get('activas', 'false').lower() == 'true'
        search = request.query_params.get('search', None)

        logger.info(f"📋 Filtros recibidos: laboratorio={laboratorio}, proveedor={proveedor}, activas={solo_activas}, search={search}")

        # Query optimizado con select_related para reducir queries
        ofertas = OfertaLaboratorio.objects.select_related(
            'producto_catalogo',
            'producto_catalogo__proveedor',
            'laboratorio'
        ).only(
            # Solo campos necesarios para reducir payload
            'id', 'precio_normal', 'precio_oferta',
            'descuento', 'fecha_inicio', 'fecha_fin', 'activa', 'created_at',
            'producto_catalogo__id', 'producto_catalogo__codigo', 'producto_catalogo__nombre',
            'producto_catalogo__descripcion', 'producto_catalogo__proveedor__nombre',
            'laboratorio__id', 'laboratorio__nombre'
        )

        total_inicial = ofertas.count()
        logger.info(f"📊 Total ofertas (sin filtros): {total_inicial}")

        # Filtros
        if solo_activas:
            # Filtrar solo ofertas vigentes
            today = timezone.now().date()
            ofertas = ofertas.filter(activa=True, fecha_fin__gte=today)
            logger.info(f"📊 Después de filtro activas (fecha_fin >= {today}): {ofertas.count()}")

        if laboratorio:
            ofertas = ofertas.filter(laboratorio__nombre__icontains=laboratorio)
            logger.info(f"📊 Después de filtro laboratorio '{laboratorio}': {ofertas.count()}")

        if proveedor:
            # Debug: mostrar proveedores disponibles antes del filtro
            proveedores_disponibles = ofertas.values_list('producto_catalogo__proveedor__nombre', flat=True).distinct()
            logger.info(f"🔍 Proveedores disponibles: {list(proveedores_disponibles)}")
            logger.info(f"🔍 Buscando proveedor: '{proveedor}'")

            ofertas = ofertas.filter(producto_catalogo__proveedor__nombre__icontains=proveedor)
            logger.info(f"📊 Después de filtro proveedor '{proveedor}': {ofertas.count()}")

        if search:
            ofertas = ofertas.filter(
                Q(producto_catalogo__codigo__icontains=search) |
                Q(producto_catalogo__nombre__icontains=search) |
                Q(laboratorio__nombre__icontains=search) |
                Q(producto_catalogo__proveedor__nombre__icontains=search)
            )

        # Ordenamiento dinámico (si se especifica)
        ordering = request.query_params.get('ordering', None)
        if ordering:
            # Soportar ordenamiento descendente con prefijo '-'
            ofertas = ofertas.order_by(ordering)
        else:
            # Ordenar por defecto por laboratorio y producto
            ofertas = ofertas.order_by('laboratorio__nombre', 'producto_catalogo__nombre')

        # Aplicar paginación backend
        paginator = OfertasPagination()
        page = paginator.paginate_queryset(ofertas, request)

        if page is not None:
            serializer = OfertaLaboratorioDetalladaSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback sin paginación (no debería llegar aquí normalmente)
        serializer = OfertaLaboratorioDetalladaSerializer(ofertas, many=True)
        return Response({
            'total': ofertas.count(),
            'ofertas': serializer.data
        })

    @action(detail=False, methods=['get'])
    def laboratorios(self, request):
        """
        Lista todos los laboratorios disponibles con ofertas y conteo.
        Devuelve el NOMBRE del laboratorio (no el ID) para mostrar en el filtro.
        Incluye todas las ofertas (vigentes y vencidas).
        """
        laboratorios = (
            OfertaLaboratorio.objects
            .filter(laboratorio__isnull=False)
            .values('laboratorio__nombre')
            .annotate(
                total_ofertas=Count('id'),
                promedio_descuento=Sum('descuento') / Count('id')
            )
            .order_by('-total_ofertas')
        )

        # Mapear laboratorio__nombre a "laboratorio" para mantener compatibilidad con frontend
        laboratorios_list = [
            {
                'laboratorio': lab['laboratorio__nombre'],
                'total_ofertas': lab['total_ofertas'],
                'promedio_descuento': lab['promedio_descuento']
            }
            for lab in laboratorios
        ]

        return Response({
            'total_laboratorios': len(laboratorios_list),
            'laboratorios': laboratorios_list
        })

    @action(detail=False, methods=['get'])
    def proveedores(self, request):
        """
        Lista todos los proveedores disponibles con ofertas y conteo.
        Devuelve el NOMBRE del proveedor para mostrar en el filtro.
        Incluye todas las ofertas (vigentes y vencidas).
        """
        proveedores = (
            OfertaLaboratorio.objects
            .filter(producto_catalogo__proveedor__isnull=False)
            .values('producto_catalogo__proveedor__nombre')
            .annotate(
                total_ofertas=Count('id'),
                promedio_descuento=Sum('descuento') / Count('id')
            )
            .order_by('-total_ofertas')
        )

        # Mapear a formato consistente
        proveedores_list = [
            {
                'proveedor': prov['producto_catalogo__proveedor__nombre'],
                'total_ofertas': prov['total_ofertas'],
                'promedio_descuento': prov['promedio_descuento']
            }
            for prov in proveedores
        ]

        return Response({
            'total_proveedores': len(proveedores_list),
            'proveedores': proveedores_list
        })

    @action(detail=False, methods=['post'])
    def procesar(self, request):
        """Procesar archivo de ofertas (Excel/PDF)"""
        archivo = request.FILES.get('archivo')

        if not archivo:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Implementar lógica de ETL
        # Por ahora solo retorna mensaje de éxito
        return Response({
            'message': f'Archivo {archivo.name} recibido y procesado correctamente',
            'ofertas_creadas': 0
        })


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.select_related('cliente').prefetch_related('detalles__producto').all()
    serializer_class = VentaSerializer
    pagination_class = OfertasPagination  # 50 ventas por página
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero', 'cliente__rut', 'cliente__nombre', 'detalles__producto__codigo', 'detalles__producto__descripcion']
    ordering_fields = ['id', 'numero', 'fecha', 'total', 'cliente__rut', 'cliente__nombre']
    ordering = ['-fecha']  # Ordenamiento por defecto

    def get_queryset(self):
        queryset = super().get_queryset()

        # Obtener término de búsqueda y normalizarlo (quitar puntos y guiones para RUT)
        search = self.request.query_params.get('search', '')
        if search:
            # Normalizar RUT: quitar puntos y guiones
            search_normalized = search.replace('.', '').replace('-', '').strip()

            # Buscar con ambos formatos (original y normalizado)
            queryset = queryset.filter(
                Q(numero__icontains=search) |
                Q(cliente__rut__icontains=search_normalized) |
                Q(cliente__nombre__icontains=search) |
                Q(detalles__producto__codigo__icontains=search) |
                Q(detalles__producto__descripcion__icontains=search)
            ).distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        # Si hay búsqueda personalizada, no usar el SearchFilter predeterminado
        if request.query_params.get('search'):
            # Remover temporalmente SearchFilter para usar nuestra lógica
            self.filter_backends = [filters.OrderingFilter]
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='ultima-carga')
    def ultima_carga(self, request):
        """Obtiene la fecha y hora de la última carga de ventas"""
        venta_reciente = Venta.objects.filter(
            estado='completada'
        ).order_by('-fecha').first()

        if venta_reciente:
            return Response({
                'fecha_ultima_carga': venta_reciente.fecha.isoformat(),
                'tiene_ventas': True
            })
        else:
            return Response({
                'fecha_ultima_carga': None,
                'tiene_ventas': False
            })

    @action(detail=False, methods=['post'])
    def cargar_excel(self, request):
        """Cargar ventas desde archivo Excel"""
        archivo = request.FILES.get('archivo')

        if not archivo:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar extensión
        if not archivo.name.endswith(('.xlsx', '.xls', '.XLS', '.XLSX')):
            return Response(
                {'error': 'El archivo debe ser Excel (.xlsx o .xls)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from core.parsers.sales_excel_parser import SalesExcelParser

            parser = SalesExcelParser(archivo)
            result = parser.parse_and_load()

            return Response({
                'message': 'Archivo de ventas procesado correctamente',
                'ventas_insertadas': result.get('ventas_insertadas', 0),
                'ventas_duplicadas': result.get('ventas_duplicadas', 0),
                'detalles_insertados': result.get('detalles_insertados', 0),
                'detalles_duplicados_omitidos': result.get('detalles_duplicados_omitidos', 0),
                'clientes_creados': result.get('clientes_creados', 0),
                'productos_no_encontrados': result.get('productos_no_encontrados', 0),
                'errores': result.get('errores', [])[:20]  # Mostrar solo primeros 20 errores
            })

        except Exception as e:
            return Response(
                {'error': f'Error procesando archivo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardViewSet(viewsets.GenericViewSet):
    """Endpoints específicos para el dashboard"""
    # Queryset vacío para que el router funcione correctamente
    queryset = Venta.objects.none()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas generales del dashboard"""
        # Total ventas
        total_ventas = Venta.objects.filter(estado='completada').aggregate(
            total=Sum('total')
        )['total'] or 0

        # Ventas del mes más reciente (último mes con ventas)
        # Obtener la venta más reciente
        venta_reciente = Venta.objects.filter(estado='completada').order_by('-fecha').first()

        if venta_reciente:
            # Calcular el primer día del mes de esa venta
            mes_reciente = venta_reciente.fecha.replace(day=1)
            # Calcular el último día del mes
            if mes_reciente.month == 12:
                fin_mes = mes_reciente.replace(year=mes_reciente.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                fin_mes = mes_reciente.replace(month=mes_reciente.month + 1, day=1) - timedelta(days=1)

            ventas_mes = Venta.objects.filter(
                estado='completada',
                fecha__gte=mes_reciente,
                fecha__lte=fin_mes
            ).aggregate(total=Sum('total'))['total'] or 0
        else:
            ventas_mes = 0

        # Productos en stock
        productos_stock = Producto.objects.filter(activo=True).count()

        # Clientes activos (con compras en los últimos 6 meses)
        hace_6_meses = timezone.now() - timedelta(days=180)
        clientes_activos = Cliente.objects.filter(
            ventas__fecha__gte=hace_6_meses
        ).distinct().count()

        return Response({
            'total_ventas': total_ventas,
            'ventas_mes': ventas_mes,
            'productos_stock': productos_stock,
            'clientes_activos': clientes_activos
        })

    @action(detail=False, methods=['get'])
    def sales(self, request):
        """Datos de ventas para gráficos"""
        # Ventas de los últimos 12 meses
        hace_12_meses = timezone.now() - timedelta(days=365)

        # Usar TruncMonth para PostgreSQL (compatible con todas las BD)
        ventas_mensuales = Venta.objects.filter(
            estado='completada',
            fecha__gte=hace_12_meses
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total=Sum('total')
        ).order_by('mes')

        # Formatear la respuesta
        result = []
        for venta in ventas_mensuales:
            result.append({
                'mes': venta['mes'].strftime('%Y-%m') if venta['mes'] else None,
                'total': float(venta['total']) if venta['total'] else 0
            })

        return Response(result)

    @action(detail=False, methods=['get'], url_path='top-products')
    def top_products(self, request):
        """Top 10 productos más vendidos"""
        limit = int(request.query_params.get('limit', 10))

        top_productos = DetalleVenta.objects.values(
            'producto__codigo',
            'producto__descripcion'
        ).annotate(
            cantidad=Sum('cantidad'),
            ventas=Sum('subtotal')
        ).order_by('-cantidad')[:limit]

        return Response(list(top_productos))


class SugerenciaCompraViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Sugerencias de Compra Inteligentes.

    Endpoints:
    - /api/sugerencias-compra/ - CRUD básico
    - /api/sugerencias-compra/generar/ - Genera sugerencias desde productos críticos
    - /api/sugerencias-compra/consolidar/ - Consolida por proveedor
    - /api/sugerencias-compra/export-excel/ - Exporta a Excel
    """
    queryset = SugerenciaCompra.objects.all()
    serializer_class = SugerenciaCompraSerializer
    pagination_class = OfertasPagination

    def get_queryset(self):
        """Filtra sugerencias"""
        queryset = super().get_queryset()

        # Filtro por estado
        procesada = self.request.query_params.get('procesada', None)
        if procesada is not None:
            queryset = queryset.filter(procesada=procesada.lower() == 'true')

        # Filtro por proveedor
        proveedor = self.request.query_params.get('proveedor', None)
        if proveedor:
            queryset = queryset.filter(proveedor_recomendado__id=proveedor)

        return queryset.select_related('producto', 'proveedor_recomendado').order_by('-prioridad', '-fecha_creacion')

    @action(detail=False, methods=['get'])
    def todas(self, request):
        """
        Endpoint unificado optimizado que retorna todas las sugerencias agrupadas por tipo.
        Mucho más rápido que hacer 3 llamadas separadas.

        Returns:
            {
                'bajo_stock': [...],
                'estacionales': [...],
                'epidemiologicas': [...],
                'timestamp': '...',
                'total_sugerencias': N
            }
        """
        limite_por_tipo = int(request.query_params.get('limite', 50))

        # Query optimizado con select_related para reducir queries a BD
        base_query = SugerenciaCompra.objects.filter(
            procesada=False
        ).select_related(
            'producto',
            'producto__categoria',
            'producto__proveedor_principal',
            'proveedor_recomendado'
        ).only(
            # Solo campos necesarios para reducir payload
            'id', 'tipo', 'cantidad_sugerida', 'prioridad', 'razon',
            'precio_unitario', 'tiene_oferta', 'precio_oferta', 'descuento_porcentaje',
            'confianza_ml', 'fuente_datos', 'dias_cobertura',
            'producto__id', 'producto__codigo', 'producto__nombre', 'producto__descripcion',
            'producto__stock_actual', 'producto__stock_minimo', 'producto__precio_costo',
            'producto__categoria__nombre',
            'proveedor_recomendado__id', 'proveedor_recomendado__nombre'
        )

        # Obtener sugerencias por tipo (limitadas)
        bajo_stock = list(base_query.filter(tipo='bajo_stock').order_by('-prioridad', '-fecha_creacion')[:limite_por_tipo])
        estacionales = list(base_query.filter(tipo='estacional').order_by('-confianza_ml', '-prioridad')[:limite_por_tipo])
        epidemiologicas = list(base_query.filter(tipo='epidemiologico').order_by('-prioridad')[:limite_por_tipo])

        # Serializar
        serializer = self.get_serializer(bajo_stock + estacionales + epidemiologicas, many=True)
        data = serializer.data

        # Agrupar por tipo
        resultado = {
            'bajo_stock': [s for s in data if s['tipo'] == 'bajo_stock'],
            'estacionales': [s for s in data if s['tipo'] == 'estacional'],
            'epidemiologicas': [s for s in data if s['tipo'] == 'epidemiologico'],
            'timestamp': timezone.now().isoformat(),
            'total_sugerencias': len(data)
        }

        return Response(resultado)

    @action(detail=False, methods=['get'], url_path='low-stock')
    def low_stock(self, request):
        """
        Sugerencias por bajo stock (optimizado)
        Límite: 50 sugerencias por defecto
        """
        limite = int(request.query_params.get('limite', 50))

        sugerencias = SugerenciaCompra.objects.filter(
            tipo='bajo_stock',
            procesada=False
        ).select_related(
            'producto',
            'producto__categoria',
            'proveedor_recomendado'
        ).order_by('-prioridad', '-fecha_creacion')[:limite]

        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def season(self, request):
        """
        Sugerencias estacionales (optimizado)
        Límite: 50 sugerencias por defecto
        """
        limite = int(request.query_params.get('limite', 50))

        sugerencias = SugerenciaCompra.objects.filter(
            tipo='estacional',
            procesada=False
        ).select_related(
            'producto',
            'producto__categoria',
            'proveedor_recomendado'
        ).order_by('-confianza_ml', '-prioridad')[:limite]

        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def epidemiological(self, request):
        """
        Sugerencias epidemiológicas (optimizado)
        Límite: 50 sugerencias por defecto
        """
        limite = int(request.query_params.get('limite', 50))

        sugerencias = SugerenciaCompra.objects.filter(
            tipo='epidemiologico',
            procesada=False
        ).select_related(
            'producto',
            'producto__categoria',
            'proveedor_recomendado'
        ).order_by('-prioridad')[:limite]

        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generar(self, request):
        """
        Genera sugerencias de compra desde productos críticos.

        Query params:
            - limite: Número máximo de productos a procesar (default: 100)
            - forzar_mapeo: Si True, mapea automáticamente productos sin mapping (default: true)
        """
        from .purchase_optimizer_service import purchase_optimizer

        limite = int(request.query_params.get('limite', 100))
        forzar_mapeo = request.query_params.get('forzar_mapeo', 'true').lower() == 'true'

        try:
            stats = purchase_optimizer.generar_sugerencias_desde_criticos(
                limite=limite,
                forzar_mapeo=forzar_mapeo
            )

            return Response({
                'success': True,
                'mensaje': f'Sugerencias generadas correctamente',
                'estadisticas': stats,
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def consolidar(self, request):
        """
        Consolida sugerencias por proveedor (optimizado).

        Agrupa sugerencias no procesadas por proveedor,
        calcula totales y valida mínimos de pedido.

        Returns:
            {
                'MEDIVEN': {
                    'total': 150000,
                    'cumple_minimo': true,
                    'minimo_requerido': 50000,
                    'sugerencias': [...]
                },
                'SOCOFAR': {...}
            }
        """
        from .purchase_optimizer_service import purchase_optimizer

        try:
            # Verificar rápidamente si hay sugerencias
            if not SugerenciaCompra.objects.filter(procesada=False, incluida_en_orden=False).exists():
                return Response({
                    'success': True,
                    'consolidado': {},
                    'total_proveedores': 0,
                    'timestamp': timezone.now().isoformat(),
                    'mensaje': 'No hay sugerencias pendientes para consolidar'
                })

            consolidado = purchase_optimizer.consolidar_por_proveedor(incluir_solo_activas=True)

            # Limitar sugerencias en respuesta a 50 por proveedor para reducir payload
            limite_sugerencias = 50

            # Serializar para respuesta
            resultado = {}
            for prov_nombre, data in consolidado.items():
                # Limitar sugerencias serializadas
                sugerencias_limitadas = data['sugerencias'][:limite_sugerencias]
                sugerencias_serialized = SugerenciaCompraSerializer(
                    sugerencias_limitadas, many=True
                ).data

                resultado[prov_nombre] = {
                    'proveedor': {
                        'id': data['proveedor'].id,
                        'nombre': data['proveedor'].nombre
                    },
                    'total': float(data['total']),
                    'cumple_minimo': data['cumple_minimo'],
                    'minimo_requerido': float(data['minimo_requerido']),
                    'cantidad_productos': len(data['sugerencias']),
                    'sugerencias': sugerencias_serialized,
                    'total_sugerencias': len(data['sugerencias']),
                    'sugerencias_mostradas': len(sugerencias_limitadas)
                }

            return Response({
                'success': True,
                'consolidado': resultado,
                'total_proveedores': len(resultado),
                'timestamp': timezone.now().isoformat()
            })

        except Exception as e:
            print(f"Error en consolidar: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """
        Exporta sugerencias consolidadas a Excel.

        Query params:
            - proveedor: Filtrar por proveedor específico (opcional)
        """
        from django.http import HttpResponse
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from .purchase_optimizer_service import purchase_optimizer

        try:
            consolidado = purchase_optimizer.consolidar_por_proveedor(incluir_solo_activas=True)

            # Filtrar por proveedor si se especifica
            proveedor_filtro = request.query_params.get('proveedor', None)
            if proveedor_filtro:
                consolidado = {
                    k: v for k, v in consolidado.items()
                    if k.upper() == proveedor_filtro.upper()
                }

            # Crear libro Excel
            wb = openpyxl.Workbook()
            wb.remove(wb.active)  # Eliminar hoja por defecto

            # Estilos
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            title_font = Font(size=14, bold=True)

            # Crear hoja por proveedor
            for prov_nombre, data in consolidado.items():
                ws = wb.create_sheet(title=prov_nombre[:31])  # Excel limita a 31 chars

                # Título
                ws['A1'] = f"ORDEN DE COMPRA - {prov_nombre}"
                ws['A1'].font = title_font
                ws.merge_cells('A1:H1')

                # Info del proveedor
                ws['A2'] = f"Fecha: {timezone.now().strftime('%d/%m/%Y %H:%M')}"
                ws['A3'] = f"Total: ${data['total']:,.0f}"
                ws['A4'] = f"Mínimo Requerido: ${data['minimo_requerido']:,.0f}"
                ws['A5'] = f"Cumple Mínimo: {'SÍ' if data['cumple_minimo'] else 'NO'}"

                # Headers
                row = 7
                headers = ['Código', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal', 'Tiene Oferta', 'Descuento %', 'Ahorro']
                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=row, column=col, value=header)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center')

                # Datos
                row = 8
                for sug in data['sugerencias']:
                    ws.cell(row=row, column=1, value=sug.producto.codigo)
                    ws.cell(row=row, column=2, value=sug.producto.nombre)
                    ws.cell(row=row, column=3, value=sug.cantidad_sugerida)
                    ws.cell(row=row, column=4, value=float(sug.precio_unitario) if sug.precio_unitario else 0)
                    ws.cell(row=row, column=5, value=sug.total)
                    ws.cell(row=row, column=6, value='SÍ' if sug.tiene_oferta else 'NO')
                    ws.cell(row=row, column=7, value=float(sug.descuento_porcentaje) if sug.descuento_porcentaje else 0)
                    ws.cell(row=row, column=8, value=sug.ahorro_total)
                    row += 1

                # Totales
                row += 1
                ws.cell(row=row, column=2, value="TOTAL").font = Font(bold=True)
                ws.cell(row=row, column=5, value=float(data['total'])).font = Font(bold=True)

                # Ajustar anchos
                ws.column_dimensions['A'].width = 15
                ws.column_dimensions['B'].width = 50
                ws.column_dimensions['C'].width = 10
                ws.column_dimensions['D'].width = 12
                ws.column_dimensions['E'].width = 12
                ws.column_dimensions['F'].width = 12
                ws.column_dimensions['G'].width = 12
                ws.column_dimensions['H'].width = 12

            # Generar respuesta HTTP
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            filename = f"orden_compra_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
            response['Content-Disposition'] = f'attachment; filename={filename}'

            wb.save(response)
            return response

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

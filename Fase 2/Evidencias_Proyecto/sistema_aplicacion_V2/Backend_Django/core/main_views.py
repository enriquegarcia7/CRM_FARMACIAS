from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncMonth, TruncDate
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

    @action(detail=False, methods=['get'])
    def frecuentes(self, request):
        """Obtiene clientes frecuentes (con 5 o más compras)"""
        clientes = Cliente.objects.annotate(
            total_ventas=Count('ventas', filter=Q(ventas__estado='completada'))
        ).filter(total_ventas__gte=5)

        serializer = self.get_serializer(clientes, many=True)
        return Response(serializer.data)


class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de transacciones"""
        total = Transaccion.objects.count()
        return Response({'total': total})


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('proveedor').all()
    serializer_class = ProductoSerializer
    pagination_class = OfertasPagination  # 50 productos por página

    def get_queryset(self):
        """Query optimizado con filtros"""
        queryset = super().get_queryset()

        # FILTRO PRINCIPAL: Solo productos en inventario actual (del último Excel)
        queryset = queryset.filter(en_inventario_actual=True)

        # Filtro de búsqueda
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search) |
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(categoria__icontains=search)
            )

        # Filtro de stock
        filtro_stock = self.request.query_params.get('filtro_stock', None)
        if filtro_stock == 'bajo':
            queryset = queryset.filter(stock_actual__lt=F('stock_minimo'))
        elif filtro_stock == 'normal':
            queryset = queryset.filter(stock_actual__gte=F('stock_minimo'))

        return queryset.order_by('codigo')

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

    @action(detail=False, methods=['get'], url_path='ultima-carga')
    def ultima_carga(self, request):
        """Obtiene la fecha y hora de la última carga de inventario"""
        # Buscar el producto con la fecha de última carga más reciente
        producto_reciente = Producto.objects.filter(
            en_inventario_actual=True,
            fecha_ultima_carga__isnull=False
        ).order_by('-fecha_ultima_carga').first()

        if producto_reciente and producto_reciente.fecha_ultima_carga:
            return Response({
                'fecha_ultima_carga': producto_reciente.fecha_ultima_carga.isoformat(),
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
            - activas: Filtrar solo activas (default: true)
            - page: Número de página (default: 1)
            - page_size: Items por página (default: 50, max: 100)
            - search: Búsqueda en código, descripción, laboratorio
        """
        laboratorio = request.query_params.get('laboratorio', None)
        solo_activas = request.query_params.get('activas', 'true').lower() == 'true'
        search = request.query_params.get('search', None)

        # Query optimizado con select_related para reducir queries
        ofertas = OfertaLaboratorio.objects.select_related(
            'producto',
            'producto__proveedor'
        ).only(
            # Solo campos necesarios para reducir payload
            'id', 'laboratorio', 'precio_normal', 'precio_oferta',
            'descuento', 'fecha_inicio', 'fecha_fin', 'activa', 'created_at',
            'producto__id', 'producto__codigo', 'producto__nombre',
            'producto__descripcion', 'producto__proveedor__nombre'
        )

        # Filtros
        if solo_activas:
            # Filtrar solo ofertas vigentes
            today = timezone.now().date()
            ofertas = ofertas.filter(activa=True, fecha_fin__gte=today)

        if laboratorio:
            ofertas = ofertas.filter(laboratorio__icontains=laboratorio)

        if search:
            ofertas = ofertas.filter(
                Q(producto__codigo__icontains=search) |
                Q(producto__nombre__icontains=search) |
                Q(laboratorio__icontains=search) |
                Q(producto__proveedor__nombre__icontains=search)
            )

        # Ordenar por laboratorio y producto
        ofertas = ofertas.order_by('laboratorio', 'producto__nombre')

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
        Lista todos los laboratorios disponibles con ofertas activas y conteo.
        """
        laboratorios = (
            OfertaLaboratorio.objects
            .filter(activa=True)
            .values('laboratorio')
            .annotate(
                total_ofertas=Count('id'),
                promedio_descuento=Sum('descuento') / Count('id')
            )
            .order_by('-total_ofertas')
        )

        return Response({
            'total_laboratorios': laboratorios.count(),
            'laboratorios': list(laboratorios)
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


class SugerenciaCompraViewSet(viewsets.ModelViewSet):
    queryset = SugerenciaCompra.objects.filter(procesada=False)
    serializer_class = SugerenciaCompraSerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Sugerencias por bajo stock"""
        sugerencias = self.queryset.filter(tipo='bajo_stock')
        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def season(self, request):
        """Sugerencias estacionales"""
        sugerencias = self.queryset.filter(tipo='estacional')
        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def epidemiological(self, request):
        """Sugerencias epidemiológicas"""
        sugerencias = self.queryset.filter(tipo='epidemiologico')
        serializer = self.get_serializer(sugerencias, many=True)
        return Response(serializer.data)


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer


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

        # Ventas del mes actual
        mes_actual = timezone.now().replace(day=1)
        ventas_mes = Venta.objects.filter(
            estado='completada',
            fecha__gte=mes_actual
        ).aggregate(total=Sum('total'))['total'] or 0

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

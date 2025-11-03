# Este archivo hace que el directorio views sea un paquete de Python
# Importamos todas las vistas del archivo main_views.py para mantener compatibilidad

from ..main_views import (
    ClienteViewSet,
    TransaccionViewSet,
    ProductoViewSet,
    ProveedorViewSet,
    OfertaLaboratorioViewSet,
    SugerenciaCompraViewSet,
    VentaViewSet,
    DashboardViewSet
)

# Asegurar que estas clases estén disponibles cuando se importa core.views
__all__ = [
    'ClienteViewSet',
    'TransaccionViewSet',
    'ProductoViewSet',
    'ProveedorViewSet',
    'OfertaLaboratorioViewSet',
    'SugerenciaCompraViewSet',
    'VentaViewSet',
    'DashboardViewSet'
]

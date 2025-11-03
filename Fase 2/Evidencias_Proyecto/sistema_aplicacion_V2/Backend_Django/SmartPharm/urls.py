from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework import routers
from core.views import (
    ClienteViewSet, TransaccionViewSet, ProductoViewSet,
    ProveedorViewSet, OfertaLaboratorioViewSet,
    SugerenciaCompraViewSet, VentaViewSet, DashboardViewSet
)

# Rutas API
router = routers.DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'transacciones', TransaccionViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'ofertas', OfertaLaboratorioViewSet, basename='oferta')
router.register(r'sugerencias', SugerenciaCompraViewSet)
router.register(r'ventas', VentaViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# Función para redirigir la raíz a /admin
def redirect_to_admin(request):
    return redirect('/admin/')

# URLs del proyecto
urlpatterns = [
    path('', redirect_to_admin),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include('core.urls')),
]

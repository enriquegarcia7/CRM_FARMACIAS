from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework import routers
from core.views import (
    ClienteViewSet, TransaccionViewSet, ProductoViewSet,
    ProveedorViewSet, OfertaLaboratorioViewSet,
    SugerenciaCompraViewSet, VentaViewSet, DashboardViewSet
)
from core.views.etl_views import run_etl_manual, get_etl_logs, get_etl_status, get_etl_progress, get_etl_diagnostic
from core.views.gmail_auth_views import (
    check_gmail_auth, start_gmail_auth, gmail_auth_callback, revoke_gmail_auth
)
from core.views.auth_views import (
    start_login, login_callback, check_session, logout
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

    # ETL endpoints
    path('api/etl/run/', run_etl_manual, name='run_etl'),
    path('api/etl/logs/', get_etl_logs, name='etl_logs'),
    path('api/etl/status/', get_etl_status, name='etl_status'),
    path('api/etl/progress/', get_etl_progress, name='etl_progress'),
    path('api/etl/diagnostic/', get_etl_diagnostic, name='etl_diagnostic'),

    # Gmail OAuth endpoints
    path('api/gmail/auth/status/', check_gmail_auth, name='gmail_auth_status'),
    path('api/gmail/auth/start/', start_gmail_auth, name='gmail_auth_start'),
    path('api/gmail/callback', gmail_auth_callback, name='gmail_callback'),
    path('api/gmail/auth/revoke/', revoke_gmail_auth, name='gmail_auth_revoke'),

    # User Authentication endpoints (Login con Google + Gmail automático)
    path('api/auth/login/start/', start_login, name='login_start'),
    path('api/auth/callback', login_callback, name='login_callback'),
    path('api/auth/session/', check_session, name='check_session'),
    path('api/auth/logout/', logout, name='logout'),
    path('api/', include('core.urls')),
]

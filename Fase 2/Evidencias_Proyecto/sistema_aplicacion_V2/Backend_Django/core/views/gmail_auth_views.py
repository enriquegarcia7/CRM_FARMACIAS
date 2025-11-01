from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
import logging
import json
from config.secrets import (
    ensure_credentials_file_exists,
    get_gmail_token_path,
    get_credentials_file_path
)

logger = logging.getLogger(__name__)

# Configuración OAuth
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# URL de callback - debe coincidir con la configurada en Google Cloud Console
REDIRECT_URI = os.getenv('GMAIL_REDIRECT_URI', 'http://localhost:8000/api/gmail/callback')


def get_flow():
    """Crea y retorna un Flow de OAuth usando credenciales desde config.secrets"""
    # Asegurar que el archivo de credenciales existe (lo crea desde Base64 si no existe)
    credentials_path = ensure_credentials_file_exists(settings.BASE_DIR)

    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow


@api_view(['GET'])
@permission_classes([AllowAny])
def check_gmail_auth(request):
    """
    Verifica si Gmail está autenticado.
    GET /api/gmail/auth/status/
    """
    try:
        token_path = get_gmail_token_path(settings.BASE_DIR)

        # Verificar si existe el token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # Verificar si el token es válido
            if creds and creds.valid:
                return Response({
                    'authenticated': True,
                    'message': 'Gmail autenticado correctamente'
                })

            # Si el token existe pero no es válido o está expirado
            return Response({
                'authenticated': False,
                'message': 'Token expirado o inválido. Se requiere re-autenticación.'
            })

        # No existe token
        return Response({
            'authenticated': False,
            'message': 'No se ha autenticado Gmail. Se requiere autenticación.'
        })

    except Exception as e:
        logger.error(f"Error checking Gmail auth: {e}")
        return Response({
            'authenticated': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def start_gmail_auth(request):
    """
    Inicia el flujo de autenticación OAuth de Gmail.
    GET /api/gmail/auth/start/

    Retorna la URL a la que el usuario debe ser redirigido para autenticarse.
    """
    try:
        flow = get_flow()

        # Generar URL de autorización
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Fuerza el prompt de consentimiento para obtener refresh_token
        )

        # Guardar el state en sesión o base de datos para validarlo en el callback
        request.session['oauth_state'] = state

        logger.info(f"🔐 Gmail auth URL generada: {authorization_url}")

        return Response({
            'success': True,
            'auth_url': authorization_url,
            'message': 'Redirige al usuario a auth_url para autenticación'
        })

    except FileNotFoundError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error starting Gmail auth: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def gmail_auth_callback(request):
    """
    Callback de OAuth de Gmail.
    GET /api/gmail/callback?code=...&state=...

    Google redirigirá aquí después de que el usuario autorice la aplicación.
    Esta función retorna un HTML que notifica a la ventana principal y se cierra.
    """
    try:
        # Obtener el código de autorización de los query params
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')

        # Si el usuario rechazó la autorización
        if error:
            logger.warning(f"❌ Gmail auth denied: {error}")
            return HttpResponse(f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Autenticación Cancelada</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                            background: #f9fafb;
                        }}
                        .container {{
                            text-align: center;
                            padding: 2rem;
                            background: white;
                            border-radius: 0.5rem;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            max-width: 400px;
                        }}
                        .icon {{ font-size: 3rem; margin-bottom: 1rem; }}
                        h1 {{ color: #dc2626; font-size: 1.5rem; margin-bottom: 0.5rem; }}
                        p {{ color: #6b7280; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="icon">❌</div>
                        <h1>Autenticación Cancelada</h1>
                        <p>{error}</p>
                        <p style="margin-top: 1rem; font-size: 0.875rem;">Esta ventana se cerrará automáticamente...</p>
                    </div>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'GMAIL_AUTH_ERROR',
                                message: '{error}'
                            }}, window.location.origin);
                        }}
                        setTimeout(() => window.close(), 2000);
                    </script>
                </body>
                </html>
            ''')

        if not code:
            return HttpResponse('''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Error de Autenticación</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                            background: #f9fafb;
                        }}
                        .container {{
                            text-align: center;
                            padding: 2rem;
                            background: white;
                            border-radius: 0.5rem;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>❌ Error</h1>
                        <p>No se recibió código de autorización</p>
                    </div>
                    <script>
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'GMAIL_AUTH_ERROR',
                                message: 'No se recibió código de autorización'
                            }}, window.location.origin);
                        }}
                        setTimeout(() => window.close(), 2000);
                    </script>
                </body>
                </html>
            ''')

        # Validar state (opcional pero recomendado)
        saved_state = request.session.get('oauth_state')
        if saved_state and saved_state != state:
            logger.warning("⚠️ OAuth state mismatch - posible CSRF")

        # Intercambiar código por tokens
        flow = get_flow()
        flow.fetch_token(code=code)

        # Obtener credenciales
        creds = flow.credentials

        # Guardar token en archivo
        token_path = get_gmail_token_path(settings.BASE_DIR)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

        logger.info("✅ Gmail autenticado exitosamente")

        # Retornar HTML que notifica al padre y se cierra
        return HttpResponse('''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Autenticación Exitosa</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        text-align: center;
                        padding: 3rem 2rem;
                        background: white;
                        border-radius: 1rem;
                        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                        max-width: 400px;
                    }
                    .icon {
                        font-size: 4rem;
                        margin-bottom: 1rem;
                        animation: checkmark 0.5s ease-in-out;
                    }
                    @keyframes checkmark {
                        0% { transform: scale(0); }
                        50% { transform: scale(1.2); }
                        100% { transform: scale(1); }
                    }
                    h1 {
                        color: #10b981;
                        font-size: 1.75rem;
                        margin-bottom: 0.5rem;
                        font-weight: 600;
                    }
                    p {
                        color: #6b7280;
                        margin-bottom: 1.5rem;
                        font-size: 1rem;
                    }
                    .spinner {
                        display: inline-block;
                        width: 24px;
                        height: 24px;
                        border: 3px solid #e5e7eb;
                        border-top-color: #667eea;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    }
                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }
                    .closing-text {
                        font-size: 0.875rem;
                        color: #9ca3af;
                        margin-top: 1rem;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">✅</div>
                    <h1>¡Autenticación Exitosa!</h1>
                    <p>Gmail ha sido autorizado correctamente.<br>Ya puedes ejecutar el proceso ETL.</p>
                    <div class="spinner"></div>
                    <p class="closing-text">Esta ventana se cerrará automáticamente...</p>
                </div>
                <script>
                    // Notificar a la ventana principal
                    if (window.opener) {
                        window.opener.postMessage({
                            type: 'GMAIL_AUTH_SUCCESS'
                        }, window.location.origin);
                    }

                    // Cerrar ventana después de 1.5 segundos
                    setTimeout(() => {
                        window.close();
                    }, 1500);
                </script>
            </body>
            </html>
        ''')

    except Exception as e:
        logger.error(f"Error in Gmail callback: {e}", exc_info=True)
        error_msg = str(e).replace("'", "\\'")
        return HttpResponse(f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Error de Autenticación</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                        background: #fee;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                        background: white;
                        border-radius: 0.5rem;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        max-width: 500px;
                    }}
                    .icon {{ font-size: 3rem; margin-bottom: 1rem; }}
                    h1 {{ color: #dc2626; font-size: 1.5rem; margin-bottom: 1rem; }}
                    .error-detail {{
                        background: #fef2f2;
                        padding: 1rem;
                        border-radius: 0.375rem;
                        color: #7f1d1d;
                        font-size: 0.875rem;
                        margin: 1rem 0;
                        font-family: monospace;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">❌</div>
                    <h1>Error al Autenticar</h1>
                    <div class="error-detail">{error_msg}</div>
                    <p style="color: #6b7280; font-size: 0.875rem;">Esta ventana se cerrará automáticamente...</p>
                </div>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'GMAIL_AUTH_ERROR',
                            message: '{error_msg}'
                        }}, window.location.origin);
                    }}
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
            </html>
        ''')


@api_view(['DELETE'])
@permission_classes([AllowAny])
def revoke_gmail_auth(request):
    """
    Revoca la autenticación de Gmail eliminando el token.
    DELETE /api/gmail/auth/revoke/
    """
    try:
        token_path = get_gmail_token_path(settings.BASE_DIR)
        if os.path.exists(token_path):
            os.remove(token_path)
            logger.info("🗑️ Gmail token revocado")
            return Response({
                'success': True,
                'message': 'Autenticación de Gmail revocada'
            })
        else:
            return Response({
                'success': True,
                'message': 'No había token para revocar'
            })

    except Exception as e:
        logger.error(f"Error revoking Gmail auth: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

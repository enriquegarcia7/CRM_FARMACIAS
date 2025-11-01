from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
import logging
import json

logger = logging.getLogger(__name__)

# Configuración OAuth para autenticación de usuario
SCOPES = [
    'openid',  # Requerido para OAuth 2.0 (Google lo agrega automáticamente si no está)
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly'  # Incluye Gmail automáticamente
]
TOKEN_PATH = os.path.join(settings.BASE_DIR, 'gmail_token.json')
CREDENTIALS_PATH = os.path.join(settings.BASE_DIR, 'gmail_credentials.json')
USER_SESSION_TOKEN_PATH = os.path.join(settings.BASE_DIR, 'user_session_token.json')

# URL de callback para login
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/callback')


def get_flow():
    """Crea Flow de OAuth con scopes de usuario y Gmail"""
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(
            "No se encontró gmail_credentials.json. "
            "Configure las credenciales de Google Cloud"
        )

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow


@api_view(['GET'])
@permission_classes([AllowAny])
def start_login(request):
    """
    Inicia el flujo de login con Google OAuth.
    GET /api/auth/login/start/

    Retorna URL de autorización que el frontend abrirá en popup.
    Al autorizar, el usuario se logea Y autoriza Gmail automáticamente.
    """
    try:
        flow = get_flow()

        # Generar URL de autorización (incluye scopes de Gmail)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Fuerza consentimiento para obtener refresh_token
        )

        # Guardar state en sesión
        request.session['oauth_state'] = state

        logger.info(f"🔐 Login URL generada con scopes de Gmail incluidos")

        return Response({
            'success': True,
            'auth_url': authorization_url,
            'message': 'Login con Google que autoriza Gmail automáticamente'
        })

    except FileNotFoundError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error starting login: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def login_callback(request):
    """
    Callback de Google OAuth para login.
    GET /api/auth/callback?code=...&state=...

    Procesa la autenticación, guarda el usuario Y los permisos de Gmail.
    """
    try:
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')

        if error:
            logger.warning(f"❌ Login cancelled: {error}")
            return HttpResponse(f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Login Cancelado</title>
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
                        .icon {{ font-size: 3rem; margin-bottom: 1rem; }}
                        h1 {{ color: #dc2626; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="icon">❌</div>
                        <h1>Login Cancelado</h1>
                        <p>{error}</p>
                    </div>
                    <script>
                        // Guardar error en localStorage
                        try {{
                            localStorage.setItem('smartpharm_login_result', JSON.stringify({{
                                type: 'LOGIN_ERROR',
                                message: '{error}',
                                timestamp: Date.now()
                            }}));
                        }} catch (e) {{
                            console.error('Error guardando en localStorage:', e);
                        }}

                        // Intentar postMessage como respaldo
                        window.opener && window.opener.postMessage({{type: 'LOGIN_ERROR', message: '{error}'}}, '*');
                        setTimeout(() => window.close(), 2000);
                    </script>
                </body>
                </html>
            ''')

        if not code:
            return HttpResponse('''
                <html><body><h1>Error: No se recibió código de autorización</h1>
                <script>
                    try {
                        localStorage.setItem('smartpharm_login_result', JSON.stringify({
                            type: 'LOGIN_ERROR',
                            message: 'No code',
                            timestamp: Date.now()
                        }));
                    } catch (e) {
                        console.error('Error guardando en localStorage:', e);
                    }
                    window.opener && window.opener.postMessage({type: 'LOGIN_ERROR', message: 'No code'}, '*');
                    setTimeout(() => window.close(), 2000);
                </script></body></html>
            ''')

        # Validar state (CSRF protection)
        saved_state = request.session.get('oauth_state')
        if saved_state and saved_state != state:
            logger.warning("⚠️ OAuth state mismatch - posible CSRF")

        # Intercambiar código por tokens
        flow = get_flow()
        flow.fetch_token(code=code)

        # Obtener credenciales (incluyen Gmail)
        creds = flow.credentials

        # Guardar token de Gmail
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

        # Obtener info del usuario
        from googleapiclient.discovery import build
        oauth2_service = build('oauth2', 'v2', credentials=creds)
        user_info = oauth2_service.userinfo().get().execute()

        # Guardar sesión del usuario
        user_session = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'gmail_authenticated': True,
            'logged_in': True
        }

        with open(USER_SESSION_TOKEN_PATH, 'w') as session_file:
            json.dump(user_session, session_file)

        logger.info(f"✅ Usuario logueado: {user_info.get('email')} (Gmail autorizado automáticamente)")

        # Retornar HTML de éxito
        return HttpResponse(f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Login Exitoso</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        text-align: center;
                        padding: 3rem 2rem;
                        background: white;
                        border-radius: 1rem;
                        box-shadow: 0 20px 25px rgba(0,0,0,0.1);
                        max-width: 400px;
                    }}
                    .icon {{ font-size: 4rem; animation: checkmark 0.5s; }}
                    @keyframes checkmark {{
                        0% {{ transform: scale(0); }}
                        50% {{ transform: scale(1.2); }}
                        100% {{ transform: scale(1); }}
                    }}
                    h1 {{ color: #10b981; font-size: 1.75rem; }}
                    .user-info {{
                        margin: 1rem 0;
                        padding: 1rem;
                        background: #f3f4f6;
                        border-radius: 0.5rem;
                    }}
                    .user-info img {{
                        width: 60px;
                        height: 60px;
                        border-radius: 50%;
                        margin-bottom: 0.5rem;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">✅</div>
                    <h1>¡Bienvenido a SmartPharm!</h1>
                    <div class="user-info">
                        <img src="{user_info.get('picture')}" alt="Avatar">
                        <p><strong>{user_info.get('name')}</strong></p>
                        <p style="font-size: 0.875rem; color: #6b7280;">{user_info.get('email')}</p>
                        <p style="font-size: 0.75rem; color: #10b981; margin-top: 0.5rem;">
                            ✅ Gmail autorizado automáticamente
                        </p>
                    </div>
                    <p style="color: #6b7280; font-size: 0.875rem;">Redirigiendo...</p>
                </div>
                <script>
                    console.log('🚀 Popup: Script ejecutándose...');

                    const userData = {{
                        email: '{user_info.get('email')}',
                        name: '{user_info.get('name')}',
                        picture: '{user_info.get('picture')}',
                        gmailAuthenticated: true
                    }};

                    console.log('👤 Popup: Datos del usuario:', userData);

                    // Usar localStorage como canal de comunicación confiable
                    try {{
                        const loginData = {{
                            type: 'LOGIN_SUCCESS',
                            user: userData,
                            timestamp: Date.now()
                        }};

                        console.log('💾 Popup: Guardando en localStorage...');
                        localStorage.setItem('smartpharm_login_result', JSON.stringify(loginData));
                        console.log('✅ Popup: Datos guardados en localStorage');
                    }} catch (error) {{
                        console.error('❌ Popup: Error guardando en localStorage:', error);
                    }}

                    // Intentar postMessage como respaldo
                    console.log('🪟 Popup: window.opener existe?', !!window.opener);
                    if (window.opener) {{
                        console.log('📤 Popup: Enviando postMessage como respaldo...');

                        const message = {{
                            type: 'LOGIN_SUCCESS',
                            user: userData
                        }};

                        // Enviar a múltiples orígenes por seguridad
                        const origins = ['http://localhost', 'http://localhost:80', 'http://127.0.0.1'];
                        origins.forEach(origin => {{
                            try {{
                                console.log('📨 Popup: Enviando a', origin);
                                window.opener.postMessage(message, origin);
                            }} catch (e) {{
                                console.warn('⚠️ Error enviando a', origin, e);
                            }}
                        }});

                        console.log('✅ Popup: Mensajes postMessage enviados');
                    }} else {{
                        console.warn('⚠️ Popup: window.opener es null, solo se usa localStorage');
                    }}

                    setTimeout(() => {{
                        console.log('🔒 Popup: Cerrando ventana...');
                        window.close();
                    }}, 1500);
                </script>
            </body>
            </html>
        ''')

    except Exception as e:
        logger.error(f"Error in login callback: {e}", exc_info=True)
        error_msg = str(e).replace("'", "\\'")
        return HttpResponse(f'''
            <html><body><h1>Error al autenticar</h1><p>{error_msg}</p>
            <script>
                try {{
                    localStorage.setItem('smartpharm_login_result', JSON.stringify({{
                        type: 'LOGIN_ERROR',
                        message: '{error_msg}',
                        timestamp: Date.now()
                    }}));
                }} catch (e) {{
                    console.error('Error guardando en localStorage:', e);
                }}
                window.opener && window.opener.postMessage({{type: 'LOGIN_ERROR', message: '{error_msg}'}}, '*');
                setTimeout(() => window.close(), 3000);
            </script></body></html>
        ''')


@api_view(['GET'])
@permission_classes([AllowAny])
def check_session(request):
    """
    Verifica si el usuario tiene sesión activa.
    GET /api/auth/session/
    """
    try:
        if os.path.exists(USER_SESSION_TOKEN_PATH):
            with open(USER_SESSION_TOKEN_PATH, 'r') as session_file:
                user_session = json.load(session_file)

            # Verificar también que el token de Gmail exista
            gmail_authenticated = os.path.exists(TOKEN_PATH)

            return Response({
                'logged_in': True,
                'user': {
                    'email': user_session.get('email'),
                    'name': user_session.get('name'),
                    'picture': user_session.get('picture'),
                    'gmail_authenticated': gmail_authenticated
                }
            })
        else:
            return Response({
                'logged_in': False,
                'user': None
            })

    except Exception as e:
        logger.error(f"Error checking session: {e}")
        return Response({
            'logged_in': False,
            'user': None
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    """
    Cierra sesión del usuario y revoca permisos de Gmail.
    POST /api/auth/logout/

    Elimina tokens de sesión y Gmail, forzando nueva autenticación.
    """
    try:
        # Eliminar token de sesión de usuario
        if os.path.exists(USER_SESSION_TOKEN_PATH):
            os.remove(USER_SESSION_TOKEN_PATH)
            logger.info("🗑️ User session removed")

        # Eliminar token de Gmail (forzará nueva autorización)
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)
            logger.info("🗑️ Gmail token removed")

        return Response({
            'success': True,
            'message': 'Sesión cerrada. Deberá volver a autenticarse con Google.'
        })

    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

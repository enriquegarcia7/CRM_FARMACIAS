import os
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.conf import settings
import logging
from config.secrets import get_gmail_token_path

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Configuración de validación
EXCLUDED_SENDERS = ['proyectosmartpharm2025@gmail.com']
TRUSTED_DOMAINS = ['mediven', 'socofar']  # Dominios confiables (sin @)

# Palabras clave (singular y plural, con y sin tildes)
KEYWORDS = [
    'precio', 'precios',
    'oferta', 'ofertas',
    'laboratorio', 'laboratorios',
    'promocion', 'promoción', 'promociones', 'promociónes',
    'lista', 'listas',
    'descuento', 'descuentos',
    'farmacia', 'farmacias'
]

class GmailService:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """
        Autentica con Gmail usando el token existente.
        Si no existe token o no es válido, lanza una excepción.
        El usuario debe autenticarse primero usando el flujo web OAuth.
        """
        token_path = get_gmail_token_path(settings.BASE_DIR)

        # Verificar si existe el token
        if not os.path.exists(token_path):
            logger.warning("Gmail token not found. User must authenticate first.")
            raise FileNotFoundError(
                "Gmail no está autenticado. "
                "Por favor, ve a la sección ETL y haz clic en 'Autenticar Gmail' para autorizar el acceso."
            )

        # Cargar credenciales desde el token
        self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Verificar si el token es válido o necesita refresh
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    logger.info("🔄 Refreshing Gmail token...")
                    self.creds.refresh(Request())

                    # Guardar el token actualizado
                    with open(token_path, 'w') as token:
                        token.write(self.creds.to_json())

                    logger.info("✅ Gmail token refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    # Si falla el refresh, solicitar re-autenticación
                    if os.path.exists(token_path):
                        os.remove(token_path)
                    raise Exception(
                        "Token expirado y no se pudo renovar. "
                        "Por favor, vuelve a autenticar Gmail desde la sección ETL."
                    )
            else:
                # Token inválido sin refresh_token
                logger.warning("Gmail token invalid and no refresh_token available")
                if os.path.exists(token_path):
                    os.remove(token_path)
                raise Exception(
                    "Token de Gmail inválido. "
                    "Por favor, vuelve a autenticar Gmail desde la sección ETL."
                )

        # Construir el servicio de Gmail
        self.service = build('gmail', 'v1', credentials=self.creds)
        logger.info("✅ Gmail authenticated successfully")

    def get_messages(self, query='has:attachment', max_results=50):
        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            messages = results.get('messages', [])
            logger.info(f"📧 Found {len(messages)} messages")
            return messages
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []

    def get_message_detail(self, message_id):
        try:
            return self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            return None

    def _extract_sender_email(self, sender_string):
        """Extrae el email del string 'From' que puede tener formato 'Name <email@domain.com>'"""
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender_string)
        return match.group(0).lower() if match else sender_string.lower()

    def _is_excluded_sender(self, sender):
        """Verifica si el remitente está en la lista de excluidos"""
        email = self._extract_sender_email(sender)
        return email in EXCLUDED_SENDERS

    def _is_trusted_domain(self, sender):
        """Verifica si el remitente es de un dominio confiable (Mediven, Socofar)"""
        email = self._extract_sender_email(sender)
        return any(domain in email for domain in TRUSTED_DOMAINS)

    def _contains_keywords(self, text):
        """Verifica si el texto contiene alguna palabra clave (case-insensitive)"""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in KEYWORDS)

    def _get_message_body(self, message):
        """Extrae el cuerpo del mensaje (texto plano o HTML)"""
        try:
            payload = message.get('payload', {})
            body = ''

            # Intentar obtener el cuerpo del mensaje
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' or part.get('mimeType') == 'text/html':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            else:
                # Mensaje simple sin partes
                data = payload.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

            return body
        except Exception as e:
            logger.error(f"Error extracting message body: {e}")
            return ''

    def _validate_message(self, message):
        """
        Valida si un mensaje cumple con los criterios:
        1. No debe ser enviado desde proyectosmartpharm2025@gmail.com
        2. Debe ser de dominio confiable (Mediven/Socofar) O contener palabras clave
        """
        try:
            headers = message['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')

            # 1. Excluir si es del remitente excluido
            if self._is_excluded_sender(sender):
                logger.debug(f"✗ Mensaje excluido por remitente: {sender}")
                return False

            # 2. Aceptar si es de dominio confiable
            if self._is_trusted_domain(sender):
                logger.info(f"✓ Mensaje aceptado por dominio confiable: {sender}")
                return True

            # 3. Validar palabras clave en asunto o cuerpo
            if self._contains_keywords(subject):
                logger.info(f"✓ Mensaje aceptado por palabra clave en asunto: {subject}")
                return True

            # Obtener cuerpo del mensaje
            body = self._get_message_body(message)
            if self._contains_keywords(body):
                logger.info(f"✓ Mensaje aceptado por palabra clave en cuerpo")
                return True

            # No cumple criterios
            logger.debug(f"✗ Mensaje rechazado - Sin palabras clave: {subject}")
            return False

        except Exception as e:
            logger.error(f"Error validating message: {e}")
            return False

    def get_attachments(self, message_id):
        attachments = []
        try:
            message = self.get_message_detail(message_id)
            if not message:
                return attachments

            headers = message['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')

            parts = message['payload'].get('parts', [])
            for part in parts:
                if part.get('filename'):
                    attachment_id = part['body'].get('attachmentId')
                    if attachment_id:
                        attachment = self.service.users().messages().attachments().get(
                            userId='me', messageId=message_id, id=attachment_id
                        ).execute()

                        file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

                        attachments.append({
                            'filename': part['filename'],
                            'mime_type': part['mimeType'],
                            'size': part['body'].get('size', 0),
                            'data': file_data,
                            'sender': sender,
                            'subject': subject,
                            'date': date,
                            'message_id': message_id
                        })

            logger.info(f"📎 Message {message_id}: {len(attachments)} attachments")
            return attachments
        except Exception as e:
            logger.error(f"Error getting attachments: {e}")
            return []

    def search_offers_emails(self, days_back=3, strict_mode=False):
        """
        Busca correos con ofertas de laboratorios con validación avanzada.

        Args:
            days_back: Número de días hacia atrás para buscar
            strict_mode: No usado actualmente (mantenido por compatibilidad)

        Validaciones aplicadas:
        1. Excluye correos de proyectosmartpharm2025@gmail.com
        2. Acepta correos de dominios Mediven y Socofar
        3. Valida palabras clave en asunto/cuerpo (precio, oferta, laboratorio, etc.)
        """
        # Buscar todos los correos con adjuntos Excel/PDF
        query = (
            f'has:attachment newer_than:{days_back}d '
            f'(filename:xlsx OR filename:xls OR filename:pdf OR filename:csv)'
        )
        logger.info(f"🔍 Searching emails with Excel/PDF attachments from last {days_back} days")

        # Obtener mensajes
        messages = self.get_messages(query=query)
        logger.info(f"📧 Found {len(messages)} messages with attachments")

        # Aplicar validaciones
        validated_messages = []
        for msg in messages:
            # Obtener detalles del mensaje para validación
            message_detail = self.get_message_detail(msg['id'])
            if message_detail and self._validate_message(message_detail):
                validated_messages.append(msg)

        logger.info(f"✅ {len(validated_messages)} messages passed validation")
        logger.info(f"❌ {len(messages) - len(validated_messages)} messages rejected")

        return validated_messages

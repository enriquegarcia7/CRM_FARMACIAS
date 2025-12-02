import os
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.conf import settings
import logging
from config.secrets import get_gmail_token_path, get_smtp_config, get_gmail_token_from_env

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']

# Configuración de validación
EXCLUDED_SENDERS = ['proyectosmartpharm2025@gmail.com']
TRUSTED_DOMAINS = ['mediven', 'socofar', 'provefarma']  # Dominios confiables (sin @)

# Palabras clave (singular y plural, con y sin tildes)
# Se buscan en asunto Y cuerpo del correo (case-insensitive)
KEYWORDS = [
    # Precios
    'precio', 'precios', 'tarifa', 'tarifas', 'costo', 'costos', 'valor', 'valores',
    # Ofertas y promociones
    'oferta', 'ofertas', 'promocion', 'promoción', 'promociones', 'promociónes',
    'rebaja', 'rebajas', 'especial', 'especiales',
    # Descuentos
    'descuento', 'descuentos', 'dto', 'dscto',
    # Listas y catálogos
    'lista', 'listas', 'catalogo', 'catálogo', 'catalogos', 'catálogos',
    'listado', 'listados',
    # Laboratorios
    'laboratorio', 'laboratorios', 'lab', 'labs',
    # Farmacias
    'farmacia', 'farmacias',
    # Stock y productos
    'stock', 'producto', 'productos', 'medicamento', 'medicamentos'
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

    def _extract_attachments_recursive(self, parts, message_id, depth=0):
        """
        Extrae adjuntos de forma recursiva de todas las partes del mensaje.
        Algunos correos tienen adjuntos en partes anidadas (multipart/mixed, multipart/alternative).

        Args:
            parts: Lista de partes del mensaje
            message_id: ID del mensaje
            depth: Profundidad de recursión (para evitar loops infinitos)

        Returns:
            Lista de diccionarios con información de adjuntos
        """
        attachments = []

        if depth > 10:  # Límite de seguridad
            logger.warning(f"Max recursion depth reached for message {message_id}")
            return attachments

        for part in parts:
            # Si la parte tiene nombre de archivo, es un adjunto
            filename = part.get('filename')
            if filename:
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    try:
                        attachment = self.service.users().messages().attachments().get(
                            userId='me', messageId=message_id, id=attachment_id
                        ).execute()

                        file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

                        attachments.append({
                            'filename': filename,
                            'mime_type': part.get('mimeType', 'unknown'),
                            'size': part['body'].get('size', len(file_data)),
                            'data': file_data,
                        })
                        logger.debug(f"  ✓ Found attachment: {filename} ({part.get('mimeType')})")
                    except Exception as e:
                        logger.error(f"  ✗ Error downloading attachment {filename}: {e}")

            # Si la parte tiene subpartes, buscar recursivamente
            if 'parts' in part:
                nested_attachments = self._extract_attachments_recursive(
                    part['parts'], message_id, depth + 1
                )
                attachments.extend(nested_attachments)

        return attachments

    def get_attachments(self, message_id):
        """
        Obtiene todos los adjuntos de un mensaje de forma recursiva.
        Maneja correctamente correos con estructura multipart anidada.
        """
        attachments = []
        try:
            message = self.get_message_detail(message_id)
            if not message:
                logger.warning(f"Could not get message detail for {message_id}")
                return attachments

            headers = message['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')

            logger.info(f"📧 Extracting attachments from: {subject[:50]}...")
            logger.debug(f"   From: {sender}")
            logger.debug(f"   Date: {date}")

            # Buscar adjuntos en el payload (puede tener 'parts' o ser un mensaje simple)
            payload = message.get('payload', {})

            # Caso 1: Mensaje con partes (multipart)
            if 'parts' in payload:
                attachments_list = self._extract_attachments_recursive(
                    payload['parts'], message_id
                )
            else:
                # Caso 2: Mensaje simple (raro que tenga adjuntos, pero se maneja)
                attachments_list = []
                if payload.get('filename'):
                    attachment_id = payload['body'].get('attachmentId')
                    if attachment_id:
                        try:
                            attachment = self.service.users().messages().attachments().get(
                                userId='me', messageId=message_id, id=attachment_id
                            ).execute()
                            file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                            attachments_list.append({
                                'filename': payload['filename'],
                                'mime_type': payload.get('mimeType', 'unknown'),
                                'size': payload['body'].get('size', len(file_data)),
                                'data': file_data,
                            })
                        except Exception as e:
                            logger.error(f"Error downloading attachment: {e}")

            # Agregar metadatos a cada adjunto
            for att in attachments_list:
                att.update({
                    'sender': sender,
                    'subject': subject,
                    'date': date,
                    'message_id': message_id
                })
                attachments.append(att)

            if attachments:
                logger.info(f"📎 Found {len(attachments)} attachment(s) in message {message_id[:10]}...")
                for att in attachments:
                    logger.info(f"   - {att['filename']} ({att['size']} bytes, {att['mime_type']})")
            else:
                logger.warning(f"⚠️ No attachments found in message {message_id[:10]}...")

            return attachments

        except Exception as e:
            logger.error(f"❌ Error getting attachments from {message_id}: {e}", exc_info=True)
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
        logger.info(f"🔍 Query: {query}")

        # Obtener mensajes
        messages = self.get_messages(query=query)
        logger.info(f"📧 Found {len(messages)} total message(s) with attachments")

        if not messages:
            logger.warning("⚠️ No messages found matching search criteria")
            return []

        # Aplicar validaciones
        validated_messages = []
        rejected_by_sender = 0
        rejected_no_keywords = 0

        for idx, msg in enumerate(messages, 1):
            logger.info(f"\n--- Validating message {idx}/{len(messages)} (ID: {msg['id'][:10]}...) ---")

            # Obtener detalles del mensaje para validación
            message_detail = self.get_message_detail(msg['id'])
            if not message_detail:
                logger.error(f"❌ Could not get message detail for {msg['id']}")
                continue

            # Extraer información básica
            headers = message_detail['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')

            logger.info(f"  From: {sender}")
            logger.info(f"  Subject: {subject[:80]}...")

            # Validar
            if self._validate_message(message_detail):
                validated_messages.append(msg)
                logger.info(f"  ✅ Message ACCEPTED")
            else:
                # Determinar razón del rechazo
                if self._is_excluded_sender(sender):
                    rejected_by_sender += 1
                    logger.info(f"  ❌ Message REJECTED: Excluded sender")
                else:
                    rejected_no_keywords += 1
                    logger.info(f"  ❌ Message REJECTED: Not trusted domain and no keywords found")

        logger.info(f"\n{'='*60}")
        logger.info(f"📊 VALIDATION SUMMARY:")
        logger.info(f"  Total found: {len(messages)}")
        logger.info(f"  ✅ Accepted: {len(validated_messages)}")
        logger.info(f"  ❌ Rejected: {len(messages) - len(validated_messages)}")
        logger.info(f"    - By excluded sender: {rejected_by_sender}")
        logger.info(f"    - No keywords/trusted domain: {rejected_no_keywords}")
        logger.info(f"{'='*60}\n")

        return validated_messages

    def get_diagnostic_info(self, days_back=3):
        """
        Obtiene información detallada de diagnóstico de todos los correos encontrados.
        NO procesa los correos, solo obtiene información para diagnóstico.

        Returns:
            dict: Información detallada de cada correo (validación, adjuntos, etc.)
        """
        query = (
            f'has:attachment newer_than:{days_back}d '
            f'(filename:xlsx OR filename:xls OR filename:pdf OR filename:csv)'
        )

        messages = self.get_messages(query=query)
        diagnostic_data = {
            'total_found': len(messages),
            'search_query': query,
            'days_back': days_back,
            'messages': []
        }

        for msg in messages:
            message_detail = self.get_message_detail(msg['id'])
            if not message_detail:
                continue

            headers = message_detail['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')

            # Validación
            passes_validation = self._validate_message(message_detail)
            is_excluded = self._is_excluded_sender(sender)
            is_trusted = self._is_trusted_domain(sender)
            has_keywords = self._contains_keywords(subject)

            # Contar adjuntos (sin descargarlos)
            payload = message_detail.get('payload', {})
            attachment_count = self._count_attachments_recursive(payload.get('parts', []))

            diagnostic_data['messages'].append({
                'id': msg['id'],
                'sender': sender,
                'subject': subject,
                'date': date,
                'validation': {
                    'passes': passes_validation,
                    'is_excluded': is_excluded,
                    'is_trusted_domain': is_trusted,
                    'has_keywords': has_keywords,
                },
                'attachment_count': attachment_count
            })

        return diagnostic_data

    def _count_attachments_recursive(self, parts, depth=0):
        """
        Cuenta adjuntos de forma recursiva sin descargarlos.
        """
        if not parts or depth > 10:
            return 0

        count = 0
        for part in parts:
            if part.get('filename'):
                count += 1
            if 'parts' in part:
                count += self._count_attachments_recursive(part['parts'], depth + 1)

        return count

    def send_email(self, to_email, subject, body_html):
        """
        Envía un correo electrónico usando SMTP con contraseña de aplicación.

        Las credenciales se leen desde variables de entorno:
            - SMTP_EMAIL: Correo de Gmail
            - SMTP_APP_PASSWORD: Contraseña de aplicación (16 caracteres)
            - SMTP_SERVER: Servidor (default: smtp.gmail.com)
            - SMTP_PORT: Puerto (default: 587)

        Args:
            to_email: Dirección de correo del destinatario
            subject: Asunto del correo
            body_html: Cuerpo del correo en formato HTML

        Returns:
            dict: Información del mensaje enviado o None si falla
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Obtener configuración SMTP desde variables de entorno
            smtp_config = get_smtp_config()

            # Crear mensaje MIME
            message = MIMEMultipart('alternative')
            message['From'] = f'SmartPharm <{smtp_config["email"]}>'
            message['To'] = to_email
            message['Subject'] = subject

            # Agregar cuerpo HTML
            html_part = MIMEText(body_html, 'html', 'utf-8')
            message.attach(html_part)

            # Enviar usando SMTP
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                server.starttls()
                server.login(smtp_config['email'], smtp_config['app_password'])
                server.send_message(message)

            logger.info(f"✅ Correo enviado exitosamente a {to_email} via SMTP")
            return {'id': 'smtp_success', 'to': to_email}

        except ValueError as e:
            # Error de configuración (faltan variables de entorno)
            logger.error(f"❌ Error de configuración SMTP: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error enviando correo a {to_email}: {e}", exc_info=True)
            return None

    def _formato_moneda_chilena(self, valor):
        """
        Formatea un valor numérico al formato de moneda chilena.
        Ejemplo: 15000 -> "$15.000"
        """
        if valor is None or valor == 0:
            return "$0"
        # Formatear con puntos como separadores de miles
        valor_int = int(round(valor))
        valor_str = f"{valor_int:,}".replace(",", ".")
        return f"${valor_str}"

    def send_offer_email(self, cliente_nombre, cliente_email, productos, descuento_porcentaje):
        """
        Envía un correo de oferta personalizado a un cliente.

        Args:
            cliente_nombre: Nombre del cliente
            cliente_email: Email del cliente
            productos: Lista de productos (dict con 'nombre' y 'precio') o lista de strings (legacy)
            descuento_porcentaje: Porcentaje de descuento a aplicar (3, 5, 10, 15, 20)

        Returns:
            dict: Resultado del envío
        """
        import random
        import string

        # Generar código único de 8 dígitos
        codigo_descuento = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        # Construir tabla de productos con comparativa de precios
        productos_html = ""

        # Verificar si productos es una lista de dicts (nuevo formato) o strings (legacy)
        if productos and isinstance(productos[0], dict):
            # Nuevo formato con precios
            productos_html = """
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <thead>
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Producto</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid #e5e7eb;">Precio Normal</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid #e5e7eb;">Precio Oferta</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid #e5e7eb;">Ahorro</th>
                    </tr>
                </thead>
                <tbody>
            """

            for producto in productos:
                nombre = producto.get('nombre', 'Producto')
                precio = producto.get('precio', 0)
                precio_oferta = precio * (1 - descuento_porcentaje / 100)
                ahorro = precio - precio_oferta

                precio_fmt = self._formato_moneda_chilena(precio)
                precio_oferta_fmt = self._formato_moneda_chilena(precio_oferta)
                ahorro_fmt = self._formato_moneda_chilena(ahorro)

                productos_html += f"""
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{nombre}</td>
                        <td style="padding: 12px; text-align: right; border-bottom: 1px solid #e5e7eb; text-decoration: line-through; color: #9ca3af;">{precio_fmt}</td>
                        <td style="padding: 12px; text-align: right; border-bottom: 1px solid #e5e7eb; color: #10b981; font-weight: bold;">{precio_oferta_fmt}</td>
                        <td style="padding: 12px; text-align: right; border-bottom: 1px solid #e5e7eb; color: #ef4444; font-weight: bold;">-{ahorro_fmt}</td>
                    </tr>
                """

            productos_html += """
                </tbody>
            </table>
            """
        else:
            # Legacy: lista de strings
            productos_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
            for producto in productos:
                productos_html += f"<li>{producto}</li>"
            productos_html += "</ul>"

        if not productos:
            productos_html = "<p>Productos de su preferencia</p>"

        # Plantilla HTML del correo
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9fafb;
                    padding: 30px;
                    border: 1px solid #e5e7eb;
                }}
                .discount {{
                    background: #10b981;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .discount-code {{
                    font-size: 14px;
                    margin-top: 10px;
                    letter-spacing: 2px;
                }}
                .products {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                    overflow-x: auto;
                }}
                .footer {{
                    background: #1f2937;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 0 0 10px 10px;
                }}
                .highlight {{
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 10px 15px;
                    margin: 15px 0;
                    border-radius: 0 8px 8px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>SmartPharm</h1>
                <p>Tu farmacia de confianza</p>
            </div>
            <div class="content">
                <p>Estimado Cliente <strong>{cliente_nombre}</strong>,</p>

                <p>Gracias por su preferencia. Enviamos Oferta por los siguientes productos:</p>

                <div class="products">
                    {productos_html}
                </div>

                <div class="highlight">
                    <strong>¡Aproveche esta oferta exclusiva!</strong> Los precios con descuento son válidos presentando el código de descuento.
                </div>

                <div class="discount">
                    {descuento_porcentaje}% DE DESCUENTO
                    <div class="discount-code">Código: {codigo_descuento}</div>
                </div>

                <p>Esta oferta es exclusiva para usted como cliente frecuente.
                   Visite nuestra farmacia para aprovechar este descuento especial.</p>
            </div>
            <div class="footer">
                <p><strong>Gracias</strong></p>
                <p>Equipo de SmartPharm</p>
            </div>
        </body>
        </html>
        """

        subject = f"Oferta Especial para ti - {descuento_porcentaje}% de Descuento | SmartPharm"

        result = self.send_email(cliente_email, subject, body_html)
        if result:
            result['codigo_descuento'] = codigo_descuento
        return result

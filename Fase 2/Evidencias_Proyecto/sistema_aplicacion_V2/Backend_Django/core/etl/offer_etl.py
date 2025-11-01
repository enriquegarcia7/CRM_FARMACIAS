import os
import json
import logging
from datetime import datetime
from django.db import transaction
from django.conf import settings
from core.services.gmail_service import GmailService
from core.parsers.excel_parser import ExcelOfferParser
from core.parsers.pdf_parser import PDFOfferParser
from core.models import OfertaLaboratorio, Producto, Proveedor, ETLLog

logger = logging.getLogger(__name__)

class OfferETL:
    def __init__(self):
        self.gmail_service = None
        self.stats = {
            'emails_processed': 0,
            'attachments_downloaded': 0,
            'offers_extracted': 0,
            'offers_inserted': 0,
            'offers_updated': 0,
            'errors': []
        }
        self.progress_file = os.path.join(settings.BASE_DIR, 'etl_progress.json')
        self.total_messages = 0
        self.current_message = 0

    def _update_progress(self, percentage, stage, message=''):
        """Actualiza el archivo de progreso del ETL"""
        try:
            progress_data = {
                'percentage': round(percentage, 1),
                'stage': stage,
                'message': message,
                'stats': self.stats.copy(),
                'timestamp': datetime.now().isoformat()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f)
            logger.info(f"Progress: {percentage:.1f}% - {stage} - {message}")
        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def run(self, days_back=5, strict_mode=False):
        logger.info(f"=== Starting ETL (last {days_back} days, strict_mode={strict_mode}) ===")
        start_time = datetime.now()

        try:
            # Inicializar progreso
            self._update_progress(0, 'iniciando', 'Iniciando proceso ETL...')

            # Borrar todas las ofertas existentes antes de cargar nuevas
            self._update_progress(5, 'limpiando', 'Eliminando ofertas antiguas...')
            deleted_count = OfertaLaboratorio.objects.all().count()
            OfertaLaboratorio.objects.all().delete()
            logger.info(f"🗑️ Deleted {deleted_count} old offers from database")

            # Conectar a Gmail
            self._update_progress(10, 'conectando', 'Conectando a Gmail...')
            self.gmail_service = GmailService()

            # Buscar mensajes
            mode_text = "específicos" if strict_mode else "con archivos Excel/PDF"
            self._update_progress(15, 'buscando', f'Buscando correos {mode_text}...')
            messages = self.gmail_service.search_offers_emails(days_back=days_back, strict_mode=strict_mode)

            if not messages:
                logger.warning("No messages found")
                self._update_progress(100, 'completado', 'No se encontraron mensajes')
                self._save_log(start_time, True)
                return self.stats

            self.total_messages = len(messages)
            logger.info(f"Found {self.total_messages} messages")
            self._update_progress(20, 'procesando', f'Procesando {self.total_messages} correos...')

            # Procesar mensajes (20% - 90% del progreso)
            for idx, message in enumerate(messages):
                self.current_message = idx + 1
                # Calcular progreso entre 20% y 90%
                progress = 20 + (70 * (idx + 1) / self.total_messages)
                self._update_progress(
                    progress,
                    'procesando',
                    f'Procesando correo {self.current_message}/{self.total_messages}'
                )
                self._process_message(message['id'])

            # Finalizar
            self._update_progress(95, 'finalizando', 'Guardando resultados...')

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"=== ETL Completed in {duration:.2f}s ===")
            logger.info(f"Emails: {self.stats['emails_processed']}")
            logger.info(f"Attachments: {self.stats['attachments_downloaded']}")
            logger.info(f"Offers extracted: {self.stats['offers_extracted']}")
            logger.info(f"Offers inserted: {self.stats['offers_inserted']}")
            logger.info(f"Offers updated: {self.stats['offers_updated']}")
            logger.info(f"Errors: {len(self.stats['errors'])}")

            self._save_log(start_time, True)

            # Progreso completo
            self._update_progress(
                100,
                'completado',
                f'ETL completado: {self.stats["offers_inserted"]} ofertas insertadas'
            )

            return self.stats

        except Exception as e:
            logger.error(f"Critical ETL error: {e}", exc_info=True)
            self.stats['errors'].append(f"Critical: {str(e)}")
            self._update_progress(0, 'error', f'Error: {str(e)}')
            self._save_log(start_time, False)
            return self.stats

    def _process_message(self, message_id):
        try:
            logger.info(f"Processing message {message_id}")
            attachments = self.gmail_service.get_attachments(message_id)

            if not attachments:
                return

            self.stats['emails_processed'] += 1

            for attachment in attachments:
                self._process_attachment(attachment)

        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}")
            self.stats['errors'].append(f"Message {message_id}: {str(e)}")

    def _process_attachment(self, attachment):
        filename = attachment['filename']
        file_data = attachment['data']

        try:
            if not self._is_valid_extension(filename):
                return

            logger.info(f"Processing: {filename}")
            self.stats['attachments_downloaded'] += 1

            offers = self._parse_file(filename, file_data, attachment)

            if not offers:
                logger.warning(f"No offers from {filename}")
                return

            self.stats['offers_extracted'] += len(offers)
            self._load_offers(offers)

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            self.stats['errors'].append(f"{filename}: {str(e)}")

    def _is_valid_extension(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        valid = ['.xlsx', '.xls', '.csv', '.pdf']
        return ext in valid

    def _parse_file(self, filename, file_data, metadata):
        ext = os.path.splitext(filename)[1].lower()

        if ext in ['.xlsx', '.xls', '.csv']:
            parser = ExcelOfferParser(file_data, filename, metadata)
        elif ext == '.pdf':
            parser = PDFOfferParser(file_data, filename, metadata)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return parser.parse()

    @transaction.atomic
    def _load_offers(self, offers):
        for offer_data in offers:
            try:
                proveedor, _ = Proveedor.objects.get_or_create(
                    nombre=offer_data['laboratorio'],
                    defaults={
                        'email': f"{offer_data['laboratorio'].lower().replace(' ', '')}@lab.cl",
                        'telefono': '+56900000000',
                        'direccion': 'Por confirmar'
                    }
                )

                producto = self._get_or_create_producto(offer_data, proveedor)

                # Crear nueva oferta (ya borramos todas las antiguas al inicio)
                oferta = OfertaLaboratorio.objects.create(
                    producto=producto,
                    laboratorio=offer_data['laboratorio'],
                    precio_normal=offer_data['precio_normal'],
                    precio_oferta=offer_data['precio_oferta'],
                    descuento=offer_data['descuento'],
                    fecha_inicio=offer_data['fecha_inicio'],
                    fecha_fin=offer_data['fecha_fin'],
                    activa=offer_data['activa'],
                )

                self.stats['offers_inserted'] += 1
                logger.info(f"✓ Created: {producto.nombre} - {offer_data['laboratorio']}")

            except Exception as e:
                logger.error(f"Error inserting offer: {e}")
                self.stats['errors'].append(f"Offer {offer_data.get('producto', 'Unknown')}: {str(e)}")
                continue

    def _get_or_create_producto(self, offer_data, proveedor):
        if offer_data.get('codigo'):
            try:
                return Producto.objects.get(codigo=offer_data['codigo'])
            except Producto.DoesNotExist:
                pass

        producto_nombre = offer_data['producto']
        try:
            return Producto.objects.get(nombre__iexact=producto_nombre)
        except Producto.DoesNotExist:
            pass

        producto = Producto.objects.create(
            codigo=offer_data.get('codigo') or f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            nombre=producto_nombre,
            descripcion=f"From {offer_data.get('source_file', 'email')}",
            categoria='Medicamento',
            stock_actual=0,
            stock_minimo=10,
            precio_unitario=offer_data['precio_normal'],
            proveedor=proveedor
        )

        logger.info(f"→ Created product: {producto.nombre}")
        return producto

    def _save_log(self, start_time, exitoso):
        try:
            duration = (datetime.now() - start_time).total_seconds()
            ETLLog.objects.create(
                emails_procesados=self.stats['emails_processed'],
                adjuntos_descargados=self.stats['attachments_downloaded'],
                ofertas_extraidas=self.stats['offers_extracted'],
                ofertas_insertadas=self.stats['offers_inserted'],
                ofertas_actualizadas=self.stats['offers_updated'],
                errores='\n'.join(self.stats['errors']),
                duracion_segundos=duration,
                exitoso=exitoso
            )
        except Exception as e:
            logger.error(f"Error saving ETL log: {e}")

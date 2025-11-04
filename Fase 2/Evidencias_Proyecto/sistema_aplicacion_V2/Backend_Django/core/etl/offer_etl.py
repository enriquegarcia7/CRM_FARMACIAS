import os
import json
import logging
import hashlib
from datetime import datetime
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from core.services.gmail_service import GmailService
from core.parsers.excel_parser import ExcelOfferParser
from core.parsers.pdf_parser import PDFOfferParser
from core.models import (
    OfertaLaboratorio, Producto, ProductoCatalogo, Proveedor,
    Laboratorio, Categoria, ETLLog, ArchivoProcesado
)

logger = logging.getLogger(__name__)

class OfferETL:
    def __init__(self):
        self.gmail_service = None
        self.stats = {
            'emails_found': 0,  # Total de correos encontrados por Gmail
            'emails_validated': 0,  # Correos que pasaron validación
            'emails_processed': 0,  # Correos que se procesaron (tenían adjuntos)
            'attachments_found': 0,  # Total de adjuntos encontrados
            'attachments_downloaded': 0,  # Adjuntos descargados y procesados
            'attachments_skipped': 0,  # Adjuntos saltados (duplicados)
            'attachments_failed': 0,  # Adjuntos que fallaron al procesar
            'offers_extracted': 0,
            'offers_inserted': 0,
            'offers_updated': 0,
            'offers_kept': 0,  # Ofertas existentes que se mantuvieron (mejor precio)
            'errors': [],
            'warnings': []
        }
        self.progress_file = os.path.join(settings.BASE_DIR, 'etl_progress.json')
        self.total_messages = 0
        self.current_message = 0
        self.etl_log = None  # Para vincular archivos procesados

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

            # Crear registro ETL antes de procesar (para vincular archivos)
            self.etl_log = ETLLog.objects.create(exitoso=False)

            # Nota: Ya NO eliminamos ofertas al inicio
            # La lógica inteligente de _load_offers() se encarga de:
            # - Mantener ofertas vigentes si no hay mejores
            # - Reemplazar ofertas vencidas siempre
            # - Reemplazar ofertas vigentes solo si la nueva es mejor
            self._update_progress(5, 'preparando', 'Preparando proceso ETL...')
            logger.info("📋 Usando lógica inteligente de actualización (mantener vigentes, reemplazar si hay mejoras)")

            # Conectar a Gmail
            self._update_progress(10, 'conectando', 'Conectando a Gmail...')
            self.gmail_service = GmailService()

            # Buscar mensajes
            mode_text = "específicos" if strict_mode else "con archivos Excel/PDF"
            self._update_progress(15, 'buscando', f'Buscando correos {mode_text}...')

            logger.info("="*80)
            logger.info("FASE 1: BÚSQUEDA Y VALIDACIÓN DE CORREOS")
            logger.info("="*80)

            messages = self.gmail_service.search_offers_emails(days_back=days_back, strict_mode=strict_mode)

            self.stats['emails_validated'] = len(messages)

            if not messages:
                logger.warning("⚠️ No messages found or all messages rejected by validation")
                self._update_progress(100, 'completado', 'No se encontraron mensajes válidos')
                self._save_log(start_time, True)
                return self.stats

            self.total_messages = len(messages)
            logger.info(f"\n✅ {self.total_messages} mensaje(s) pasó validación")
            logger.info("="*80)
            logger.info("FASE 2: PROCESAMIENTO DE MENSAJES Y ADJUNTOS")
            logger.info("="*80)

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

            logger.info("\n" + "="*80)
            logger.info("RESUMEN FINAL DEL ETL")
            logger.info("="*80)
            logger.info(f"⏱️  Duración: {duration:.2f} segundos")
            logger.info(f"\n📧 CORREOS:")
            logger.info(f"  - Validados: {self.stats['emails_validated']}")
            logger.info(f"  - Procesados (con adjuntos): {self.stats['emails_processed']}")
            logger.info(f"\n📎 ADJUNTOS:")
            logger.info(f"  - Encontrados: {self.stats['attachments_found']}")
            logger.info(f"  - Procesados: {self.stats['attachments_downloaded']}")
            logger.info(f"  - Saltados (duplicados): {self.stats['attachments_skipped']}")
            logger.info(f"  - Fallidos: {self.stats['attachments_failed']}")
            logger.info(f"\n💰 OFERTAS:")
            logger.info(f"  - Extraídas: {self.stats['offers_extracted']}")
            logger.info(f"  - Nuevas (insertadas): {self.stats['offers_inserted']}")
            logger.info(f"  - Actualizadas (mejoradas): {self.stats['offers_updated']}")
            logger.info(f"  - Mantenidas (mejor existente): {self.stats['offers_kept']}")
            logger.info(f"\n⚠️  ERRORES Y ADVERTENCIAS:")
            logger.info(f"  - Errores: {len(self.stats['errors'])}")
            logger.info(f"  - Advertencias: {len(self.stats['warnings'])}")

            if self.stats['errors']:
                logger.error(f"\n❌ ERRORES DETECTADOS:")
                for err in self.stats['errors'][:10]:  # Mostrar max 10
                    logger.error(f"  - {err}")
                if len(self.stats['errors']) > 10:
                    logger.error(f"  ... y {len(self.stats['errors']) - 10} errores más")

            logger.info("="*80 + "\n")

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
            logger.info(f"\n📧 Processing message {message_id[:15]}...")
            attachments = self.gmail_service.get_attachments(message_id)

            self.stats['attachments_found'] += len(attachments)

            if not attachments:
                logger.warning(f"⚠️ No attachments found in message {message_id[:15]}")
                self.stats['warnings'].append(f"No attachments in message {message_id[:15]}")
                return

            logger.info(f"📎 Found {len(attachments)} attachment(s) in this message")
            self.stats['emails_processed'] += 1

            for idx, attachment in enumerate(attachments, 1):
                logger.info(f"\n  --- Processing attachment {idx}/{len(attachments)} ---")
                self._process_attachment(attachment)

        except Exception as e:
            logger.error(f"❌ Error processing message {message_id}: {e}", exc_info=True)
            self.stats['errors'].append(f"Message {message_id[:15]}: {str(e)}")

    def _calculate_hash(self, file_data):
        """Calcula SHA256 hash del contenido del archivo"""
        return hashlib.sha256(file_data).hexdigest()

    def _is_file_processed(self, file_hash):
        """Verifica si el archivo ya fue procesado anteriormente"""
        # Buscar en los últimos 30 días para no buscar en toda la historia
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        return ArchivoProcesado.objects.filter(
            hash_archivo=file_hash,
            fecha_procesamiento__gte=thirty_days_ago
        ).exists()

    def _process_attachment(self, attachment):
        filename = attachment['filename']
        file_data = attachment['data']

        try:
            logger.info(f"  📄 File: {filename} ({len(file_data)} bytes)")

            if not self._is_valid_extension(filename):
                logger.info(f"  ⏭️ SKIPPED: Invalid extension")
                return

            # Calcular hash del archivo
            file_hash = self._calculate_hash(file_data)
            file_size = len(file_data)

            logger.info(f"  🔑 Hash: {file_hash[:16]}...")

            # Verificar si ya fue procesado
            if self._is_file_processed(file_hash):
                logger.info(f"  ⏭️ SKIPPED: Already processed (duplicate)")
                self.stats['attachments_skipped'] += 1
                return

            logger.info(f"  ⚙️ Processing attachment...")
            self.stats['attachments_downloaded'] += 1

            offers = self._parse_file(filename, file_data, attachment)

            if not offers:
                logger.warning(f"  ⚠️ No offers extracted from {filename}")
                # Aún así registrar que se procesó para no reintentar
                self._register_processed_file(filename, file_hash, file_size, 0, attachment)
                return

            logger.info(f"  ✅ Extracted {len(offers)} offers from {filename}")
            self.stats['offers_extracted'] += len(offers)

            # Registrar archivo Y cargar ofertas en la MISMA transacción
            self._load_offers_and_register(offers, filename, file_hash, file_size, attachment)

        except Exception as e:
            logger.error(f"  ❌ Error processing {filename}: {e}", exc_info=True)
            self.stats['errors'].append(f"{filename}: {str(e)}")
            self.stats['attachments_failed'] += 1

    def _register_processed_file(self, filename, file_hash, file_size, offers_count, metadata):
        """Registra el archivo procesado para evitar reprocesamiento"""
        try:
            ArchivoProcesado.objects.create(
                etl_log=self.etl_log,
                nombre_archivo=filename,
                hash_archivo=file_hash,
                tamano_bytes=file_size,
                ofertas_extraidas=offers_count,
                email_id=metadata.get('message_id', ''),
                email_subject=metadata.get('subject', '')[:500]
            )
            logger.info(f"✓ Registered: {filename} ({offers_count} offers)")
        except Exception as e:
            logger.warning(f"Could not register file {filename}: {e}")

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
    def _load_offers_and_register(self, offers, filename, file_hash, file_size, metadata):
        """
        Carga ofertas Y registra el archivo procesado en una SOLA transacción atómica.
        Si falla alguna oferta, se hace rollback de TODO incluyendo el registro del archivo.
        """
        # Cargar ofertas
        self._load_offers(offers)

        # Registrar archivo procesado (dentro de la misma transacción)
        ArchivoProcesado.objects.create(
            etl_log=self.etl_log,
            nombre_archivo=filename,
            hash_archivo=file_hash,
            tamano_bytes=file_size,
            ofertas_extraidas=len(offers),
            email_id=metadata.get('message_id', ''),
            email_subject=metadata.get('subject', '')[:500]
        )
        logger.info(f"✓ Archivo registrado: {filename} ({len(offers)} ofertas)")

    def _load_offers(self, offers):
        """
        Carga ofertas con lógica inteligente anti-duplicados usando ProductoCatalogo y Laboratorio.
        NOTA: Este método NO tiene @transaction.atomic porque es llamado desde _load_offers_and_register

        Para cada nueva oferta:
        1. Obtener/Crear Proveedor (quien envía el correo)
        2. Obtener/Crear Laboratorio (fabricante del producto)
        3. Obtener/Crear ProductoCatalogo (producto en catálogo de proveedor)
        4. Buscar oferta existente del mismo producto_catalogo + laboratorio
        5. Aplicar lógica de reemplazo (vigente/vencida/mejor precio)
        """
        today = timezone.now().date()

        for offer_data in offers:
            try:
                # 1. Obtener o crear PROVEEDOR (quien envía el archivo: Mediven, Socofar, etc.)
                proveedor, _ = Proveedor.objects.get_or_create(
                    nombre=offer_data.get('proveedor', 'Proveedor Desconocido'),
                    defaults={
                        'email': f"{offer_data.get('proveedor', 'proveedor').lower().replace(' ', '')}@proveedor.cl",
                        'telefono': '+56900000000',
                        'direccion': 'Por confirmar'
                    }
                )

                # 2. Obtener o crear LABORATORIO (fabricante)
                laboratorio, _ = Laboratorio.objects.get_or_create(
                    nombre=offer_data.get('laboratorio', 'Sin Laboratorio'),
                    defaults={
                        'activo': True
                    }
                )

                # 3. Obtener o crear PRODUCTO en CATÁLOGO
                producto_catalogo = self._get_or_create_producto_catalogo(offer_data, proveedor)

                # 4. Buscar oferta existente del mismo producto_catalogo + laboratorio
                oferta_existente = OfertaLaboratorio.objects.filter(
                    producto_catalogo=producto_catalogo,
                    laboratorio=laboratorio,
                    activa=True
                ).first()

                # Precios de la nueva oferta
                nuevo_precio = offer_data['precio_oferta'] if offer_data['precio_oferta'] > 0 else offer_data['precio_normal']
                nuevo_descuento = offer_data['descuento']

                if oferta_existente:
                    # Verificar si la oferta existente está vigente
                    esta_vigente = oferta_existente.fecha_fin >= today

                    if esta_vigente:
                        # Oferta VIGENTE: solo reemplazar si la nueva es mejor
                        precio_existente = oferta_existente.precio_oferta if oferta_existente.precio_oferta > 0 else oferta_existente.precio_normal
                        descuento_existente = oferta_existente.descuento

                        # Comparar: ¿la nueva es mejor?
                        precio_mejor = nuevo_precio < precio_existente
                        descuento_mejor = nuevo_descuento > descuento_existente

                        if precio_mejor or descuento_mejor:
                            # La nueva oferta es mejor, reemplazar
                            logger.info(f"🔄 Actualizando oferta vigente mejorada: {producto_catalogo.nombre}")
                            logger.info(f"   Antes: ${precio_existente} ({descuento_existente}% desc)")
                            logger.info(f"   Ahora: ${nuevo_precio} ({nuevo_descuento}% desc)")

                            # Eliminar la antigua
                            oferta_existente.delete()

                            # Crear la nueva
                            OfertaLaboratorio.objects.create(
                                producto_catalogo=producto_catalogo,
                                laboratorio=laboratorio,
                                precio_normal=offer_data['precio_normal'],
                                precio_oferta=offer_data['precio_oferta'],
                                descuento=offer_data['descuento'],
                                fecha_inicio=offer_data['fecha_inicio'],
                                fecha_fin=offer_data['fecha_fin'],
                                activa=offer_data['activa'],
                            )
                            self.stats['offers_updated'] += 1
                        else:
                            # La oferta existente es mejor o igual, mantenerla
                            logger.info(f"⏭️ Manteniendo oferta vigente existente (mejor precio): {producto_catalogo.nombre}")
                            self.stats['offers_kept'] += 1
                            # No hacer nada, skip
                            continue

                    else:
                        # Oferta VENCIDA: reemplazar siempre
                        logger.info(f"🔄 Reemplazando oferta vencida: {producto_catalogo.nombre}")
                        oferta_existente.delete()

                        OfertaLaboratorio.objects.create(
                            producto_catalogo=producto_catalogo,
                            laboratorio=laboratorio,
                            precio_normal=offer_data['precio_normal'],
                            precio_oferta=offer_data['precio_oferta'],
                            descuento=offer_data['descuento'],
                            fecha_inicio=offer_data['fecha_inicio'],
                            fecha_fin=offer_data['fecha_fin'],
                            activa=offer_data['activa'],
                        )
                        self.stats['offers_updated'] += 1

                else:
                    # NO existe oferta: crear nueva
                    OfertaLaboratorio.objects.create(
                        producto_catalogo=producto_catalogo,
                        laboratorio=laboratorio,
                        precio_normal=offer_data['precio_normal'],
                        precio_oferta=offer_data['precio_oferta'],
                        descuento=offer_data['descuento'],
                        fecha_inicio=offer_data['fecha_inicio'],
                        fecha_fin=offer_data['fecha_fin'],
                        activa=offer_data['activa'],
                    )
                    self.stats['offers_inserted'] += 1
                    logger.info(f"✓ Nueva oferta: {producto_catalogo.nombre} - Proveedor: {proveedor.nombre} - Lab: {laboratorio.nombre}")

            except Exception as e:
                logger.error(f"Error procesando oferta: {e}", exc_info=True)
                self.stats['errors'].append(f"Offer {offer_data.get('producto', 'Unknown')}: {str(e)}")
                continue

    def _get_or_create_producto_catalogo(self, offer_data, proveedor):
        """
        Obtiene o crea un ProductoCatalogo (producto en catálogo de proveedor).
        NO es inventario físico, es el catálogo de productos disponibles.

        REGLA DE NEGOCIO: Si el mismo código existe con otro proveedor,
        mantener solo el de MENOR PRECIO.
        """
        codigo = offer_data.get('codigo') or f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Buscar producto por código SIN filtrar por proveedor
        # (para comparar precios entre proveedores)
        producto_existente = ProductoCatalogo.objects.filter(codigo=codigo).first()

        # Determinar el precio a usar para comparación (priorizar precio_oferta si existe)
        nuevo_precio = offer_data.get('precio_oferta', 0) or offer_data.get('precio_normal', 0)

        if producto_existente:
            # Existe un producto con este código
            # Buscar la oferta asociada para comparar precios
            oferta_existente = OfertaLaboratorio.objects.filter(
                producto_catalogo=producto_existente
            ).first()

            if oferta_existente:
                precio_existente = oferta_existente.precio_oferta or oferta_existente.precio_normal
            else:
                # Si no hay oferta, usar 0 (así siempre se reemplaza)
                precio_existente = float('inf')

            # Comparar precios
            if nuevo_precio > 0 and nuevo_precio < precio_existente:
                # El NUEVO precio es MEJOR (menor) - actualizar producto existente
                logger.info(f"💰 Mejor precio encontrado para {codigo}: ${nuevo_precio} < ${precio_existente} - Cambiando de {producto_existente.proveedor.nombre} a {proveedor.nombre}")

                # Eliminar ofertas antiguas del proveedor anterior
                OfertaLaboratorio.objects.filter(producto_catalogo=producto_existente).delete()

                producto_existente.nombre = offer_data['producto']
                producto_existente.descripcion = f"From {offer_data.get('source_file', 'email')}"
                producto_existente.proveedor = proveedor  # Cambiar al proveedor con mejor precio
                producto_existente.save()

                return producto_existente
            else:
                # El precio EXISTENTE es mejor o igual - mantener el existente
                if producto_existente.proveedor.id != proveedor.id:
                    logger.info(f"⏭️ Manteniendo {codigo} de {producto_existente.proveedor.nombre} (${precio_existente}) - Descartando oferta de {proveedor.nombre} (${nuevo_precio})")
                return producto_existente

        # Si no existe, crear nuevo producto en catálogo
        # Obtener categoría por defecto
        categoria_medicamento, _ = Categoria.objects.get_or_create(
            nombre='Medicamento',
            defaults={'activa': True}
        )

        logger.info(f"✨ Nuevo producto: {codigo} - {offer_data['producto']} - {proveedor.nombre} - ${nuevo_precio}")
        producto_catalogo = ProductoCatalogo.objects.create(
            codigo=codigo,
            nombre=offer_data['producto'],
            descripcion=f"From {offer_data.get('source_file', 'email')}",
            categoria=categoria_medicamento,
            proveedor=proveedor,
            activo=True
        )

        return producto_catalogo

    def _save_log(self, start_time, exitoso):
        try:
            duration = (datetime.now() - start_time).total_seconds()

            # Actualizar el log existente (creado al inicio)
            if self.etl_log:
                self.etl_log.emails_procesados = self.stats['emails_processed']
                self.etl_log.adjuntos_descargados = self.stats['attachments_downloaded']
                self.etl_log.ofertas_extraidas = self.stats['offers_extracted']
                self.etl_log.ofertas_insertadas = self.stats['offers_inserted']
                self.etl_log.ofertas_actualizadas = self.stats['offers_updated']
                self.etl_log.errores = '\n'.join(self.stats['errors'])
                self.etl_log.duracion_segundos = duration
                self.etl_log.exitoso = exitoso
                self.etl_log.save()

                logger.info(f"📊 ETL Log actualizado (ID: {self.etl_log.id})")
                logger.info(f"   Archivos saltados (duplicados): {self.stats.get('attachments_skipped', 0)}")
            else:
                # Fallback si no se creó el log al inicio
                self.etl_log = ETLLog.objects.create(
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

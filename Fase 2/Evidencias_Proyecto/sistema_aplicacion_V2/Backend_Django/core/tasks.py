from celery import shared_task
from core.etl.offer_etl import OfferETL
import logging

logger = logging.getLogger(__name__)

@shared_task(name='core.tasks.run_offer_etl_task')
def run_offer_etl_task(days_back=5, strict_mode=False):
    """
    Celery task para ejecutar ETL automáticamente.
    Busca correos de los últimos 5 días y reescribe la base de datos de ofertas.

    Args:
        days_back: Número de días hacia atrás para buscar
        strict_mode: Si es True, solo busca correos con palabras clave específicas.
                    Si es False (default), busca todos los correos con adjuntos Excel/PDF.
    """
    logger.info(f"🤖 Starting automated ETL task (days_back={days_back}, strict_mode={strict_mode})")

    try:
        etl = OfferETL()
        stats = etl.run(days_back=days_back, strict_mode=strict_mode)

        logger.info(f"✓ ETL task completed successfully")
        logger.info(f"Stats: {stats}")

        return {
            'success': True,
            'stats': stats
        }

    except Exception as e:
        logger.error(f"❌ ETL task failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

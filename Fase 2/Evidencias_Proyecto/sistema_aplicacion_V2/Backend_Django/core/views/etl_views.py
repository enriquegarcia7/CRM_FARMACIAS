from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from core.tasks import run_offer_etl_task
from core.models import ETLLog
from django.conf import settings
import logging
import json
import os

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def run_etl_manual(request):
    """
    Endpoint para ejecutar ETL manualmente desde el frontend.
    POST /api/etl/run/
    Body: {
        "days_back": 5,  // Opcional, default 5
        "strict_mode": false  // Opcional, default false
    }

    strict_mode=false: Busca todos los correos con adjuntos Excel/PDF (recomendado para pruebas)
    strict_mode=true: Solo busca correos con palabras clave de ofertas (oferta, precio, etc.)
    """
    try:
        days_back = request.data.get('days_back', 5)
        strict_mode = request.data.get('strict_mode', False)

        logger.info(f"🚀 Manual ETL triggered (days_back={days_back}, strict_mode={strict_mode})")

        # Ejecutar tarea de Celery de forma asíncrona
        task = run_offer_etl_task.delay(days_back=days_back, strict_mode=strict_mode)

        mode_text = "modo estricto" if strict_mode else "modo amplio (todos los Excel/PDF)"
        return Response({
            'success': True,
            'message': f'ETL iniciado correctamente en {mode_text}',
            'task_id': task.id,
            'days_back': days_back,
            'strict_mode': strict_mode
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"Error starting ETL: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_etl_status(request):
    """
    Obtener estado del último ETL ejecutado.
    GET /api/etl/status/
    """
    try:
        last_log = ETLLog.objects.first()

        if not last_log:
            return Response({
                'success': True,
                'message': 'No hay registros de ETL',
                'last_execution': None
            })

        return Response({
            'success': True,
            'last_execution': {
                'fecha': last_log.fecha_ejecucion,
                'exitoso': last_log.exitoso,
                'ofertas_insertadas': last_log.ofertas_insertadas,
                'ofertas_actualizadas': last_log.ofertas_actualizadas,
                'duracion_segundos': last_log.duracion_segundos
            }
        })

    except Exception as e:
        logger.error(f"Error getting ETL status: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_etl_logs(request):
    """
    Obtener historial de ejecuciones ETL.
    GET /api/etl/logs/
    """
    try:
        logs = ETLLog.objects.all()[:20]  # Últimos 20

        data = [{
            'id': log.id,
            'fecha_ejecucion': log.fecha_ejecucion,
            'emails_procesados': log.emails_procesados,
            'adjuntos_descargados': log.adjuntos_descargados,
            'ofertas_extraidas': log.ofertas_extraidas,
            'ofertas_insertadas': log.ofertas_insertadas,
            'ofertas_actualizadas': log.ofertas_actualizadas,
            'duracion_segundos': log.duracion_segundos,
            'exitoso': log.exitoso,
            'errores': log.errores
        } for log in logs]

        return Response({
            'success': True,
            'data': data
        })

    except Exception as e:
        logger.error(f"Error getting ETL logs: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_etl_progress(request):
    """
    Obtener progreso en tiempo real del ETL en ejecución.
    GET /api/etl/progress/
    """
    try:
        progress_file = os.path.join(settings.BASE_DIR, 'etl_progress.json')

        if not os.path.exists(progress_file):
            return Response({
                'success': True,
                'running': False,
                'progress': None
            })

        with open(progress_file, 'r') as f:
            progress_data = json.load(f)

        # Verificar si el ETL está en ejecución o ya terminó
        stage = progress_data.get('stage', 'unknown')
        percentage = progress_data.get('percentage', 0)

        return Response({
            'success': True,
            'running': stage not in ['completado', 'error'] and percentage < 100,
            'progress': progress_data
        })

    except Exception as e:
        logger.error(f"Error getting ETL progress: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_etl_diagnostic(request):
    """
    Obtener información de diagnóstico de los correos encontrados.
    GET /api/etl/diagnostic/?days_back=3

    Muestra todos los correos encontrados y su estado de validación,
    útil para diagnosticar por qué algunos correos no se procesan.
    """
    try:
        days_back = int(request.GET.get('days_back', 3))

        logger.info(f"🔍 ETL Diagnostic requested (days_back={days_back})")

        from core.services.gmail_service import GmailService

        gmail_service = GmailService()
        diagnostic_data = gmail_service.get_diagnostic_info(days_back=days_back)

        logger.info(f"✅ Diagnostic completed: {diagnostic_data['total_found']} messages found")

        return Response({
            'success': True,
            'diagnostic': diagnostic_data
        })

    except FileNotFoundError as e:
        # Gmail no autenticado
        logger.warning(f"Gmail not authenticated: {e}")
        return Response({
            'success': False,
            'error': 'Gmail no está autenticado. Por favor, autentícate primero.',
            'needs_auth': True
        }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        logger.error(f"Error getting ETL diagnostic: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

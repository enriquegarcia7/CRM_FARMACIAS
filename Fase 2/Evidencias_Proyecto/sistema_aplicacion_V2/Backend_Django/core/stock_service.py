# core/stock_service.py
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg
from django.utils import timezone
import math


class DynamicStockService:
    """
    Servicio para calcular stock mínimo dinámico basado en:
    - Ventas históricas
    - Predicción estacional
    - Variabilidad de la demanda
    """

    def __init__(self):
        self.LEAD_TIME_DAYS = 7  # Tiempo de reposición (días)
        self.SERVICE_LEVEL = 0.95  # Nivel de servicio deseado (95%)
        self.Z_SCORE = 1.65  # Z-score para 95% de nivel de servicio
        self.SAFETY_STOCK_FACTOR = 1.5  # Factor de seguridad adicional

    def calcular_stock_minimo(self, producto):
        """
        Calcula el stock mínimo dinámico para un producto.

        Fórmula: Stock Mínimo = (Demanda Promedio Diaria × Lead Time) + Stock de Seguridad

        Stock de Seguridad = Z × σ × √Lead Time
        Donde σ es la desviación estándar de la demanda diaria
        """
        try:
            # Importar aquí para evitar dependencias circulares
            from .models import DetalleVenta

            # 1. Obtener datos de ventas históricas (últimos 90 días)
            fecha_limite = timezone.now() - timedelta(days=90)

            ventas_historicas = DetalleVenta.objects.filter(
                producto=producto,
                venta__estado='completada',
                venta__fecha__gte=fecha_limite
            ).values('venta__fecha__date').annotate(
                cantidad_vendida=Sum('cantidad')
            ).order_by('venta__fecha__date')

            if not ventas_historicas.exists():
                # Sin datos históricos, usar stock mínimo actual o un valor por defecto
                return max(producto.stock_minimo, 10)

            # 2. Calcular demanda promedio diaria
            ventas_list = list(ventas_historicas)
            total_vendido = sum(v['cantidad_vendida'] for v in ventas_list)
            dias_con_ventas = len(ventas_list)

            if dias_con_ventas == 0:
                return max(producto.stock_minimo, 10)

            demanda_promedio_diaria = total_vendido / dias_con_ventas

            # 3. Calcular desviación estándar de la demanda diaria
            cantidades = [v['cantidad_vendida'] for v in ventas_list]
            media = sum(cantidades) / len(cantidades)
            varianza = sum((x - media) ** 2 for x in cantidades) / len(cantidades)
            desviacion_estandar = math.sqrt(varianza)

            # 4. Calcular stock de seguridad
            # Stock de Seguridad = Z × σ × √Lead Time
            stock_seguridad = self.Z_SCORE * desviacion_estandar * math.sqrt(self.LEAD_TIME_DAYS)

            # 5. Calcular stock mínimo base
            stock_base = demanda_promedio_diaria * self.LEAD_TIME_DAYS

            # 6. Stock mínimo dinámico total
            stock_minimo_dinamico = stock_base + stock_seguridad

            # 7. Ajustar por estacionalidad si hay patrón
            factor_estacional = self._calcular_factor_estacional(producto, ventas_list)
            stock_minimo_dinamico *= factor_estacional

            # 8. Redondear al entero más cercano y asegurar un mínimo
            stock_minimo_final = max(math.ceil(stock_minimo_dinamico), 5)

            # 9. Limitar valores extremos
            if stock_minimo_final > 1000:
                stock_minimo_final = min(stock_minimo_final, int(demanda_promedio_diaria * 30))

            return stock_minimo_final

        except Exception as e:
            print(f"Error calculando stock dinámico para {producto.codigo}: {str(e)}")
            # En caso de error, devolver stock mínimo actual
            return producto.stock_minimo if producto.stock_minimo > 0 else 10

    def _calcular_factor_estacional(self, producto, ventas_historicas):
        """
        Calcula un factor de ajuste estacional usando el modelo ML predictivo.

        Combina:
        1. Predicción del modelo ML para el próximo mes
        2. Análisis de tendencias recientes vs históricas
        """
        # Análisis básico de tendencias
        factor_tendencia = self._calcular_tendencia_basica(ventas_historicas)

        # Intentar usar modelo ML de predicción estacional
        try:
            from .ml_service import seasonal_service
            from datetime import datetime

            # Verificar si el producto tiene categoría válida para el modelo
            if not producto.categoria:
                return factor_tendencia

            categoria_nombre = producto.categoria.nombre.upper()

            # Verificar si la categoría existe en el modelo ML
            if categoria_nombre not in seasonal_service.label_encoder.classes_:
                # Si no existe, intentar mapear a una categoría similar o usar tendencia básica
                return factor_tendencia

            # Calcular features desde ventas históricas
            if len(ventas_historicas) == 0:
                return factor_tendencia

            ventas_list = list(ventas_historicas)
            trans_lag_1 = ventas_list[-1]['cantidad_vendida'] if len(ventas_list) > 0 else 0
            trans_lag_3 = ventas_list[-3]['cantidad_vendida'] if len(ventas_list) > 2 else trans_lag_1
            trans_lag_6 = ventas_list[-6]['cantidad_vendida'] if len(ventas_list) > 5 else trans_lag_1
            trans_lag_12 = ventas_list[-12]['cantidad_vendida'] if len(ventas_list) > 11 else trans_lag_1

            # Promedio móvil 3 meses
            import numpy as np
            trans_ma_3 = np.mean([v['cantidad_vendida'] for v in ventas_list[-3:]]) if len(ventas_list) >= 3 else trans_lag_1

            # Obtener mes y año actual + 1 mes (para predecir próximo mes)
            hoy = datetime.now()
            mes_siguiente = hoy.month + 1 if hoy.month < 12 else 1
            año_siguiente = hoy.year if hoy.month < 12 else hoy.year + 1

            # Predecir demanda del próximo mes usando modelo ML
            prediccion_proxima = seasonal_service.predict(
                categoria=categoria_nombre,
                mes=mes_siguiente,
                año=año_siguiente,
                trans_lag_1=trans_lag_1,
                trans_lag_3=trans_lag_3,
                trans_lag_6=trans_lag_6,
                trans_lag_12=trans_lag_12,
                trans_ma_3=trans_ma_3
            )

            # Calcular factor basado en predicción vs promedio histórico
            promedio_historico = sum(v['cantidad_vendida'] for v in ventas_list) / len(ventas_list)

            if promedio_historico > 0:
                # Convertir predicción mensual a diaria para comparar
                prediccion_diaria = prediccion_proxima / 30
                factor_ml = prediccion_diaria / promedio_historico

                # Combinar factor ML (60%) con tendencia básica (40%)
                factor_combinado = (factor_ml * 0.6) + (factor_tendencia * 0.4)

                # Limitar factor entre 0.7 y 2.0 para evitar extremos
                factor_final = max(0.7, min(2.0, factor_combinado))

                print(f"📊 Producto {producto.codigo} ({categoria_nombre}): Factor estacional ML = {factor_final:.2f} (predicción: {prediccion_proxima:.0f} trans/mes)")
                return factor_final

            return factor_tendencia

        except Exception as e:
            print(f"⚠️ No se pudo calcular factor estacional ML para {producto.codigo}: {str(e)}")
            # Fallback a análisis de tendencias básico
            return factor_tendencia

    def _calcular_tendencia_basica(self, ventas_historicas):
        """
        Calcula tendencia básica comparando ventas recientes vs históricas.
        Fallback cuando no se puede usar el modelo ML.
        """
        if len(ventas_historicas) < 30:
            return 1.0

        ventas_recientes = ventas_historicas[-30:]
        total_recientes = sum(v['cantidad_vendida'] for v in ventas_recientes)
        promedio_reciente = total_recientes / len(ventas_recientes)

        total_historico = sum(v['cantidad_vendida'] for v in ventas_historicas)
        promedio_historico = total_historico / len(ventas_historicas)

        if promedio_historico == 0:
            return 1.0

        ratio_tendencia = promedio_reciente / promedio_historico

        if ratio_tendencia > 1.2:
            return min(1.5, 1.0 + (ratio_tendencia - 1.0) * 0.5)
        elif ratio_tendencia < 0.8:
            return max(0.8, ratio_tendencia)
        else:
            return 1.0

    def obtener_metricas_producto(self, producto):
        """
        Obtiene métricas adicionales para el producto.
        Útil para mostrar en el frontend.
        """
        try:
            from .models import DetalleVenta

            fecha_limite = timezone.now() - timedelta(days=90)

            ventas_historicas = DetalleVenta.objects.filter(
                producto=producto,
                venta__estado='completada',
                venta__fecha__gte=fecha_limite
            ).aggregate(
                total_vendido=Sum('cantidad'),
                dias_con_ventas=Count('venta__fecha__date', distinct=True)
            )

            total_vendido = ventas_historicas['total_vendido'] or 0
            dias_con_ventas = ventas_historicas['dias_con_ventas'] or 1

            demanda_promedio_diaria = total_vendido / dias_con_ventas if dias_con_ventas > 0 else 0

            # Días de cobertura actual
            dias_cobertura = producto.stock_actual / demanda_promedio_diaria if demanda_promedio_diaria > 0 else 999

            return {
                'demanda_promedio_diaria': round(demanda_promedio_diaria, 2),
                'total_vendido_90dias': total_vendido,
                'dias_cobertura': round(dias_cobertura, 1),
                'nivel_riesgo': self._clasificar_riesgo(dias_cobertura)
            }

        except Exception as e:
            print(f"Error obteniendo métricas para {producto.codigo}: {str(e)}")
            return {
                'demanda_promedio_diaria': 0,
                'total_vendido_90dias': 0,
                'dias_cobertura': 0,
                'nivel_riesgo': 'desconocido'
            }

    def _clasificar_riesgo(self, dias_cobertura):
        """Clasifica el nivel de riesgo de quiebre de stock"""
        if dias_cobertura < 7:
            return 'critico'
        elif dias_cobertura < 14:
            return 'alto'
        elif dias_cobertura < 30:
            return 'medio'
        else:
            return 'bajo'


# Instancia global del servicio
stock_service = DynamicStockService()

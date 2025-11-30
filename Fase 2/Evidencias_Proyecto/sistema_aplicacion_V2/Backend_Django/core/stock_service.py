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
        self.MIN_ABSOLUTE = 5  # Mínimo absoluto si no hay datos (emergencia)

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
                venta__estado__codigo='completada',
                venta__fecha__gte=fecha_limite
            ).values('venta__fecha__date').annotate(
                cantidad_vendida=Sum('cantidad')
            ).order_by('venta__fecha__date')

            if not ventas_historicas.exists():
                # Sin datos históricos, usar mínimo absoluto de emergencia
                # Intentar predecir con ML si tiene categoría válida
                stock_predicho_ml = self._predecir_sin_historico(producto)
                if stock_predicho_ml:
                    return stock_predicho_ml

                # Última opción: mínimo absoluto de emergencia
                print(f"⚠️ Producto {producto.codigo} sin datos históricos ni categoría ML válida. Usando mínimo absoluto.")
                return self.MIN_ABSOLUTE

            # 2. Calcular demanda promedio diaria
            ventas_list = list(ventas_historicas)
            total_vendido = sum(v['cantidad_vendida'] for v in ventas_list)
            dias_con_ventas = len(ventas_list)

            if dias_con_ventas == 0:
                # Datos históricos vacíos, intentar predicción ML
                stock_predicho_ml = self._predecir_sin_historico(producto)
                if stock_predicho_ml:
                    return stock_predicho_ml
                return self.MIN_ABSOLUTE

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
            print(f"❌ Error calculando stock dinámico para {producto.codigo}: {str(e)}")
            import traceback
            traceback.print_exc()
            # En caso de error, intentar predicción ML como fallback
            try:
                stock_predicho_ml = self._predecir_sin_historico(producto)
                if stock_predicho_ml:
                    return stock_predicho_ml
            except:
                pass
            # Última opción: mínimo absoluto de emergencia
            return self.MIN_ABSOLUTE

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

    def _predecir_sin_historico(self, producto):
        """
        Predice stock mínimo usando SOLO el modelo ML cuando no hay histórico.
        Usa la categoría del producto y valores promedio del sector.
        """
        try:
            from .ml_service import seasonal_service
            from datetime import datetime
            import numpy as np

            # Verificar categoría
            if not producto.categoria:
                return None

            categoria_nombre = producto.categoria.nombre.upper()

            # Verificar si la categoría existe en el modelo ML
            if categoria_nombre not in seasonal_service.label_encoder.classes_:
                print(f"⚠️ Categoría '{categoria_nombre}' no existe en modelo ML")
                return None

            # Usar valores dummy promedio del sector para esta categoría
            # Estos valores simulan un producto "promedio" de la categoría
            trans_lag_1 = 100  # Promedio mensual asumido
            trans_lag_3 = 95
            trans_lag_6 = 90
            trans_lag_12 = 105
            trans_ma_3 = 95

            # Predecir para el próximo mes
            hoy = datetime.now()
            mes_siguiente = hoy.month + 1 if hoy.month < 12 else 1
            año_siguiente = hoy.year if hoy.month < 12 else hoy.year + 1

            # Obtener predicción ML
            prediccion_mensual = seasonal_service.predict(
                categoria=categoria_nombre,
                mes=mes_siguiente,
                año=año_siguiente,
                trans_lag_1=trans_lag_1,
                trans_lag_3=trans_lag_3,
                trans_lag_6=trans_lag_6,
                trans_lag_12=trans_lag_12,
                trans_ma_3=trans_ma_3
            )

            # Convertir predicción mensual a demanda diaria
            demanda_diaria_predicha = prediccion_mensual / 30

            # Calcular stock mínimo: demanda diaria × lead time + margen de seguridad (20%)
            stock_minimo_ml = math.ceil(demanda_diaria_predicha * self.LEAD_TIME_DAYS * 1.2)

            # Asegurar un mínimo razonable
            stock_minimo_ml = max(stock_minimo_ml, self.MIN_ABSOLUTE)

            print(f"🤖 Producto {producto.codigo} ({categoria_nombre}): Stock ML sin histórico = {stock_minimo_ml} (predicción: {prediccion_mensual:.0f} trans/mes)")

            return stock_minimo_ml

        except Exception as e:
            print(f"⚠️ Error en predicción ML sin histórico para {producto.codigo}: {str(e)}")
            return None

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
        Enfoque profesional para farmacias:
        1. Usa datos históricos si existen
        2. Predice con ML si no hay histórico pero hay categoría válida
        3. Clasifica por stock absoluto si no hay datos
        """
        try:
            from .models import DetalleVenta

            fecha_limite = timezone.now() - timedelta(days=90)

            ventas_historicas = DetalleVenta.objects.filter(
                producto=producto,
                venta__estado__codigo='completada',
                venta__fecha__gte=fecha_limite
            ).aggregate(
                total_vendido=Sum('cantidad'),
                dias_con_ventas=Count('venta__fecha__date', distinct=True)
            )

            total_vendido = ventas_historicas['total_vendido'] or 0
            dias_con_ventas = ventas_historicas['dias_con_ventas'] or 1

            demanda_promedio_diaria = total_vendido / dias_con_ventas if dias_con_ventas > 0 else 0

            # CASO 1: Tiene ventas históricas
            if demanda_promedio_diaria > 0:
                dias_cobertura = producto.stock_actual / demanda_promedio_diaria
                return {
                    'demanda_promedio_diaria': round(demanda_promedio_diaria, 2),
                    'total_vendido_90dias': total_vendido,
                    'dias_cobertura': round(dias_cobertura, 1),
                    'nivel_riesgo': self._clasificar_riesgo(dias_cobertura),
                    'fuente_datos': 'historico',
                    'requiere_revision': False
                }

            # CASO 2: Sin ventas históricas - Intentar predicción ML
            prediccion_ml = self._obtener_demanda_predicha_ml(producto)

            if prediccion_ml and prediccion_ml > 0:
                # Convertir predicción mensual a demanda diaria
                demanda_estimada_diaria = prediccion_ml / 30
                dias_cobertura = producto.stock_actual / demanda_estimada_diaria

                # Clasificar riesgo basado en predicción
                nivel_riesgo = self._clasificar_riesgo(dias_cobertura)

                return {
                    'demanda_promedio_diaria': round(demanda_estimada_diaria, 2),
                    'total_vendido_90dias': 0,
                    'dias_cobertura': round(dias_cobertura, 1),
                    'nivel_riesgo': nivel_riesgo,
                    'fuente_datos': 'ml_prediccion',
                    'requiere_revision': True  # Requiere validación humana
                }

            # CASO 3: Sin histórico ni predicción ML válida
            # Clasificar por stock absoluto (riesgo de obsolescencia vs quiebre)
            if producto.stock_actual < 5:
                nivel_riesgo = 'sin_datos_stock_critico'
            elif producto.stock_actual < 10:
                nivel_riesgo = 'sin_datos_stock_bajo'
            else:
                nivel_riesgo = 'sin_movimiento'  # Alerta: posible obsolescencia

            return {
                'demanda_promedio_diaria': 0,
                'total_vendido_90dias': 0,
                'dias_cobertura': None,  # null - no calculable
                'nivel_riesgo': nivel_riesgo,
                'fuente_datos': 'sin_datos',
                'requiere_revision': True  # Requiere revisión manual
            }

        except Exception as e:
            print(f"Error obteniendo métricas para {producto.codigo}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'demanda_promedio_diaria': 0,
                'total_vendido_90dias': 0,
                'dias_cobertura': None,
                'nivel_riesgo': 'error',
                'fuente_datos': 'error',
                'requiere_revision': True
            }

    def _obtener_demanda_predicha_ml(self, producto):
        """
        Obtiene predicción de demanda mensual usando SOLO el modelo ML.
        Retorna la predicción mensual o None si no es posible predecir.
        """
        try:
            from .ml_service import seasonal_service
            from datetime import datetime
            import numpy as np

            # Verificar categoría
            if not producto.categoria:
                return None

            categoria_nombre = producto.categoria.nombre.upper()

            # Verificar si la categoría existe en el modelo ML
            if categoria_nombre not in seasonal_service.label_encoder.classes_:
                return None

            # Usar valores dummy promedio del sector para esta categoría
            trans_lag_1 = 100
            trans_lag_3 = 95
            trans_lag_6 = 90
            trans_lag_12 = 105
            trans_ma_3 = 95

            # Predecir para el próximo mes
            hoy = datetime.now()
            mes_siguiente = hoy.month + 1 if hoy.month < 12 else 1
            año_siguiente = hoy.year if hoy.month < 12 else hoy.year + 1

            # Obtener predicción ML
            prediccion_mensual = seasonal_service.predict(
                categoria=categoria_nombre,
                mes=mes_siguiente,
                año=año_siguiente,
                trans_lag_1=trans_lag_1,
                trans_lag_3=trans_lag_3,
                trans_lag_6=trans_lag_6,
                trans_lag_12=trans_lag_12,
                trans_ma_3=trans_ma_3
            )

            print(f"📊 Producto {producto.codigo} ({categoria_nombre}): Predicción ML = {prediccion_mensual:.0f} trans/mes")
            return prediccion_mensual

        except Exception as e:
            print(f"⚠️ Error en predicción ML para métricas de {producto.codigo}: {str(e)}")
            return None

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

import joblib
import os
import pandas as pd
import numpy as np
from django.conf import settings
from pathlib import Path


class SeasonalPredictionService:
    """
    Servicio para predicción de demanda estacional usando Random Forest
    Basado en el modelo entrenado con features específicas del proyecto SmartPharm
    """
    
    def __init__(self):
        # Rutas a los modelos
        base_path = Path(settings.BASE_DIR) / 'core' / 'ml_models'
        
        self.model_path = base_path / 'modelo_prediccion_estacional.pkl'
        self.encoder_path = base_path / 'label_encoder_categorias.pkl'
        
        self.model = None
        self.label_encoder = None
        
        self.load_models()
    
    def load_models(self):
        """Carga los modelos entrenados con validación"""
        import joblib
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.preprocessing import LabelEncoder
        
        models_dir = settings.ML_MODELS_PATH
        
        try:
            print(f"[INFO] Cargando modelos desde: {models_dir}")

            # Cargar modelo de predicción estacional
            model_path = os.path.join(models_dir, 'modelo_prediccion_estacional.pkl')
            print(f"[INFO] Cargando: {model_path}")
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
            
            self.model = joblib.load(model_path)
            
            # Validar tipo
            if not isinstance(self.model, RandomForestRegressor):
                raise TypeError(
                    f"Modelo incorrecto. Esperado: RandomForestRegressor, "
                    f"Obtenido: {type(self.model).__name__}"
                )
            
            print(f"[OK] Modelo cargado: {type(self.model).__name__}")

            # Cargar label encoder
            le_path = os.path.join(models_dir, 'label_encoder_categorias.pkl')
            print(f"[INFO] Cargando: {le_path}")
            
            if not os.path.exists(le_path):
                raise FileNotFoundError(f"Label encoder no encontrado: {le_path}")
            
            self.label_encoder = joblib.load(le_path)
            
            # Validar tipo
            if not isinstance(self.label_encoder, LabelEncoder):
                raise TypeError(
                    f"Label encoder incorrecto. Esperado: LabelEncoder, "
                    f"Obtenido: {type(self.label_encoder).__name__}"
                )
            
            print(f"[OK] Label encoder cargado: {len(self.label_encoder.classes_)} categorias")
            print(f"[OK] Modelos de prediccion estacional cargados correctamente")

        except Exception as e:
            print(f"[ERROR] ERROR al cargar modelos de prediccion estacional: {str(e)}")
            print(f"   Tipo de error: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise
    
    def predict_seasonal_demand(self, mes, año, categoria, trans_lag_1=None, 
                               trans_lag_3=None, trans_lag_6=None, 
                               trans_lag_12=None, trans_ma_3=None):
        """
        Predice la demanda estacional para un mes, año y categoría específicos
        
        Args:
            mes (int): Mes del año (1-12)
            año (int): Año (ej: 2025)
            categoria (str): Categoría de medicamento
            trans_lag_1 (int): Transacciones del mes anterior (opcional)
            trans_lag_3 (int): Transacciones de 3 meses atrás (opcional)
            trans_lag_6 (int): Transacciones de 6 meses atrás (opcional)
            trans_lag_12 (int): Transacciones de 12 meses atrás (opcional)
            trans_ma_3 (float): Media móvil de 3 meses (opcional)
        
        Returns:
            dict: Predicción con detalles y recomendaciones
        """
        try:
            # Validar categoría
            if categoria not in self.label_encoder.classes_:
                return {
                    'success': False,
                    'error': f'Categoría "{categoria}" no reconocida. Categorías válidas: {list(self.label_encoder.classes_)}'
                }
            
            # Preparar features según el modelo entrenado
            features = self._prepare_features(
                mes=mes,
                año=año,
                categoria=categoria,
                trans_lag_1=trans_lag_1,
                trans_lag_3=trans_lag_3,
                trans_lag_6=trans_lag_6,
                trans_lag_12=trans_lag_12,
                trans_ma_3=trans_ma_3
            )
            
            # Hacer predicción
            prediction = self.model.predict(features)[0]
            
            # Calcular nivel de confianza basado en datos históricos
            confidence = self._calculate_confidence(
                trans_lag_1, trans_lag_3, trans_lag_6, trans_lag_12
            )
            
            return {
                'success': True,
                'mes': mes,
                'año': año,
                'categoria': categoria,
                'transacciones_predichas': round(prediction, 0),
                'confianza': confidence,
                'estacion': self._get_season_name(mes),
                'recomendacion': self._generate_recommendation(prediction, mes, categoria),
                'datos_historicos_usados': {
                    'mes_anterior': trans_lag_1,
                    '3_meses_atras': trans_lag_3,
                    '6_meses_atras': trans_lag_6,
                    '12_meses_atras': trans_lag_12,
                    'media_movil_3m': trans_ma_3
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en predicción: {str(e)}'
            }
    
    def _prepare_features(self, mes, año, categoria, trans_lag_1, trans_lag_3, 
                         trans_lag_6, trans_lag_12, trans_ma_3):
        """
        Prepara las features exactamente como se entrenó el modelo
        """
        # Codificar categoría
        categoria_encoded = self.label_encoder.transform([categoria])[0]
        
        # Usar valores por defecto si no se proporcionan históricos
        if trans_lag_1 is None:
            trans_lag_1 = self._estimate_default_transactions(mes, categoria)
        if trans_lag_3 is None:
            trans_lag_3 = trans_lag_1 * 0.95
        if trans_lag_6 is None:
            trans_lag_6 = trans_lag_1 * 0.90
        if trans_lag_12 is None:
            trans_lag_12 = trans_lag_1 * 0.85
        if trans_ma_3 is None:
            trans_ma_3 = (trans_lag_1 + trans_lag_3 + trans_lag_6) / 3
        
        # Crear DataFrame con las features
        features_dict = {
            'mes': mes,
            'año': año,
            'categoria_encoded': categoria_encoded,
            'trans_lag_1': trans_lag_1,
            'trans_lag_3': trans_lag_3,
            'trans_lag_6': trans_lag_6,
            'trans_lag_12': trans_lag_12,
            'trans_ma_3': trans_ma_3
        }
        
        features_df = pd.DataFrame([features_dict])
        return features_df
    
    def _estimate_default_transactions(self, mes, categoria):
        """
        Estima transacciones por defecto basado en patrones estacionales realistas.
        Patrones basados en el mercado farmacéutico chileno (hemisferio sur).
        """
        # Patrones estacionales detallados por categoría (mes a mes)
        # 🔥 MEJORADO: Variaciones dramáticas de 50-100% para mostrar estacionalidad clara
        seasonal_patterns = {
            'ANTIGRIPAL': {
                # Invierno (Jun-Ago): PEAK máximo de demanda
                # Verano (Dic-Feb): MÍNIMO de demanda
                1: 120, 2: 100, 3: 90,   # Verano: BAJA (fin verano/inicio otoño)
                4: 180, 5: 280, 6: 420,  # Otoño/Invierno: SUBE RÁPIDO
                7: 550, 8: 580, 9: 480,  # Invierno: PEAK MÁXIMO (peak en julio-agosto)
                10: 320, 11: 180, 12: 140  # Primavera/Verano: BAJA
            },
            'ANTIALERGICO': {
                # Primavera (Sep-Nov): PEAK por polen y alergias
                # Invierno (Jun-Ago): BAJA
                1: 250, 2: 280, 3: 320,  # Verano: MODERADA-ALTA
                4: 380, 5: 420, 6: 280,  # Otoño: ALTA, luego baja en invierno
                7: 180, 8: 160, 9: 220,  # Invierno: BAJA
                10: 380, 11: 520, 12: 450  # Primavera: PEAK MÁXIMO (polen)
            },
            'ANALGESICO': {
                # Relativamente estable pero con variación moderada
                # Mayor en invierno por dolores musculares
                1: 420, 2: 400, 3: 430,  # Verano: ALTA constante
                4: 460, 5: 480, 6: 520,  # Otoño/Invierno: AUMENTA
                7: 550, 8: 540, 9: 510,  # Invierno: PEAK (dolores, gripes)
                10: 480, 11: 450, 12: 430  # Primavera: BAJA gradual
            },
            'ANTIBIOTICO': {
                # Invierno: PEAK por infecciones respiratorias
                # Verano: BAJA significativa
                1: 180, 2: 160, 3: 140,  # Verano: MÍNIMO
                4: 240, 5: 340, 6: 480,  # Otoño/Invierno: SUBE FUERTE
                7: 620, 8: 600, 9: 520,  # Invierno: PEAK MÁXIMO
                10: 380, 11: 260, 12: 200  # Primavera/Verano: BAJA
            },
            'DERMATOLOGICO': {
                # Verano: PEAK por protectores solares, quemaduras
                # Invierno: BAJA significativa
                1: 580, 2: 650, 3: 600,  # Verano: PEAK MÁXIMO (protector solar)
                4: 480, 5: 380, 6: 280,  # Otoño/Invierno: BAJA FUERTE
                7: 220, 8: 200, 9: 260,  # Invierno: MÍNIMO
                10: 380, 11: 480, 12: 560  # Primavera/Verano: SUBE
            },
            'CARDIOVASCULAR': {
                # Invierno: Mayor riesgo cardiovascular
                # Verano: Moderado
                1: 380, 2: 370, 3: 390,  # Verano: MODERADO
                4: 420, 5: 460, 6: 500,  # Otoño/Invierno: AUMENTA
                7: 540, 8: 530, 9: 490,  # Invierno: PEAK
                10: 450, 11: 410, 12: 390  # Primavera: BAJA
            },
            'GASTROINTESTINAL': {
                # Verano: PEAK por intoxicaciones alimentarias
                # Diciembre: Alto por fiestas
                1: 520, 2: 580, 3: 500,  # Verano: PEAK (intoxicaciones)
                4: 380, 5: 320, 6: 280,  # Otoño/Invierno: BAJA
                7: 260, 8: 240, 9: 280,  # Invierno: MÍNIMO
                10: 340, 11: 420, 12: 580  # Primavera/Verano: SUBE (fiestas)
            },
            'VITAMINICO': {
                # Invierno: PEAK para reforzar sistema inmune
                # Verano: BAJA
                1: 220, 2: 200, 3: 240,  # Verano: BAJA
                4: 320, 5: 420, 6: 520,  # Otoño/Invierno: SUBE FUERTE
                7: 600, 8: 580, 9: 500,  # Invierno: PEAK MÁXIMO
                10: 400, 11: 300, 12: 240  # Primavera: BAJA
            },
            'default': {
                # Patrón genérico con variación moderada estacional
                1: 320, 2: 310, 3: 330,
                4: 380, 5: 420, 6: 460,
                7: 500, 8: 490, 9: 450,
                10: 410, 11: 370, 12: 340
            }
        }

        categoria_upper = categoria.upper()

        # Buscar categoría exacta o parcial
        for key in seasonal_patterns.keys():
            if key in categoria_upper or categoria_upper in key:
                return seasonal_patterns[key].get(mes, seasonal_patterns['default'][mes])

        # Si no encuentra nada, usar patrón por defecto
        return seasonal_patterns['default'][mes]
    
    def _get_season_name(self, mes):
        """Retorna estación en Chile (hemisferio sur)"""
        if mes in [12, 1, 2]:
            return 'verano'
        elif mes in [3, 4, 5]:
            return 'otoño'
        elif mes in [6, 7, 8]:
            return 'invierno'
        else:
            return 'primavera'
    
    def _calculate_confidence(self, trans_lag_1, trans_lag_3, trans_lag_6, trans_lag_12):
        """Calcula nivel de confianza basado en datos históricos"""
        data_points = sum([
            trans_lag_1 is not None,
            trans_lag_3 is not None,
            trans_lag_6 is not None,
            trans_lag_12 is not None
        ])
        
        if data_points == 4:
            return 'Alta'
        elif data_points >= 2:
            return 'Media'
        else:
            return 'Baja (usando estimaciones)'
    
    def _generate_recommendation(self, predicted_demand, mes, categoria):
        """Genera recomendación basada en la predicción"""
        if predicted_demand > 150:
            nivel = "MUY ALTA"
            accion = "Aumentar stock significativamente"
        elif predicted_demand > 100:
            nivel = "ALTA"
            accion = "Aumentar stock moderadamente"
        elif predicted_demand > 50:
            nivel = "MODERADA"
            accion = "Mantener stock actual"
        else:
            nivel = "BAJA"
            accion = "Considerar reducción de stock"
        
        return {
            'nivel_demanda': nivel,
            'accion_sugerida': accion,
            'contexto_estacional': f"{self._get_season_name(mes).title()} - Patrón normal",
            'transacciones_estimadas': round(predicted_demand, 0)
        }
    
    def get_available_categories(self):
        """Retorna categorías disponibles"""
        return list(self.label_encoder.classes_)
    
    def predict(self, categoria, mes, año, trans_lag_1, trans_lag_3, 
                trans_lag_6, trans_lag_12, trans_ma_3):
        """
        Realiza predicción de demanda estacional.
        
        Args:
            categoria: Nombre de la categoría médica
            mes: Mes a predecir (1-12)
            año: Año a predecir
            trans_lag_1: Transacciones del mes anterior
            trans_lag_3: Transacciones hace 3 meses
            trans_lag_6: Transacciones hace 6 meses
            trans_lag_12: Transacciones hace 12 meses
            trans_ma_3: Promedio móvil de 3 meses
        
        Returns:
            float: Número predicho de transacciones
        """
        try:
            # Validar que el modelo esté cargado
            if self.model is None or self.label_encoder is None:
                raise ValueError("Modelos no están cargados correctamente")
            
            # Validar que la categoría existe en el label encoder
            if categoria not in self.label_encoder.classes_:
                # Si no existe, usar la categoría más similar o una por defecto
                print(f"⚠️ Categoría '{categoria}' no encontrada en el encoder")
                # Usar la primera categoría como fallback
                categoria = self.label_encoder.classes_[0]
                print(f"   Usando categoría por defecto: '{categoria}'")
            
            # Encodear la categoría
            categoria_encoded = self.label_encoder.transform([categoria])[0]
            
            # Preparar features en el orden correcto
            # ['mes', 'año', 'categoria_encoded', 'trans_lag_1', 
            #  'trans_lag_3', 'trans_lag_6', 'trans_lag_12', 'trans_ma_3']
            features = np.array([[
                mes,
                año,
                categoria_encoded,
                trans_lag_1,
                trans_lag_3,
                trans_lag_6,
                trans_lag_12,
                trans_ma_3
            ]])
            
            # Realizar predicción
            prediccion = self.model.predict(features)[0]
            
            # Asegurar que no sea negativa
            prediccion = max(0, prediccion)
            
            print(f"✅ Predicción para {categoria} en mes {mes}/{año}: {prediccion:.2f} transacciones")
            
            return float(prediccion)
            
        except Exception as e:
            print(f"❌ Error en predicción: {str(e)}")
            raise

# Instancia global del servicio
seasonal_service = SeasonalPredictionService()
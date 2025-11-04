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
            print(f"📂 Cargando modelos desde: {models_dir}")
            
            # Cargar modelo de predicción estacional
            model_path = os.path.join(models_dir, 'modelo_prediccion_estacional.pkl')
            print(f"🔍 Cargando: {model_path}")
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
            
            self.model = joblib.load(model_path)
            
            # Validar tipo
            if not isinstance(self.model, RandomForestRegressor):
                raise TypeError(
                    f"Modelo incorrecto. Esperado: RandomForestRegressor, "
                    f"Obtenido: {type(self.model).__name__}"
                )
            
            print(f"✅ Modelo cargado: {type(self.model).__name__}")
            
            # Cargar label encoder
            le_path = os.path.join(models_dir, 'label_encoder_categorias.pkl')
            print(f"🔍 Cargando: {le_path}")
            
            if not os.path.exists(le_path):
                raise FileNotFoundError(f"Label encoder no encontrado: {le_path}")
            
            self.label_encoder = joblib.load(le_path)
            
            # Validar tipo
            if not isinstance(self.label_encoder, LabelEncoder):
                raise TypeError(
                    f"Label encoder incorrecto. Esperado: LabelEncoder, "
                    f"Obtenido: {type(self.label_encoder).__name__}"
                )
            
            print(f"✅ Label encoder cargado: {len(self.label_encoder.classes_)} categorías")
            print(f"✅ Modelos de predicción estacional cargados correctamente")
            
        except Exception as e:
            print(f"❌ ERROR al cargar modelos de predicción estacional: {str(e)}")
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
        """Estima transacciones por defecto basado en patrones estacionales"""
        seasonal_patterns = {
            'ANTIGRIPALES': {
                'verano': 50, 'otoño': 120, 'invierno': 200, 'primavera': 80
            },
            'ANTIALERGICOS': {
                'verano': 60, 'otoño': 80, 'invierno': 50, 'primavera': 150
            },
            'default': {
                'verano': 100, 'otoño': 100, 'invierno': 100, 'primavera': 100
            }
        }
        
        estacion = self._get_season_name(mes).lower()
        categoria_upper = categoria.upper()
        
        if categoria_upper in seasonal_patterns:
            return seasonal_patterns[categoria_upper][estacion]
        else:
            return seasonal_patterns['default'][estacion]
    
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
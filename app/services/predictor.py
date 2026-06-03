import pandas as pd
import xgboost as xgb
import gc
import logging
from app.core.config import settings
from app.schemas.telemetry import TelemetryEvent

logger = logging.getLogger(__name__)

class PredictionEngine:
    def __init__(self):
        self.model = xgb.XGBClassifier(
            # Configuración preparada para escalar a GPU y mitigar errores de asignación de memoria
            device="cuda", 
            n_estimators=100,
            max_depth=5
        )
        self.is_model_loaded = False
        self._load_dummy_model()

    def _load_dummy_model(self):
        """
        Para propósitos de la hackatón, en lugar de entrenar por horas,
        creamos un modelo base en memoria listo para hacer inferencias.
        """
        import numpy as np
        logger.info("Cargando pesos del modelo XGBoost...")
        # Entrenamos rápido con datos ficticios para inicializar la estructura
        X_dummy = np.random.rand(10, 2)
        y_dummy = np.random.randint(0, 2, 10)
        self.model.fit(X_dummy, y_dummy)
        self.is_model_loaded = True
        logger.info("✅ Modelo XGBoost inicializado.")

    async def analyze_telemetry(self, event: TelemetryEvent) -> dict:
        """
        Recibe las coordenadas actuales y las contrasta con la capa Gold del Data Lake (Parquet).
        Devuelve un diccionario con la decisión si detecta anomalía.
        """
        try:
            # 1. OPTIMIZACIÓN DE MEMORIA: Leemos del Parquet solo las columnas estrictamente necesarias
            columns_to_read = ['route_id', 'historical_avg_speed', 'congestion_probability']
            
            df_history = pd.read_parquet(
                settings.S3_MOCK_PARQUET_PATH, 
                engine='pyarrow',
                columns=columns_to_read
            )
            
            # Filtramos rápidamente solo el historial de la ruta del bus
            route_data = df_history[df_history['route_id'] == event.route_id]
            
            # 2. Lógica de predicción mock (Comparar velocidad actual vs histórica)
            if not route_data.empty:
                avg_historic_speed = route_data['historical_avg_speed'].mean()
                
                # Si el bus va a menos de la mitad de la velocidad histórica, hay congestión
                if event.speed < (avg_historic_speed * 0.5):
                    # Aquí el modelo XGBoost evaluaría el nivel exacto de congestión
                    # prediction = self.model.predict(features)
                    
                    congestion_score = 0.85 # Mock del resultado de la IA
                    logger.warning(f"🚨 Anomalía detectada en {event.route_id}. Velocidad: {event.speed}km/h (Normal: {avg_historic_speed:.1f}km/h)")
                    
                    return {
                        "requires_reroute": True,
                        "congestion_level": congestion_score,
                        "reason": "Velocidad anómala detectada vs histórico S3"
                    }
            
            return {"requires_reroute": False}
            
        except Exception as e:
            logger.error(f"Error en inferencia: {str(e)}")
            return {"requires_reroute": False}
            
        finally:
            # 3. Liberación forzada de memoria RAM después de cada procesamiento pesado
            del route_data
            del df_history
            gc.collect()

# Instancia global (Singleton) para ser usada en los workers
predictor_service = PredictionEngine()
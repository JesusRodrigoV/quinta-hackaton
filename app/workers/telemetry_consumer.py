import asyncio
import logging
import json
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.telemetry import TelemetryEvent, RerouteCommand
from app.services.predictor import predictor_service
from app.services.kafka_producer import event_producer

# Inyecciones de Base de Datos
from app.db.session import AsyncSessionLocal
from app.models.prediction import PredictionLog

logger = logging.getLogger(__name__)

class TelemetryWorker:
    def __init__(self):
        self.consumer = None
        self.running = False

    async def start(self):
        self.running = True
        await self._connect_with_retry()
        if self.consumer:
            asyncio.create_task(self._consume_loop())

    async def _connect_with_retry(self):
        while self.running:
            try:
                self.consumer = AIOKafkaConsumer(
                    settings.KAFKA_TOPIC_TELEMETRY,
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id=settings.KAFKA_CONSUMER_GROUP,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset="latest"
                )
                await self.consumer.start()
                logger.info("✅ ¡Enlace establecido! Consumidor de Kafka activo.")
                break
            except KafkaConnectionError:
                await asyncio.sleep(5)
            except Exception as e:
                await asyncio.sleep(5)

    async def _save_to_db(self, log_entry: dict):
        """Paso 8.2: Guardado asíncrono en PostgreSQL."""
        try:
            # Abrimos una sesión de BD exclusiva para esta operación
            async with AsyncSessionLocal() as db:
                new_log = PredictionLog(
                    bus_id=log_entry["bus_id"],
                    corridor_id=log_entry["route_id"],
                    congestion_level=log_entry["congestion_level"],
                    original_route="RUTA_STANDARD_101", # En un caso real, esto viene del cache
                    suggested_route="RUTA_ALTERNATIVA_101_B"
                )
                db.add(new_log)
                await db.commit()
                logger.info("💾 Registro de decisión guardado en PostgreSQL.")
        except Exception as e:
            logger.error(f"❌ Error al guardar en base de datos: {e}")

    async def _consume_loop(self):
        """Paso 8.2: Flujo completo: Consumo -> Inferencia -> DB -> Producción"""
        try:
            async for msg in self.consumer:
                if not self.running:
                    break
                
                try:
                    event_data = TelemetryEvent(**msg.value)
                    
                    # 1. El Cerebro procesa la información
                    decision = await predictor_service.analyze_telemetry(event_data)
                    
                    if decision.get("requires_reroute"):
                        logger.warning(f"🚨 Anomalía confirmada para bus {event_data.bus_id}!")
                        
                        # Preparar la data de la decisión
                        congestion_score = decision.get("congestion_level", 0.0)
                        
                        # 2. Guardar en Base de Datos Local
                        await self._save_to_db({
                            "bus_id": event_data.bus_id,
                            "route_id": event_data.route_id,
                            "congestion_level": congestion_score
                        })
                        
                        # 3. Disparar el evento de desvío a la red vía Kafka
                        reroute_cmd = RerouteCommand(
                            bus_id=event_data.bus_id,
                            original_route="RUTA_STANDARD_101",
                            suggested_route="RUTA_ALTERNATIVA_101_B",
                            congestion_level=congestion_score,
                            reason=decision.get("reason", "Congestión detectada")
                        )
                        
                        await event_producer.emit_reroute(reroute_cmd.model_dump())
                        
                except ValidationError as ve:
                    pass
                except Exception as e:
                    logger.error(f"💥 Error procesando flujo: {e}")
                    
        except Exception as e:
            pass
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("🔴 Consumidor de Kafka detenido limpiamente.")

telemetry_worker = TelemetryWorker()
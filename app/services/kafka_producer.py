import json
import logging
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

class EventProducer:
    def __init__(self):
        self.producer = None

    async def start(self):
        """Inicializa el productor al arrancar FastAPI."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info("📡 Productor de Kafka listo para emitir desvíos.")
        except Exception as e:
            logger.error(f"❌ Error al iniciar el productor de Kafka: {e}")

    async def stop(self):
        """Cierra la conexión limpiamente."""
        if self.producer:
            await self.producer.stop()
            logger.info("🔴 Productor de Kafka detenido.")

    async def emit_reroute(self, payload: dict):
        """Envía el comando de desvío al tópico configurado."""
        if not self.producer:
            logger.error("⚠️ Intento de emitir mensaje, pero el productor no está activo.")
            return
            
        try:
            await self.producer.send_and_wait(
                settings.KAFKA_TOPIC_REROUTE, 
                value=payload
            )
            logger.info(f"🚀 Comando de desvío emitido a Kafka para el bus: {payload.get('bus_id')}")
        except Exception as e:
            logger.error(f"💥 Error al emitir evento de desvío: {e}")

# Instancia global para usar en todo el proyecto
event_producer = EventProducer()
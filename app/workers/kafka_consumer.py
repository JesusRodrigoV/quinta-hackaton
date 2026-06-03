import asyncio
import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError

from app.core.config import settings
from app.workers.manager import process_kafka_message

# Configuración del logger del worker
logger = logging.getLogger("urbanflow.audit.worker")
logging.basicConfig(level=logging.INFO)


class KafkaConsumerWorker:
    """
    Worker encargado del ciclo de vida del consumidor de Kafka.
    Maneja la reconexión automática, la escucha asíncrona de eventos
    y la delegación de mensajes al gestor de procesamiento.
    """

    def __init__(self):
        self.consumer: AIOKafkaConsumer = None
        self._is_running: bool = False
        self._task: asyncio.Task = None

    async def start(self):
        """Inicializa y arranca el consumidor en un hilo/tarea asíncrona de fondo."""
        self._is_running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("🚀 Tarea de fondo del Consumidor de Kafka instanciada con éxito.")

    async def stop(self):
        """Detiene el bucle de consumo de manera limpia y cierra las conexiones."""
        logger.info("🛑 Deteniendo el Consumidor de Kafka de forma controlada...")
        self._is_running = False
        
        if self.consumer:
            # Cancelamos el consumidor asíncrono
            await self.consumer.stop()
            
        if self._task:
            # Esperamos a que la tarea principal finalice limpiamente
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("✨ Consumidor de Kafka apagado correctamente.")

    async def _consume_loop(self):
        """Bucle infinito asíncrono de extracción y procesamiento de mensajes."""
        
        # Estrategia de reintentos en caso de que Kafka esté caído al arrancar la app
        while self._is_running:
            try:
                logger.info(f"Conectando al clúster de Kafka en: {settings.KAFKA_BOOTSTRAP_SERVERS}...")
                
                self.consumer = AIOKafkaConsumer(
                    *settings.KAFKA_TOPICS, # Desempaqueta los tópicos configurados en la Fase 2
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id=settings.KAFKA_CONSUMER_GROUP,
                    auto_offset_reset="earliest", # Lee desde el inicio si es un grupo nuevo
                    enable_auto_commit=True,      # Commit automático de offsets procesados
                    auto_commit_interval_ms=5000  # Envía el offset cada 5 segundos
                )
                
                # Arrancar físicamente el cliente
                await self.consumer.start()
                logger.info(f"✅ ¡Conectado a Kafka! Suscrito con éxito a los tópicos: {settings.KAFKA_TOPICS}")
                break # Rompe el bucle de reintento si conecta con éxito
                
            except KafkaConnectionError as e:
                logger.error(f"❌ Error de conexión con Kafka: {e}. Reintentando en 5 segundos...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.critical(f"💥 Error inesperado al inicializar Kafka: {e}. Reintentando...")
                await asyncio.sleep(5)

        # Bucle de escucha activa de mensajes
        try:
            async for message in self.consumer:
                if not self._is_running:
                    break
                
                # Extraemos los metadatos y el cuerpo crudo del mensaje en bytes
                topic = message.topic
                partition = message.partition
                offset = message.offset
                raw_value = message.value

                logger.info(f"📥 Mensaje recibido del Tópico: '{topic}' | Partición: {partition} | Offset: {offset}")

                # Creamos una tarea asíncrona independiente por mensaje recibido.
                # Esto permite que el consumidor siga leyendo eventos de Kafka inmediatamente
                # sin esperar a que el procesamiento en base de datos termine (Máximo rendimiento).
                asyncio.create_task(
                    process_kafka_message(
                        topic=topic,
                        raw_bytes=raw_value
                    )
                )

        except Exception as e:
            logger.error(f"🚨 Error crítico en el bucle de consumo activo: {e}")
        finally:
            if self.consumer:
                await self.consumer.stop()


# Instancia única reutilizable globalmente para controlar el ciclo de vida en main.py
kafka_worker = KafkaConsumerWorker()
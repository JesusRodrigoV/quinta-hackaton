import json
import logging
from typing import Any, Dict

from app.core.database import async_session_maker
from app.core.config import settings
from app.schemas.audit import AuditLogCreate
from app.services.audit_service import AuditService

logger = logging.getLogger("urbanflow.audit.manager")


async def process_kafka_message(topic: str, raw_bytes: bytes) -> None:
    """
    Orquesta la deserialización, el parseo de contratos según el tópico de Kafka
    y la persistencia del log de auditoría abriendo una sesión asíncrona dedicada.
    """
    try:
        # 1. Deserializar los bytes crudos a un diccionario de Python
        if not raw_bytes:
            logger.warning(f"⚠️ Mensaje vacío (tombstone) recibido en el tópico {topic}. Ignorando.")
            return

        payload_dict: Dict[str, Any] = json.loads(raw_bytes.decode("utf-8"))

        # Variables para construir nuestro contrato de auditoría unificado
        event_type: str = ""
        source_service: str = ""
        actor: str = "system_auto" # Por defecto, ya que viene de eventos automatizados entre servicios

        # 2. Identificar el contexto del evento basado en el tópico de procedencia
        if topic == settings.KAFKA_TOPIC_REROUTE:
            event_type = "reroute_executed"
            source_service = "prediction_engine"
            
        elif topic == settings.KAFKA_TOPIC_TARIFF:
            event_type = "tariff_modification"
            source_service = "payment_service"
            # Si el servicio de pago envía quién autorizó el cambio en el mensaje, lo extraemos
            if "actor" in payload_dict:
                actor = str(payload_dict.pop("actor"))
                
        else:
            logger.error(f"❌ Tópico desconocido detectado en el gestor: '{topic}'. No se puede procesar.")
            return

        # 3. Construir el objeto de entrada unificado y validarlo externamente
        audit_log_data = AuditLogCreate(
            event_type=event_type,
            source_service=source_service,
            actor=actor,
            payload=payload_dict
        )

        # 4. Crear una sesión asíncrona manual y persistir el log de auditoría
        # Usamos 'async_session_maker()' directamente porque no estamos bajo el contexto de una petición HTTP
        async with async_session_maker() as db_session:
            try:
                inserted_log = await AuditService.create_log(db=db_session, log_in=audit_log_data)
                
                logger.info(
                    f"✅ Log de Auditoría SELLADO CRIPTOGRÁFICAMENTE | "
                    f"ID: {inserted_log.id} | Tipo: {inserted_log.event_type} | "
                    f"Hash: {inserted_log.hash_signature[:16]}..."
                )
            except Exception as service_err:
                # Si falla la validación interna del payload o el commit, hacemos rollback implícito al salir del contexto
                logger.error(f"❌ Error en la lógica del servicio de auditoría: {str(service_err)}")
                
    except json.JSONDecodeError:
        logger.error(f"🚨 Error crítico: El mensaje del tópico '{topic}' no tiene un formato JSON válido. Bytes: {raw_bytes[:100]}")
    except Exception as e:
        logger.critical(f"💥 Falla catastrófica al procesar mensaje de Kafka en el manager: {str(e)}", exc_info=True)
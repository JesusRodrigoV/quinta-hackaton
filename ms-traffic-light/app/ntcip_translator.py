"""NTCIP protocol translator for traffic signal commands."""
import logging

from app.models import NTCIPMessage, SignalPriority, SignalState

logger = logging.getLogger(__name__)


class NTCIPTranslator:
    """Translates high-level events to NTCIP payloads (max 256 bytes)."""

    @staticmethod
    def translate_bus_delay_to_priority_command(
        intersection_id: str,
        delay_minutes: int,
        max_payload_bytes: int = 256,
    ) -> bytes:
        """
        Translate a delayed bus event to an NTCIP priority command.

        For a bus delayed > 5 minutes, request GREEN signal at intersection.
        Duration: min(delay_minutes * 10, 120) seconds.
        """
        duration_sec = min(delay_minutes * 10, 120)

        message = NTCIPMessage(
            command_type="ACTIVATE_PRIORITY",
            intersection_id=intersection_id,
            signal_state=SignalState.GREEN,
            priority_level=SignalPriority.HIGH,
            duration_sec=duration_sec,
        )

        try:
            payload = message.to_ntcip_payload()
            if len(payload) > max_payload_bytes:
                logger.warning(
                    "NTCIP payload truncated from %d to %d bytes",
                    len(payload),
                    max_payload_bytes,
                )
                payload = payload[:max_payload_bytes]
            return payload
        except Exception as e:
            logger.exception("Failed to translate bus delay to NTCIP: %s", e)
            raise

    @staticmethod
    def translate_congestion_to_command(
        intersection_id: str,
        severity: int,
        max_payload_bytes: int = 256,
    ) -> bytes:
        """
        Translate congestion alert to NTCIP command.

        Severity 1-2: NORMAL state
        Severity 3-4: Extended RED for congestion control
        Severity 5: CRITICAL with extended duration
        """
        if severity <= 2:
            target_state = SignalState.RED
            duration_sec = 30
            priority = SignalPriority.NORMAL
        elif severity <= 4:
            target_state = SignalState.RED
            duration_sec = 60
            priority = SignalPriority.HIGH
        else:
            target_state = SignalState.RED
            duration_sec = 120
            priority = SignalPriority.CRITICAL

        message = NTCIPMessage(
            command_type="SET_SIGNAL_STATE",
            intersection_id=intersection_id,
            signal_state=target_state,
            priority_level=priority,
            duration_sec=duration_sec,
        )

        try:
            payload = message.to_ntcip_payload()
            if len(payload) > max_payload_bytes:
                logger.warning(
                    "NTCIP payload truncated from %d to %d bytes",
                    len(payload),
                    max_payload_bytes,
                )
                payload = payload[:max_payload_bytes]
            return payload
        except Exception as e:
            logger.exception("Failed to translate congestion to NTCIP: %s", e)
            raise

    @staticmethod
    def validate_ntcip_payload(payload: bytes, max_bytes: int = 256) -> bool:
        """Validate NTCIP payload size and format."""
        if len(payload) > max_bytes:
            logger.error(f"NTCIP payload exceeds {max_bytes} bytes: {len(payload)}")
            return False
        if not isinstance(payload, bytes):
            logger.error("NTCIP payload must be bytes")
            return False
        return True

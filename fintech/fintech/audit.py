# audit.py
import time
import aiohttp
import logging
from typing import List, Dict, Any

logger = logging.getLogger("sentinel.audit")

class AuditEngine:
    """
    Tracks and compiles session interactions, user PIN verification attempts, 
    and fraud mitigation requests to post to a banking REST endpoint upon disconnect.
    """
    def __init__(self):
        self.buffer: List[Dict[str, Any]] = []
        self.status = "COMPLETED"  # Defaults to COMPLETED, changes to CARD_FROZEN on trigger
        self.identified_vector = "ACCOUNT_TAKEOVER_LINK"

    def log_message(self, speaker: str, message: str):
        """Appends conversation turn message to session transcript."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.buffer.append({
            "timestamp": timestamp,
            "speaker": speaker,
            "message": message,
            "type": "message"
        })
        logger.info(f"[{speaker}] {message}")

    def log_event(self, event_name: str, details: str = ""):
        """Appends custom session lifecycle and security milestone events."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.buffer.append({
            "timestamp": timestamp,
            "event": event_name,
            "details": details,
            "type": "event"
        })
        logger.info(f"[EVENT] {event_name}: {details}")
        
        # State transitions mapping
        if event_name == "CARD_FROZEN":
            self.status = "CARD_FROZEN"
        elif event_name == "PIN_VERIFICATION_FAILED":
            self.status = "VERIFICATION_FAILED"

    def get_transcript(self) -> str:
        """Serializes session events and conversations to a plain text transcript."""
        lines = []
        for entry in self.buffer:
            if entry.get("type") == "message":
                lines.append(f"{entry['timestamp']} - {entry['speaker']}: {entry['message']}")
            elif entry.get("type") == "event":
                lines.append(f"{entry['timestamp']} - EVENT: [{entry['event']}] {entry.get('details', '')}")
        return "\n".join(lines)

    async def send_audit_report(self, audit_url: str, account_id: str):
        """Asynchronously dispatches the accumulated transcript and state indicators to the API."""
        transcript = self.get_transcript()
        payload = {
            "account_id": account_id,
            "transcript": transcript,
            "identified_vector": self.identified_vector,
            "status": self.status
        }
        
        logger.info(f"Uploading session metrics to: {audit_url}")
        
        # Enforce 8-second connect and request timeouts for robustness
        timeout = aiohttp.ClientTimeout(total=8.0, connect=3.0)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(audit_url, json=payload) as response:
                    if response.status in (200, 201):
                        logger.info(f"Audit log sent successfully (HTTP status: {response.status}).")
                        return True
                    else:
                        response_body = await response.text()
                        logger.error(f"Audit reporting failed (HTTP status: {response.status}). Body: {response_body}")
                        return False
        except aiohttp.ClientConnectorError as cce:
            logger.error(f"Could not connect to audit endpoint: {str(cce)}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timed out waiting for audit report API response.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing audit log: {str(e)}")
            return False

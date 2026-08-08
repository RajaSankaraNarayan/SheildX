# config.py
import os
import logging
from dotenv import load_dotenv

# Configure structured logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sentinel.config")

# Load variables from local .env environment
load_dotenv()

# Gemini API configuration keys (resolve both standard google and gemini variants)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Sarvam AI developer key
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# Server binding variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8765"))

# Logging & fraud integration variables
AUDIT_LOG_URL = os.getenv("AUDIT_LOG_URL", "http://localhost:8000/api/v1/audit/log")
ACCOUNT_ID = os.getenv("ACCOUNT_ID", "ACC_1001")

def validate_config():
    """
    Validates that all necessary API tokens and configuration settings 
    are properly set in the runtime environment.
    """
    missing_vars = []
    if not GEMINI_API_KEY:
        missing_vars.append("GEMINI_API_KEY (or GOOGLE_API_KEY)")
    if not SARVAM_API_KEY:
        missing_vars.append("SARVAM_API_KEY")

    if missing_vars:
        error_message = (
            "Configuration Failure: The following environment variables are missing:\n"
            f"  {', '.join(missing_vars)}\n"
            "Please create a .env file based on .env.example and populate it with valid keys."
        )
        logger.error(error_message)
        raise ValueError(error_message)
    
    logger.info("Sentinel environment configuration validated successfully.")
    logger.info(f"Target WebSocket: ws://{HOST}:{PORT}")
    logger.info(f"Auditing Endpoint: {AUDIT_LOG_URL}")

from pydantic import BaseModel
from typing import Optional, List

class TransactionCreate(BaseModel):
    account_id: str
    amount: float
    recipient: str
    device_ip: str
    is_new_device: bool
    memo: Optional[str] = None
    
    # Enhanced Enterprise Metadata (All Optional for backwards compatibility)
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    merchant_mcc: Optional[str] = None
    merchant_country: Optional[str] = None
    currency: Optional[str] = "INR"
    payment_method: Optional[str] = None
    device_fingerprint: Optional[str] = None
    device_trust_score: Optional[float] = None
    os: Optional[str] = None
    app_version: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    network_type: Optional[str] = None
    is_vpn: Optional[bool] = False
    is_proxy: Optional[bool] = False
    is_tor: Optional[bool] = False
    failed_logins_24h: Optional[int] = 0
    sim_swap_detected: Optional[bool] = False
    rooted_device: Optional[bool] = False
    atm_withdrawal: Optional[bool] = False
    international_tx: Optional[bool] = False

class AccountAction(BaseModel):
    action: str

class AuditLogCreate(BaseModel):
    account_id: str
    transaction_id: Optional[str] = None
    transcript: str
    identified_vector: str
    voice_stress_score: Optional[float] = None
    status: str

class TransactionResponse(BaseModel):
    message: str
    transaction_id: str
    status: str
    risk_score: float
    risk_level: str  # Low, Medium, High, Critical
    reasons: List[str] = []
    ai_instruction: Optional[str] = None

class ThreatIntelCreate(BaseModel):
    threat_type: str
    value: str

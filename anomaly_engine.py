from models import TransactionCreate
from typing import Tuple, List, Dict
import database
from threat_intel_mock import get_threat_intel

def classify_risk(score: int) -> str:
    if score >= 80: return "Critical Risk"
    if score >= 60: return "High Risk"
    if score >= 30: return "Medium Risk"
    return "Low Risk"

def evaluate_transaction(tx_data: TransactionCreate, account: dict) -> Tuple[int, bool, str, List[str]]:
    """
    Enterprise-Grade Fraud Evaluation Engine
    Returns: (Risk Score 0-100, is_fraud boolean, risk_level string, list of triggered rules)
    """
    risk_score = 0
    reasons = []
    
    # Load Threat Intel
    threat_intel = get_threat_intel()
    db_threats = database.get_all_threats()
    suspicious_keywords = db_threats.get("KEYWORD", [])
    
    # Pre-process strings
    recipient_lower = tx_data.recipient.lower()
    memo_lower = tx_data.memo.lower() if tx_data.memo else ""

    # 1. Threat Intelligence & Network Checks
    if tx_data.device_ip in threat_intel["BLACKLISTED_IPS"] or tx_data.device_ip in db_threats.get("IP_ADDRESS", []):
        risk_score += 80
        reasons.append("BLACKLISTED_IP_DETECTED")
        
    if tx_data.is_tor:
        risk_score += 90
        reasons.append("TOR_EXIT_NODE_DETECTED")
        
    if tx_data.is_vpn or tx_data.is_proxy:
        risk_score += 30
        reasons.append("ANONYMIZING_NETWORK_DETECTED")
        
    if tx_data.merchant_country in threat_intel["HIGH_RISK_COUNTRIES"]:
        risk_score += 60
        reasons.append("HIGH_RISK_COUNTRY")

    # 2. Device & Account Security
    if tx_data.sim_swap_detected:
        risk_score += 85
        reasons.append("SIM_SWAP_DETECTED")
        
    if tx_data.rooted_device:
        risk_score += 40
        reasons.append("ROOTED_OR_JAILBROKEN_DEVICE")
        
    if tx_data.is_new_device:
        risk_score += 25
        reasons.append("NEW_DEVICE_LOGIN")
        
    if tx_data.failed_logins_24h and tx_data.failed_logins_24h > 3:
        risk_score += 35
        reasons.append("MULTIPLE_FAILED_LOGINS")
        
    if tx_data.device_trust_score is not None and tx_data.device_trust_score < 0.4:
        risk_score += 45
        reasons.append("LOW_DEVICE_TRUST_SCORE")

    # 3. Transaction Velocity & Amount Anomalies
    if tx_data.amount > 200000:
        risk_score += 30
        reasons.append("HIGH_VALUE_TRANSACTION")
        
    if 0 < tx_data.amount <= 10.00:
        risk_score += 25
        reasons.append("MICRO_TRANSACTION_PROBING")
        
    if tx_data.amount > 10000 and tx_data.amount % 10000 == 0:
        risk_score += 20
        reasons.append("ROUND_NUMBER_LARGE")
        
    if tx_data.merchant_mcc in threat_intel["HIGH_RISK_MCCS"]:
        risk_score += 40
        reasons.append("HIGH_RISK_MERCHANT_CATEGORY")

    # 4. Account Drain Check
    if account and account.get("balance", 0) > 0:
        balance = account["balance"]
        if tx_data.amount >= (balance * 0.95):
            risk_score += 50
            reasons.append("ACCOUNT_DRAIN_ATTEMPT")

    # 5. Scam Keywords (Social Engineering / BEC)
    if any(keyword in recipient_lower for keyword in suspicious_keywords) or \
       any(keyword in memo_lower for keyword in suspicious_keywords):
        risk_score += 60
        reasons.append("SUSPICIOUS_KEYWORD_MATCH")
        
    if tx_data.recipient in threat_intel["KNOWN_MULE_ACCOUNTS"] or tx_data.recipient in db_threats.get("UPI_ID", []):
        risk_score += 95
        reasons.append("KNOWN_MULE_ACCOUNT")

    # 6. Impossible Travel / Geo-Velocity (Mocked via flag)
    if tx_data.international_tx and not tx_data.merchant_country:
        risk_score += 30
        reasons.append("UNEXPECTED_INTERNATIONAL_TX")

    # Final Computation
    risk_score = min(risk_score, 100)
    risk_level = classify_risk(risk_score)
    is_fraud = risk_score >= 60  # High or Critical triggers fraud response
    
    return risk_score, is_fraud, risk_level, reasons

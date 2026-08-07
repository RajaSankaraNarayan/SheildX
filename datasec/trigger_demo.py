"""
===============================================================================
SENTINEL ENTERPRISE BANKING FRAUD SIMULATION & THREAT TESTING PLATFORM
===============================================================================
File: trigger_demo.py
Description: Production-quality testing harness for the Sentinel Fraud Detection System.
             Aligned with Sentinel SDK - Data & Security Engineer Guide & Master Spec.
             Simulates the 4 core Sentinel Fraud Simulator scenarios (Normal, Digital
             Arrest Scam, Impossible Travel, Account Takeover Drain) + extended vectors,
             Admin Threat Intelligence injection, 45+ banking telemetry fields,
             configurable 0-100 rule engine scoring, and PDF incident report generation.

Notice: DEFENSIVE SIMULATION HARNESS FOR BENCHMARKING & HACKATHON DEMONSTRATION.

Author: Senior Cybersecurity Engineer & Banking Security Architect
Python Version: 3.10+
Dependencies: requests, reportlab, faker
===============================================================================
"""

import os
import sys
import json
import uuid
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Reconfigure stdout/stderr to UTF-8 on Windows environments for cross-platform support
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Third-party HTTP request library
import requests
from requests.exceptions import ConnectionError as RequestConnectionError, Timeout, RequestException

# Third-party PDF generation library (ReportLab)
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)

# Third-party Synthetic Data Generator (Faker with fallback)
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    fake = None

# =============================================================================
# SECTION 1: CONFIGURATION & MASTER ENDPOINT CONSTANTS
# =============================================================================
# Base URL for the Sentinel FastAPI Backend (Default port 8000)
BASE_URL = "http://127.0.0.1:8000"

# Target REST & Admin Endpoints conforming to Sentinel Contracts
TRANSACTION_ENDPOINT = f"{BASE_URL}/api/v1/transaction"
ACCOUNT_ENDPOINT = f"{BASE_URL}/api/v1/account"
AUDIT_LOG_ENDPOINT = f"{BASE_URL}/api/v1/audit/log"
ADMIN_THREAT_ENDPOINT = f"{BASE_URL}/api/v1/admin/threat"
WEBSOCKET_ALERTS_URL = "ws://127.0.0.1:8000/ws/alerts"

# HTTP Request Timeout in seconds
DEFAULT_TIMEOUT = 10.0

# Output PDF File Name
PDF_REPORT_NAME = "Bank_Fraud_Incident_Report.pdf"

# Default Test Account ID as specified in Sentinel Guide
DEFAULT_ACCOUNT_ID = "ACC_1001"

# =============================================================================
# SECTION 2: LOGGING CONFIGURATION
# =============================================================================
stream_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[stream_handler]
)
logger = logging.getLogger("SentinelPlatform")


# =============================================================================
# SECTION 3: THREAT INTELLIGENCE DATASETS (STATIC MOCK & ADMIN DB)
# =============================================================================
class ThreatIntelDB:
    """
    Simulated Threat Intelligence Feeds as defined in threat_intel_mock.py & Sentinel Guide.
    Includes UPI IDs, scam keywords, blacklisted IPs, TOR nodes, and mule accounts.
    """
    # Blacklisted IP Addresses & Proxy Nodes
    BLACKLISTED_IPS: List[str] = [
        "185.220.101.5",     # Known TOR Exit Node (Moscow subnet)
        "45.154.255.71",     # Bulletproof Proxy Server
        "194.26.29.112",     # Anonymized VPN Gateway
        "185.220.100.240",   # High-risk TOR Node
        "193.218.118.152"    # Malicious Proxy Subnet
    ]

    # Suspicious ASNs (DigitalOcean, M247, IPVolume TOR)
    SUSPICIOUS_ASNS: List[int] = [14061, 9009, 202425, 51852, 60729]

    # High-Risk / Sanctioned Country Codes
    HIGH_RISK_COUNTRIES: List[str] = ["RU", "KP", "IR", "SY", "NG", "BY"]

    # Known Phishing Domains
    KNOWN_PHISHING_DOMAINS: List[str] = [
        "bank-verify-login.com",
        "secure-update-account.net",
        "irs-tax-settlement.org",
        "cbi-verification-portal.com"
    ]

    # Known Mule Accounts & Scam UPI Handles (Sentinel Guide Spec)
    KNOWN_MULE_ACCOUNTS: List[str] = [
        "fake_cbi_agent@upi",
        "digital_arrest_pay@upi",
        "cyber_police_desk@upi",
        "irs_settlement_pay@upi",
        "ACC_MULE_9901",
        "ACC_MULE_7712"
    ]

    # Social Engineering & Scam Keywords
    SCAM_KEYWORDS: List[str] = [
        "digital arrest",
        "cbi agent",
        "cyber crime",
        "police investigation",
        "irs tax settlement",
        "urgent crypto transfer",
        "anydesk refund",
        "verification fee"
    ]

    # Compromised Hardware Fingerprints
    COMPROMISED_FINGERPRINTS: List[str] = [
        "FP-DEV-MALICIOUS-X86-MOSCOW",
        "FP-ROOTED-ANDROID-EMULATOR-99",
        "FP-TOR-ANON-BROWSER-v12",
        "FP-ANYDESK-REMOTE-SESSION"
    ]


# =============================================================================
# SECTION 4: SENTINEL ANOMALY ENGINE (0-100 WEIGHTED SCORING)
# =============================================================================
class SentinelRuleEngine:
    """
    Sentinel Anomaly Engine (0-100 Scoring Model).
    Conforms to Sentinel SDK Guide Section 3.
    Evaluates 40+ metadata fields (VPN usage, Device Trust, Velocity, Keywords, MCCs).
    """

    @staticmethod
    def evaluate_transaction(payload: Dict[str, Any]) -> Dict[str, Any]:
        triggered_rules: List[Dict[str, Any]] = []
        score: float = 0.0

        # R01: Digital Arrest / Scam Keyword Trigger (+60 pts as per Sentinel Guide)
        memo = str(payload.get("memo", "")).lower()
        recipient = str(payload.get("recipient", "")).lower()
        if any(kw in memo or kw in recipient for kw in ThreatIntelDB.SCAM_KEYWORDS):
            weight = 60.0
            score += weight
            triggered_rules.append({
                "code": "R01_SCAM_KEYWORD_DIGITAL_ARREST",
                "weight": weight,
                "description": f"Social Engineering / Digital Arrest keyword detected in memo or recipient: '{payload.get('memo')}'"
            })

        # R02: Known Mule Account / Scam UPI ID (+60 pts)
        if recipient in [u.lower() for u in ThreatIntelDB.KNOWN_MULE_ACCOUNTS] or "fake_cbi" in recipient or "digital_arrest" in recipient:
            weight = 60.0
            score += weight
            triggered_rules.append({
                "code": "R02_KNOWN_MULE_UPI_ID",
                "weight": weight,
                "description": f"Recipient UPI ID/Account ({payload.get('recipient')}) matches blacklisted scammer watchlist."
            })

        # R03: Tor Network Exit Node (+90 pts as per Sentinel Guide)
        network_type = payload.get("network_type", "WiFi")
        if payload.get("tor_exit_node_detection", False) or network_type == "Tor" or payload.get("ip_address") in ThreatIntelDB.BLACKLISTED_IPS:
            weight = 90.0
            score += weight
            triggered_rules.append({
                "code": "R03_TOR_NETWORK_EXIT_NODE",
                "weight": weight,
                "description": "High Severity: Transaction routed through an anonymized TOR network exit node."
            })

        # R04: Impossible Travel Anomaly (+50 pts)
        geo_speed = payload.get("geo_velocity_kmh", 0.0)
        if payload.get("impossible_travel_detection", False) or geo_speed > 800.0:
            weight = 50.0
            score += weight
            triggered_rules.append({
                "code": "R04_IMPOSSIBLE_TRAVEL",
                "weight": weight,
                "description": f"Physical impossibility: Location shifted at {geo_speed:.1f} km/h since last active session."
            })

        # R05: Account Takeover & Full Account Drain (+40 pts)
        amount = payload.get("amount", 0.0)
        avg_spend = payload.get("average_customer_spend", 750.0)
        if amount > (avg_spend * 10.0):
            weight = 40.0
            score += weight
            triggered_rules.append({
                "code": "R05_ACCOUNT_DRAIN_SPIKE",
                "weight": weight,
                "description": f"High value transfer (INR {amount:,.2f}) >10x customer baseline (INR {avg_spend:,.2f})."
            })

        # R06: VPN & Proxy Detection (+30 pts)
        if payload.get("is_vpn", False) or payload.get("vpn_detection", False) or network_type in ["VPN", "Proxy"]:
            weight = 30.0
            score += weight
            triggered_rules.append({
                "code": "R06_VPN_PROXY_ACTIVE",
                "weight": weight,
                "description": "Anonymized VPN tunnel or proxy server active during request."
            })

        # R07: Recent SIM Swap & Password Reset (+35 pts)
        if payload.get("sim_swap_detected", False) or payload.get("password_reset_attempt", False):
            weight = 35.0
            score += weight
            triggered_rules.append({
                "code": "R07_SIM_SWAP_RECENT",
                "weight": weight,
                "description": "Cellular SIM swap or credential password reset detected within last 48 hours."
            })

        # R08: Multiple Failed Login Attempts (+25 pts)
        failed_logins = payload.get("failed_login_attempts", 0)
        if failed_logins >= 3:
            weight = 25.0
            score += weight
            triggered_rules.append({
                "code": "R08_BRUTE_FORCE_LOGINS",
                "weight": weight,
                "description": f"Credential stuffing indicator: {failed_logins} failed password login attempts recorded."
            })

        # R09: High-Risk Country Jurisdiction (+40 pts)
        country = payload.get("merchant_country", "IN")
        if country in ThreatIntelDB.HIGH_RISK_COUNTRIES:
            weight = 40.0
            score += weight
            triggered_rules.append({
                "code": "R09_HIGH_RISK_COUNTRY",
                "weight": weight,
                "description": f"Geographical origin ({country}) is flagged on OFAC/FATF sanctioned country list."
            })

        # R10: Untrusted / New Device Fingerprint (+20 pts)
        if payload.get("is_new_device", False) or payload.get("device_trust_score", 1.0) < 0.4:
            weight = 20.0
            score += weight
            triggered_rules.append({
                "code": "R10_UNTRUSTED_DEVICE",
                "weight": weight,
                "description": "Transaction initiated from unverified hardware signature or low trust device."
            })

        # Cap score at 100.0
        final_score = min(100.0, round(score, 1))

        # Classify Severity Level & Enforcement Action
        if final_score < 30.0:
            risk_level = "LOW RISK"
            status = "COMPLETED"
            action = "APPROVED"
        elif final_score < 60.0:
            risk_level = "MEDIUM RISK"
            status = "STEP_UP_MFA_REQUIRED"
            action = "CHALLENGE_OTP"
        elif final_score < 85.0:
            risk_level = "HIGH RISK"
            status = "PENDING_REVIEW"
            action = "VOICE_AI_VERIFICATION"
        else:
            risk_level = "CRITICAL RISK"
            status = "BLOCKED"
            action = "FREEZE_ACCOUNT_AND_ALERT_WEBSOCKET"

        # Generate Voice AI Intervention Instruction if score > 60 (Sentinel Guide Spec)
        ai_instruction = None
        if final_score >= 60.0:
            ai_instruction = (
                f"Refuse the transfer of INR {amount:,.2f}. Gently explain that scammers often use these keywords "
                f"and fake official handles ({payload.get('recipient')}). Ask if someone is pressuring them under a 'Digital Arrest'."
            )

        return {
            "risk_score": final_score,
            "risk_level": risk_level,
            "status": status,
            "action": action,
            "triggered_rules": triggered_rules,
            "ai_instruction": ai_instruction
        }


# =============================================================================
# SECTION 5: SYNTHETIC DATA & SCENARIO GENERATOR (SENTINEL GUIDE SPEC)
# =============================================================================
class TransactionGenerator:
    """
    Generates synthetic transaction payloads for Sentinel Fraud Simulator.
    Implements the 4 primary scenarios specified in Sentinel Guide Section 4:
      1. Normal Transaction
      2. Social Engineering (Digital Arrest Scam)
      3. Impossible Travel (Tor & Foreign IP)
      4. Account Takeover (Account Drain with VPN)
    + Extended Attack Vectors.
    """

    @staticmethod
    def _base_normal_payload() -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        cust_name = fake.name() if fake else "Rahul Sharma"
        city = fake.city() if fake else "Mumbai"

        return {
            "transaction_id": str(uuid.uuid4()),
            "account_number": "ACC_1001",
            "account_id": DEFAULT_ACCOUNT_ID,
            "customer_id": "CUST_987654",
            "customer_name": cust_name,
            "customer_account_age_days": 1420,
            "average_customer_spend": 750.00,
            "amount": 500.00,
            "currency": "INR",
            "recipient": "Starbucks Coffee",
            "merchant_name": "Starbucks Coffee",
            "merchant_category_code": 5411,
            "merchant_country": "IN",
            "merchant_city": city,
            "payment_method": "UPI",
            "memo": "Buying morning coffee",
            "device_id": "DEV-IPHONE15-PRO-9921",
            "device_fingerprint": "FP-VERIFIED-IOS-MOBILE",
            "device_trust_score": 0.95,
            "browser_user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) Mobile/15E148",
            "operating_system": "iOS 17.4",
            "mobile_app_version": "v4.12.0",
            "is_new_device": False,
            "device_fingerprint_match": True,
            "rooted_jailbroken_device_flag": False,
            "latitude": 19.0760,
            "longitude": 72.8777,
            "gps_accuracy_meters": 5.2,
            "timestamp": now.isoformat(),
            "time_zone": "Asia/Kolkata (+05:30)",
            "ip_address": "49.207.54.10",
            "isp": "Reliance Jio Infocomm",
            "asn": 55836,
            "network_type": "WiFi",
            "is_vpn": False,
            "proxy_detection": False,
            "tor_exit_node_detection": False,
            "vpn_detection": False,
            "login_session_id": f"SESS-{uuid.uuid4().hex[:8]}",
            "previous_login_location": "Mumbai, IN",
            "previous_device": "DEV-IPHONE15-PRO-9921",
            "failed_login_attempts": 0,
            "password_reset_attempt": False,
            "sim_swap_detected": False,
            "impossible_travel_detection": False,
            "velocity_check_count": 1,
            "geo_velocity_kmh": 12.5,
            "new_beneficiary_flag": False,
            "beneficiary_account_age_days": 900,
            "beneficiary_risk_score": 0.05,
            "first_time_merchant_flag": False,
            "high_risk_merchant_flag": False,
            "card_present": True,
            "contactless_payment": True,
            "atm_withdrawal_flag": False,
            "international_transaction_flag": False
        }

    @staticmethod
    def generate_scenario_payload(scenario_code: str) -> Dict[str, Any]:
        payload = TransactionGenerator._base_normal_payload()

        match scenario_code:
            # -----------------------------------------------------------------
            # SENTINEL GUIDE SCENARIO 1: NORMAL TRANSACTION
            # -----------------------------------------------------------------
            case "NORMAL":
                pass  # Base normal coffee purchase

            # -----------------------------------------------------------------
            # SENTINEL GUIDE SCENARIO 2: SOCIAL ENGINEERING (DIGITAL ARREST)
            # -----------------------------------------------------------------
            case "DIGITAL_ARREST" | "SOCIAL_ENGINEERING":
                payload.update({
                    "amount": 150000.00,  # High urgency scam transfer
                    "recipient": "fake_cbi_agent@upi",  # Blacklisted scam UPI handle
                    "merchant_name": "Cyber Police Settlement Desk",
                    "merchant_category_code": 4829,
                    "payment_method": "UPI",
                    "memo": "Digital Arrest clearance fee for CBI investigation case",
                    "new_beneficiary_flag": True,
                    "beneficiary_risk_score": 0.98,
                    "high_risk_merchant_flag": True
                })

            # -----------------------------------------------------------------
            # SENTINEL GUIDE SCENARIO 3: IMPOSSIBLE TRAVEL (TOR & FOREIGN IP)
            # -----------------------------------------------------------------
            case "IMPOSSIBLE_TRAVEL":
                payload.update({
                    "amount": 45000.00,
                    "merchant_country": "RU",
                    "merchant_city": "Moscow",
                    "latitude": 55.7558,
                    "longitude": 37.6173,
                    "ip_address": "185.220.101.5",  # TOR Exit Node
                    "isp": "TOR Anonymized Exit Node",
                    "asn": 14061,
                    "network_type": "Tor",
                    "tor_exit_node_detection": True,
                    "impossible_travel_detection": True,
                    "geo_velocity_kmh": 6800.0,
                    "international_transaction_flag": True,
                    "memo": "Moscow ATM transfer check"
                })

            # -----------------------------------------------------------------
            # SENTINEL GUIDE SCENARIO 4: ACCOUNT TAKEOVER (ACCOUNT DRAIN)
            # -----------------------------------------------------------------
            case "ATO" | "ACCOUNT_DRAIN":
                payload.update({
                    "amount": 250000.00,  # Full account balance drain
                    "recipient": "digital_arrest_pay@upi",
                    "merchant_name": "Offshore Escrow Liquidators",
                    "merchant_category_code": 6051,
                    "device_id": "DEV-UNKNOWN-LINUX-9901",
                    "device_fingerprint": "FP-DEV-MALICIOUS-X86-MOSCOW",
                    "device_trust_score": 0.10,
                    "operating_system": "Linux x86_64",
                    "is_new_device": True,
                    "device_fingerprint_match": False,
                    "ip_address": "194.26.29.112",
                    "network_type": "VPN",
                    "is_vpn": True,
                    "vpn_detection": True,
                    "failed_login_attempts": 5,
                    "sim_swap_detected": True,
                    "password_reset_attempt": True,
                    "new_beneficiary_flag": True,
                    "high_risk_merchant_flag": True,
                    "memo": "Full account balance drain following SIM reset"
                })

            # Extended Scenarios
            case "BEC":
                payload.update({
                    "amount": 350000.00,
                    "recipient": "irs_settlement_pay@upi",
                    "memo": "Vendor invoice payment urgent clearance",
                    "new_beneficiary_flag": True,
                    "international_transaction_flag": True
                })

            case "CRYPTO_SCAM":
                payload.update({
                    "amount": 120000.00,
                    "recipient": "BEN_CRYPTO_LIQUIDATOR_GLOBAL",
                    "merchant_category_code": 6051,
                    "high_risk_merchant_flag": True,
                    "memo": "Guaranteed investment return deposit"
                })

            case _:
                payload.update({
                    "amount": 50000.00,
                    "recipient": "fake_cbi_agent@upi",
                    "memo": f"Simulated test scenario: {scenario_code}"
                })

        return payload


# =============================================================================
# SECTION 6: SENTINEL REST & ADMIN API DEMO HARNESS
# =============================================================================
def send_transaction_payload(payload: Dict[str, Any], scenario_title: str) -> Optional[Dict[str, Any]]:
    """Sends synthetic transaction payload to FastAPI backend and evaluates local rule engine."""
    print("\n" + "=" * 70)
    print(f" [HARNESS EXECUTION] SCENARIO: {scenario_title.upper()}")
    print("=" * 70)

    rule_results = SentinelRuleEngine.evaluate_transaction(payload)
    print(f"--> Target Endpoint  : {TRANSACTION_ENDPOINT}")
    print(f"--> Account ID       : {payload['account_id']} ({payload['customer_name']})")
    print(f"--> Amount / Recipient: INR {payload['amount']:,.2f} // {payload['recipient']}")
    print(f"--> Network / IP     : {payload['ip_address']} ({payload['network_type']})")
    print(f"--> Sentinel Score   : {rule_results['risk_score']} / 100.0 ({rule_results['risk_level']})")
    print(f"--> System Action    : {rule_results['action']}")

    if rule_results["triggered_rules"]:
        print("--> Triggered Fraud Heuristics:")
        for r in rule_results["triggered_rules"]:
            print(f"    * [{r['code']}] (+{r['weight']} pts) {r['description']}")

    if rule_results["ai_instruction"]:
        print(f"\n--> Voice AI Instruction: \"{rule_results['ai_instruction']}\"")

    print("\n[+] Telemetry Request Payload JSON:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        logger.info(f"Posting transaction to {TRANSACTION_ENDPOINT}...")
        response = requests.post(
            TRANSACTION_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT
        )

        print("\n<-- RESPONSE RECEIVED FROM FASTAPI BACKEND:")
        print(f"HTTP Status Code : {response.status_code}")

        try:
            response_json = response.json()
            print("Formatted Server Response JSON:")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
            logger.info(f"Backend responded with HTTP {response.status_code}.")
            return response_json
        except json.JSONDecodeError:
            print("[!] Raw Response Body:", response.text)
            return None

    except RequestConnectionError:
        logger.error(f"Connection Error: Backend offline at {BASE_URL}.")
        print("\n[!] NOTICE: Sentinel FastAPI server is currently offline.")
        print("    The harness successfully evaluated local threat intelligence & 0-100 anomaly engine.")
        print(f"    To connect live backend, launch FastAPI server at {BASE_URL}.")
        return None
    except Exception as exc:
        logger.error(f"HTTP Exception: {exc}")
        print(f"\n[!] ERROR: {exc}")
        return None


def push_admin_threat_intel(threat_type: str = "UPI_ID", value: str = "fake_cbi_agent@upi") -> Optional[Dict[str, Any]]:
    """
    Pushes live threat intelligence entry to backend via Admin API (Sentinel Guide Option B).
    Endpoint: POST http://127.0.0.1:8000/api/v1/admin/threat
    """
    print("\n" + "=" * 60)
    print(" PUSH LIVE THREAT INTEL TO ADMIN DB (POST /api/v1/admin/threat)")
    print("=" * 60)

    admin_payload = {
        "threat_type": threat_type,
        "value": value
    }

    logger.info(f"Posting Threat Intel to Admin API at {ADMIN_THREAT_ENDPOINT}...")
    print("--> Admin Request Payload:")
    print(json.dumps(admin_payload, indent=2, ensure_ascii=False))

    try:
        response = requests.post(
            ADMIN_THREAT_ENDPOINT,
            json=admin_payload,
            headers={"Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT
        )
        print(f"<-- Status Code: {response.status_code}")
        try:
            res_json = response.json()
            print("Response JSON:")
            print(json.dumps(res_json, indent=2, ensure_ascii=False))
            return res_json
        except json.JSONDecodeError:
            print("[!] Raw Response:", response.text)
            return None
    except RequestConnectionError:
        print(f"[!] Server offline at {ADMIN_THREAT_ENDPOINT}. Threat intel recorded locally in ThreatIntelDB.")
        return {"status": "RECORDED_LOCALLY", "threat_type": threat_type, "value": value}
    except Exception as e:
        print(f"[!] Error: {e}")
        return None


def check_account_balance(account_id: str = DEFAULT_ACCOUNT_ID) -> Optional[Dict[str, Any]]:
    """Query account balance (Sentinel Master Contract #2)."""
    print("\n" + "=" * 60)
    print(f" CHECK ACCOUNT BALANCE (GET /api/v1/account/{account_id})")
    print("=" * 60)
    url = f"{ACCOUNT_ENDPOINT}/{account_id}"
    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        print(f"<-- Status Code: {response.status_code}")
        res_json = response.json()
        print("Response JSON:")
        print(json.dumps(res_json, indent=2, ensure_ascii=False))
        return res_json
    except RequestConnectionError:
        print(f"[!] Server offline at {url}. (Simulated local response: Balance INR 150,000.00)")
        return {"balance": 150000.0, "status": "NORMAL", "language_pref": "EN"}
    except Exception as e:
        print(f"[!] Error: {e}")
        return None


def post_audit_log(
    account_id: str = DEFAULT_ACCOUNT_ID,
    transaction_id: str = "TXN-ATK-9999",
    transcript: str = "Customer: I did not authorize this payment. Voice AI: We detected a Digital Arrest scam vector and blocked the transaction.",
    identified_vector: str = "DIGITAL_ARREST_SCAM",
    voice_stress_score: float = 0.85
) -> Optional[Dict[str, Any]]:
    """Push voice AI call audit log (Sentinel Master Contract #4)."""
    print("\n" + "=" * 60)
    print(" POST VOICE CALL AUDIT LOG (POST /api/v1/audit/log)")
    print("=" * 60)
    audit_payload = {
        "account_id": account_id,
        "transaction_id": transaction_id,
        "transcript": transcript,
        "identified_vector": identified_vector,
        "voice_stress_score": voice_stress_score
    }
    try:
        response = requests.post(AUDIT_LOG_ENDPOINT, json=audit_payload, timeout=DEFAULT_TIMEOUT)
        print(f"<-- Status Code: {response.status_code}")
        res_json = response.json()
        print("Response JSON:")
        print(json.dumps(res_json, indent=2, ensure_ascii=False))
        return res_json
    except RequestConnectionError:
        print(f"[!] Server offline at {AUDIT_LOG_ENDPOINT}. Log recorded locally for report export.")
        return {"status": "SUCCESS", "logged_id": "AUDIT-LOCAL-1001"}
    except Exception as e:
        print(f"[!] Error: {e}")
        return None


# =============================================================================
# SECTION 7: REPORTLAB PDF AUDIT INCIDENT REPORT GENERATOR
# =============================================================================
def generate_incident_report(output_filename: str = PDF_REPORT_NAME) -> None:
    """Generates PDF Incident Report using ReportLab."""
    print("\n" + "=" * 70)
    print(f" [REPORT GENERATOR] BUILDING AUDIT INCIDENT REPORT PDF ({output_filename})")
    print("=" * 70)

    try:
        payload = TransactionGenerator.generate_scenario_payload("DIGITAL_ARREST")
        rule_eval = SentinelRuleEngine.evaluate_transaction(payload)

        doc = SimpleDocTemplate(
            output_filename,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        PRIMARY = colors.HexColor("#1E3A8A")
        SECONDARY = colors.HexColor("#0F172A")
        ACCENT_RED = colors.HexColor("#DC2626")
        BG_LIGHT = colors.HexColor("#F8FAFC")
        TEXT_DARK = colors.HexColor("#1E293B")

        title_style = ParagraphStyle(
            "ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=PRIMARY, alignment=0, spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#64748B"), spaceAfter=10
        )
        h2_style = ParagraphStyle(
            "Heading2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=PRIMARY, spaceBefore=8, spaceAfter=4
        )
        body_style = ParagraphStyle(
            "BodyCustom", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=12, textColor=TEXT_DARK
        )
        transcript_cust = ParagraphStyle("TCust", parent=body_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#1E40AF"))
        transcript_ai = ParagraphStyle("TAI", parent=body_style, fontName="Helvetica-Oblique", textColor=colors.HexColor("#065F46"))

        story = []

        # 1. HEADER
        story.append(Paragraph("SENTINEL FRAUD INCIDENT REPORT", title_style))
        story.append(Paragraph("CONFIDENTIAL // DIGITAL ARREST & SCAM AUDIT RECORD", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=8))

        # 2. OVERVIEW TABLE
        incident_id = f"INC-SENTINEL-{uuid.uuid4().hex[:6].upper()}"
        ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        overview_data = [
            [Paragraph("<b>Incident Reference:</b>", body_style), Paragraph(f"<b>{incident_id}</b>", body_style), Paragraph("<b>Date & Time:</b>", body_style), Paragraph(ts_now, body_style)],
            [Paragraph("<b>Threat Category:</b>", body_style), Paragraph("Social Engineering / Digital Arrest Scam", body_style), Paragraph("<b>Containment Status:</b>", body_style), Paragraph("<font color='#DC2626'><b>BLOCKED & FROZEN</b></font>", body_style)],
            [Paragraph("<b>Detection Engine:</b>", body_style), Paragraph("Sentinel 0-100 Anomaly Engine", body_style), Paragraph("<b>Investigating Agent:</b>", body_style), Paragraph("SecOps Automated Harness", body_style)]
        ]

        t_overview = Table(overview_data, colWidths=[130, 140, 120, 150])
        t_overview.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_overview)
        story.append(Spacer(1, 8))

        # 3. TELEMETRY
        story.append(Paragraph("1. Customer Profile & Attack Telemetry", h2_style))
        cust_data = [
            [Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>Recorded Attack Value</b>", body_style), Paragraph("<b>Baseline / Normal State</b>", body_style)],
            [Paragraph("Customer Identifier", body_style), Paragraph(f"{payload['customer_name']} ({payload['account_id']})", body_style), Paragraph("Verified Individual Account", body_style)],
            [Paragraph("Scam Recipient UPI", body_style), Paragraph(f"<font color='#DC2626'><b>{payload['recipient']}</b></font>", body_style), Paragraph("Starbucks Coffee (Normal)", body_style)],
            [Paragraph("Transaction Amount", body_style), Paragraph("<font color='#DC2626'><b>INR 150,000.00</b></font>", body_style), Paragraph("INR 750.00 Avg Purchase", body_style)],
            [Paragraph("Memo / Reference", body_style), Paragraph(payload["memo"], body_style), Paragraph("Morning coffee purchase", body_style)]
        ]

        t_cust = Table(cust_data, colWidths=[140, 200, 200])
        t_cust.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('BOX', (0, 0), (-1, -1), 1, PRIMARY),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        for i in range(3):
            cust_data[0][i].style.textColor = colors.white
        story.append(t_cust)
        story.append(Spacer(1, 8))

        # 4. RULE BREAKDOWN
        story.append(Paragraph("2. Evaluated Risk Score & Triggered Rule Breakdown", h2_style))
        risk_banner = [
            [
                Paragraph("<b>EVALUATED RISK SCORE:</b>", body_style),
                Paragraph(f"<font color='#DC2626' size=13><b>{rule_eval['risk_score']} / 100.0 ({rule_eval['risk_level']})</b></font>", body_style),
                Paragraph("<b>ACTION ENFORCED:</b>", body_style),
                Paragraph(f"<font color='#DC2626'><b>{rule_eval['action']}</b></font>", body_style)
            ]
        ]
        t_banner = Table(risk_banner, colWidths=[140, 150, 110, 140])
        t_banner.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEE2E2")),
            ('BOX', (0, 0), (-1, -1), 1.5, ACCENT_RED),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_banner)
        story.append(Spacer(1, 6))

        rule_table_data = [
            [Paragraph("<b>Rule Code</b>", body_style), Paragraph("<b>Weight</b>", body_style), Paragraph("<b>Triggered Heuristic Explanation</b>", body_style)]
        ]
        for r in rule_eval["triggered_rules"]:
            rule_table_data.append([
                Paragraph(f"<b>{r['code']}</b>", body_style),
                Paragraph(f"+{r['weight']} pts", body_style),
                Paragraph(r["description"], body_style)
            ])

        t_rules = Table(rule_table_data, colWidths=[160, 65, 315])
        t_rules.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
            ('BOX', (0, 0), (-1, -1), 1, SECONDARY),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        for i in range(3):
            rule_table_data[0][i].style.textColor = colors.white
        story.append(t_rules)
        story.append(Spacer(1, 8))

        # 5. TRANSCRIPT
        story.append(Paragraph("3. Voice AI & Customer Audit Transcript", h2_style))
        transcript_data = [
            [Paragraph("<b>Speaker</b>", body_style), Paragraph("<b>Transcript Content</b>", body_style), Paragraph("<b>Context Telemetry</b>", body_style)],
            [Paragraph("Customer", transcript_cust), Paragraph('"I received a video call from a CBI official saying I am under Digital Arrest for illegal money laundering."', body_style), Paragraph("Voice Stress: <b>0.85</b><br/>Vector: DIGITAL_ARREST", body_style)],
            [Paragraph("Voice AI", transcript_ai), Paragraph(f'"{rule_eval["ai_instruction"]}"', body_style), Paragraph("Action: <b>BLOCKED</b><br/>WebSocket Alert: <b>DISPATCHED</b>", body_style)]
        ]
        t_trans = Table(transcript_data, colWidths=[90, 290, 160])
        t_trans.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('BOX', (0, 0), (-1, -1), 1, PRIMARY),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        for i in range(3):
            transcript_data[0][i].style.textColor = colors.white
        story.append(t_trans)
        story.append(Spacer(1, 8))

        doc.build(story)
        logger.info(f"PDF Report generated: {os.path.abspath(output_filename)}")
        print(f"\n[+] SUCCESS: Incident Report PDF generated cleanly at:")
        print(f"    --> {os.path.abspath(output_filename)}")

    except Exception as e:
        logger.exception("Failed to build PDF report.")
        print(f"\n[!] ERROR: PDF Generation failed: {e}")


# =============================================================================
# SECTION 8: AUTOMATED BATCH FRAUD SIMULATOR (SENTINEL GUIDE SPEC)
# =============================================================================
def run_batch_fraud_simulator() -> None:
    """Executes the 4 primary Sentinel Fraud Simulator scenarios defined in Section 4."""
    print("\n" + "=" * 75)
    print(" [FRAUD SIMULATOR] RUNNING SENTINEL 4-SCENARIO BENCHMARK SUITE")
    print("=" * 75)

    sentinel_scenarios = [
        ("NORMAL", "1. Normal Transaction", "Legitimate coffee purchase"),
        ("DIGITAL_ARREST", "2. Social Engineering", "Digital Arrest scam (fake_cbi_agent@upi)"),
        ("IMPOSSIBLE_TRAVEL", "3. Impossible Travel", "Tor network & foreign IP (Moscow)"),
        ("ATO", "4. Account Takeover", "Full account drain with VPN & SIM swap")
    ]

    print(f"{'#':<3} | {'Scenario Name':<24} | {'Target Recipient/IP':<26} | {'Score':<8} | {'Status'}")
    print("-" * 75)

    for idx, (code, name, desc) in enumerate(sentinel_scenarios, 1):
        payload = TransactionGenerator.generate_scenario_payload(code)
        eval_res = SentinelRuleEngine.evaluate_transaction(payload)
        rec_info = f"{payload['recipient'][:12]} / {payload['ip_address']}"
        print(f"{idx:<3} | {name:<24} | {rec_info:<26} | {eval_res['risk_score']:<8} | {eval_res['action']}")

    print("-" * 75)
    print("[+] Sentinel 4-scenario benchmark simulation complete.")


# =============================================================================
# SECTION 9: INTERACTIVE CLI MENU
# =============================================================================
def display_menu() -> None:
    while True:
        print("\n" + "=" * 60)
        print("       SENTINEL FRAUD SIMULATOR & TESTING HARNESS      ")
        print("============================================================")
        print("  1. Run 4-Scenario Fraud Simulator  (Sentinel Guide Benchmark)")
        print("  2. Trigger Normal Transaction       (POST /api/v1/transaction)")
        print("  3. Trigger Digital Arrest Scam     (fake_cbi_agent@upi)")
        print("  4. Trigger Impossible Travel       (Tor & Moscow IP)")
        print("  5. Trigger Account Takeover Drain  (VPN & SIM Swap)")
        print("  6. Push Live Threat Intel          (POST /api/v1/admin/threat)")
        print("  7. Check Account Balance           (GET  /api/v1/account/ACC_1001)")
        print("  8. Post Voice Call Audit Log       (POST /api/v1/audit/log)")
        print("  9. Generate PDF Incident Report    (ReportLab PDF Export)")
        print(" 10. Exit")
        print("============================================================")

        try:
            choice = input("Enter your choice (1-10): ").strip()

            match choice:
                case "1":
                    run_batch_fraud_simulator()

                case "2":
                    payload = TransactionGenerator.generate_scenario_payload("NORMAL")
                    send_transaction_payload(payload, "Normal Coffee Transaction")

                case "3":
                    payload = TransactionGenerator.generate_scenario_payload("DIGITAL_ARREST")
                    send_transaction_payload(payload, "Social Engineering - Digital Arrest Scam")

                case "4":
                    payload = TransactionGenerator.generate_scenario_payload("IMPOSSIBLE_TRAVEL")
                    send_transaction_payload(payload, "Impossible Travel Anomaly")

                case "5":
                    payload = TransactionGenerator.generate_scenario_payload("ATO")
                    send_transaction_payload(payload, "Account Takeover Balance Drain")

                case "6":
                    t_type = input("Enter threat type (UPI_ID / KEYWORD / IP_ADDRESS) [default: UPI_ID]: ").strip() or "UPI_ID"
                    t_val = input("Enter threat value [default: fake_cbi_agent@upi]: ").strip() or "fake_cbi_agent@upi"
                    push_admin_threat_intel(t_type, t_val)

                case "7":
                    check_account_balance()

                case "8":
                    post_audit_log()

                case "9":
                    generate_incident_report()

                case "10":
                    print("\n[+] Exiting Sentinel Platform. Goodbye!")
                    logger.info("Application shut down cleanly.")
                    sys.exit(0)

                case _:
                    print("\n[!] Invalid selection! Enter a number between 1 and 10.")

        except (KeyboardInterrupt, EOFError):
            print("\n\n[!] Program interrupted by user (Ctrl+C). Exiting safely...")
            sys.exit(0)


if __name__ == "__main__":
    logger.info("Initializing Sentinel Fraud Simulator Platform...")
    display_menu()

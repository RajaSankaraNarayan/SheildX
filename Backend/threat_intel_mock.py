# Realistic (but simulated) Threat Intelligence Datasets

BLACKLISTED_IPS = [
    "185.15.2.14", "193.201.224.230", "45.132.2.111", "103.111.82.5", "192.168.1.99"
]

SUSPICIOUS_ASNS = [
    "AS21034", # Mock sketchy bulletproof host
    "AS40921"
]

HIGH_RISK_COUNTRIES = [
    "KP", "IR", "SY", "CU", "SD", "RU" # Sanctioned or high risk
]

KNOWN_PHISHING_DOMAINS = [
    "secure-update-bank.com", "verify-kyc-now.info", "portal-login-auth.net"
]

DISPOSABLE_EMAIL_DOMAINS = [
    "mailinator.com", "10minutemail.com", "guerrillamail.com"
]

KNOWN_MULE_ACCOUNTS = [
    "ACC_MULE_001", "ACC_MULE_002", "ACC_MULE_003"
]

HIGH_RISK_MCCS = [
    "6051", # Non-Financial Institutions – Foreign Currency, Liquid Assets
    "7995", # Gambling
    "4829"  # Money Transfer
]

def get_threat_intel():
    return {
        "BLACKLISTED_IPS": BLACKLISTED_IPS,
        "SUSPICIOUS_ASNS": SUSPICIOUS_ASNS,
        "HIGH_RISK_COUNTRIES": HIGH_RISK_COUNTRIES,
        "KNOWN_PHISHING_DOMAINS": KNOWN_PHISHING_DOMAINS,
        "DISPOSABLE_EMAIL_DOMAINS": DISPOSABLE_EMAIL_DOMAINS,
        "KNOWN_MULE_ACCOUNTS": KNOWN_MULE_ACCOUNTS,
        "HIGH_RISK_MCCS": HIGH_RISK_MCCS
    }

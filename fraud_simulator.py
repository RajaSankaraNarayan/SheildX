import requests
import json
import time
import random
from faker import Faker

fake = Faker('en_IN')
API_URL = "http://127.0.0.1:8000/api/v1/transaction"

def print_result(scenario: str, response: dict):
    print(f"\n{'='*50}")
    print(f"SCENARIO: {scenario}")
    print(f"Status: {response.get('status')}")
    print(f"Risk Level: {response.get('risk_level')} ({response.get('risk_score')}/100)")
    print("Triggered Rules:")
    for reason in response.get('reasons', []):
        print(f"  - {reason}")
    print(f"AI Instruction: {response.get('ai_instruction')}")
    print(f"{'='*50}\n")

def simulate_normal_transaction():
    payload = {
        "account_id": "ACC_IND_001",
        "amount": 1500.0,
        "recipient": fake.name(),
        "device_ip": "192.168.1.10",
        "is_new_device": False,
        "memo": "Dinner split",
        "merchant_country": "IN",
        "device_trust_score": 0.95
    }
    resp = requests.post(API_URL, json=payload).json()
    print_result("Normal Transaction", resp)

def simulate_account_takeover():
    payload = {
        "account_id": "ACC_IND_001",
        "amount": 540000.0, # Account Drain
        "recipient": "scammer@upi", # Known Mule
        "device_ip": "185.15.2.14", # Blacklisted
        "is_new_device": True,
        "os": "Android",
        "is_vpn": True,
        "failed_logins_24h": 5
    }
    resp = requests.post(API_URL, json=payload).json()
    print_result("Account Takeover & Drain", resp)

def simulate_social_engineering_scam():
    payload = {
        "account_id": "ACC_IND_001",
        "amount": 50000.0, # Round number
        "recipient": "CBI Officer Sharma", # Scam keyword
        "device_ip": "10.0.0.5",
        "is_new_device": False,
        "memo": "Digital arrest clearance",
        "device_trust_score": 0.8
    }
    resp = requests.post(API_URL, json=payload).json()
    print_result("Social Engineering (Digital Arrest)", resp)

def simulate_impossible_travel():
    payload = {
        "account_id": "ACC_IND_001",
        "amount": 25000.0,
        "recipient": "Crypto Exchange LTD",
        "device_ip": "89.187.160.0",
        "merchant_country": "RU", # High risk
        "is_new_device": True,
        "is_tor": True,
        "international_tx": True
    }
    resp = requests.post(API_URL, json=payload).json()
    print_result("Impossible Travel & Tor Network", resp)

if __name__ == "__main__":
    print("Running Fraud Simulator against Sentinel Backend...")
    time.sleep(1)
    
    simulate_normal_transaction()
    time.sleep(1)
    
    simulate_social_engineering_scam()
    time.sleep(1)
    
    simulate_impossible_travel()
    time.sleep(1)
    
    simulate_account_takeover()
    print("Simulation complete. Check the 'reports' folder for Incident Reports on Critical threats.")

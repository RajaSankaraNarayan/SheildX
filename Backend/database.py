import sqlite3
import datetime
import uuid

DB_NAME = "sentinel.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        account_id TEXT PRIMARY KEY,
        user_name TEXT,
        balance REAL,
        status TEXT,
        voice_pin TEXT,
        language_pref TEXT DEFAULT 'EN'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        account_id TEXT,
        amount REAL,
        recipient TEXT,
        device_ip TEXT,
        status TEXT,
        risk_score REAL,
        timestamp DATETIME,
        FOREIGN KEY (account_id) REFERENCES accounts (account_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id TEXT PRIMARY KEY,
        account_id TEXT,
        transaction_id TEXT,
        transcript TEXT,
        identified_vector TEXT,
        voice_stress_score REAL,
        timestamp DATETIME
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS threat_intelligence (
        threat_id TEXT PRIMARY KEY,
        threat_type TEXT,
        value TEXT,
        timestamp DATETIME
    )
    ''')

    # Seed data
    cursor.execute("SELECT account_id FROM accounts WHERE account_id = 'ACC_IND_001'")
    if not cursor.fetchone():
        cursor.execute('''
        INSERT INTO accounts (account_id, user_name, balance, status, voice_pin, language_pref)
        VALUES ('ACC_IND_001', 'Rajesh Kumar', 550000.00, 'NORMAL', '1234', 'HI')
        ''')

    # Seed some default threat intel
    cursor.execute("SELECT threat_id FROM threat_intelligence")
    if not cursor.fetchone():
        default_threats = [
            ("KEYWORD", "cbi"), ("KEYWORD", "customs"), ("KEYWORD", "fedex"),
            ("KEYWORD", "kyc"), ("KEYWORD", "electricity"), ("KEYWORD", "jio tower"),
            ("KEYWORD", "digital arrest"), ("KEYWORD", "kbc"), ("KEYWORD", "lottery"),
            ("UPI_ID", "scammer@upi"), ("IP_ADDRESS", "192.168.1.99")
        ]
        now = datetime.datetime.now()
        for t_type, val in default_threats:
            cursor.execute('''
            INSERT INTO threat_intelligence (threat_id, threat_type, value, timestamp)
            VALUES (?, ?, ?, ?)
            ''', (str(uuid.uuid4()), t_type, val, now))
    
    conn.commit()
    conn.close()

def get_account(account_id: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_account_status(account_id: str, status: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET status = ? WHERE account_id = ?", (status, account_id))
    conn.commit()
    conn.close()

def create_transaction(account_id: str, amount: float, recipient: str, device_ip: str, status: str, risk_score: float):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    tx_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    cursor.execute('''
    INSERT INTO transactions (transaction_id, account_id, amount, recipient, device_ip, status, risk_score, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tx_id, account_id, amount, recipient, device_ip, status, risk_score, now))
    conn.commit()
    conn.close()
    return tx_id

def create_audit_log(account_id: str, transcript: str, identified_vector: str, transaction_id: str = None, voice_stress_score: float = None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    log_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    cursor.execute('''
    INSERT INTO audit_logs (log_id, account_id, transaction_id, transcript, identified_vector, voice_stress_score, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (log_id, account_id, transaction_id, transcript, identified_vector, voice_stress_score, now))
    conn.commit()
    conn.close()
    return log_id

def add_threat_intel(threat_type: str, value: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    threat_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    cursor.execute('''
    INSERT INTO threat_intelligence (threat_id, threat_type, value, timestamp)
    VALUES (?, ?, ?, ?)
    ''', (threat_id, threat_type, value, now))
    conn.commit()
    conn.close()
    return threat_id

def get_all_threats():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT threat_type, value FROM threat_intelligence")
    rows = cursor.fetchall()
    conn.close()
    
    threats = {"KEYWORD": [], "UPI_ID": [], "IP_ADDRESS": []}
    for row in rows:
        t_type = row["threat_type"]
        if t_type in threats:
            threats[t_type].append(row["value"].lower())
    return threats

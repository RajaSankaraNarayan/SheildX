from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from contextlib import asynccontextmanager
from typing import List

from models import TransactionCreate, AccountAction, AuditLogCreate, TransactionResponse, ThreatIntelCreate
import database
from anomaly_engine import evaluate_transaction
from report_generator import generate_pdf_report

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize and seed database on startup
    database.init_db()
    yield
    # Clean up on shutdown if needed

app = FastAPI(title="Sentinel Backend", lifespan=lifespan)

# Add CORS middleware for Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for hackathon demo
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (including OPTIONS preflight)
    allow_headers=["*"],
)

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We just need to keep the connection open to send alerts
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/v1/transaction", response_model=TransactionResponse)
async def create_transaction_endpoint(tx_data: TransactionCreate):
    # Check if account exists
    account = database.get_account(tx_data.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if account["status"] == "FROZEN":
        raise HTTPException(status_code=400, detail="Account is frozen")

    # Run anomaly engine
    risk_score, is_fraud, risk_level, reasons = evaluate_transaction(tx_data, account)
    
    tx_status = "COMPLETED"
    ai_instruction = None
    
    if is_fraud:
        tx_status = "PENDING_REVIEW"
        database.update_account_status(tx_data.account_id, "SUSPICIOUS")
        
        # Generate PDF report for Critical incidents
        if risk_level == "Critical Risk":
            # Using dict() on the pydantic model to pass data easily
            generate_pdf_report(tx_data.dict(), risk_score, risk_level, reasons)
        
        # Map reasons to AI instructions
        if "ACCOUNT_DRAIN" in reasons:
            ai_instruction = "Refuse the transfer. Warn the user that this will drain their entire account and ask if they are sure."
        elif "SUSPICIOUS_KEYWORD" in reasons:
            ai_instruction = "Refuse the transfer. Gently explain that government agencies like CBI, Police, or Customs never ask for instant wire transfers or UPI payments. Ask if someone is threatening them with digital arrest."
        elif "ROUND_NUMBER_LARGE" in reasons:
            ai_instruction = "Pause the transfer. Ask the user why they are sending a large, even amount."
        elif "MICRO_PROBING" in reasons:
            ai_instruction = "Flag the transfer. Warn the user that someone might be testing their UPI ID with a small amount."
        else:
            ai_instruction = "Pause the transfer. This looks highly suspicious. Ask the user to verify the recipient."
        
    # Save transaction
    tx_id = database.create_transaction(
        account_id=tx_data.account_id,
        amount=tx_data.amount,
        recipient=tx_data.recipient,
        device_ip=tx_data.device_ip,
        status=tx_status,
        risk_score=risk_score
    )
    
    if is_fraud:
        # Broadcast alert to all connected WebSocket clients
        alert_payload = {
            "event": "FRAUD_ALERT",
            "account_id": tx_data.account_id,
            "transaction_id": tx_id,
            "vector": reasons[0] if reasons else "UNKNOWN_VECTOR",
            "reasons": reasons
        }
        await manager.broadcast(json.dumps(alert_payload))
        
    return {
        "message": "Transaction processed", 
        "transaction_id": tx_id, 
        "status": tx_status, 
        "risk_score": float(risk_score), 
        "risk_level": risk_level,
        "reasons": reasons,
        "ai_instruction": ai_instruction
    }


@app.post("/api/v1/account/{account_id}/action")
async def account_action_endpoint(account_id: str, action_req: AccountAction):
    account = database.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if action_req.action == "FREEZE_ACCOUNT":
        database.update_account_status(account_id, "FROZEN")
        return {"message": "Account frozen successfully"}
    elif action_req.action == "VOID_TRANSACTION":
        # In a full implementation, this would cancel a specific transaction
        # For now we'll just acknowledge it
        return {"message": "Action VOID_TRANSACTION received"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@app.post("/api/v1/audit/log")
async def create_audit_log_endpoint(audit_data: AuditLogCreate):
    log_id = database.create_audit_log(
        account_id=audit_data.account_id,
        transaction_id=audit_data.transaction_id,
        transcript=audit_data.transcript,
        identified_vector=audit_data.identified_vector,
        voice_stress_score=audit_data.voice_stress_score
    )
    return {"message": "Audit log saved successfully", "log_id": log_id}

@app.get("/api/v1/account/{account_id}")
async def get_account_endpoint(account_id: str):
    account = database.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {
        "balance": account["balance"],
        "status": account["status"],
        "language_pref": account["language_pref"]
    }

@app.post("/api/v1/admin/threat")
async def add_threat_intel_endpoint(threat_data: ThreatIntelCreate):
    valid_types = ["KEYWORD", "UPI_ID", "IP_ADDRESS"]
    if threat_data.threat_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid threat type")
        
    threat_id = database.add_threat_intel(threat_data.threat_type, threat_data.value)
    return {"message": "Threat intel added successfully", "threat_id": threat_id}

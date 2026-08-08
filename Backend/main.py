from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import json
import uuid
import datetime
import tempfile
import os
import base64
import httpx
from dotenv import load_dotenv
from google import genai
from contextlib import asynccontextmanager

load_dotenv(os.path.join(os.path.dirname(__file__), "../fintech/fintech/.env"))

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
            
        import os
        with open("latest_alert.txt", "w") as f:
            f.write(ai_instruction)
        
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
            "reasons": reasons,
            "ai_instruction": ai_instruction
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
        transcript=audit_data.transcript,
        identified_vector=audit_data.identified_vector,
        transaction_id=audit_data.transaction_id,
        voice_stress_score=audit_data.voice_stress_score
    )
    
    # Broadcast to frontend that the Voice AI has finished its intervention
    payload = {
        "event": "VOICE_CALL_COMPLETED",
        "status": "success",
        "ai_resolution": f"AI Action: {audit_data.status}"
    }
    await manager.broadcast(json.dumps(payload))
    
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


# ==========================================
# WALKIE-TALKIE VOICE ASSISTANT ENDPOINT
# ==========================================

class TTSRequest(BaseModel):
    text: str

@app.post("/api/v1/tts_alert")
async def tts_alert_endpoint(req: TTSRequest):
    sarvam_key = os.getenv("SARVAM_API_KEY")
    if not sarvam_key:
        raise HTTPException(status_code=500, detail="Missing API keys")
        
    async with httpx.AsyncClient(timeout=30.0) as client:
        tts_res = await client.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": sarvam_key, "Content-Type": "application/json"},
            json={
                "inputs": [req.text],
                "target_language_code": "hi-IN",
                "speaker": "shubh",
                "pace": 1.1,
                "speech_sample_rate": 16000,
                "enable_preprocessing": True,
                "model": "bulbul:v3"
            }
        )
    if tts_res.status_code != 200:
        raise HTTPException(status_code=500, detail="TTS failed")
        
    audio_base64 = tts_res.json()["audios"][0]
    import base64
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(base64.b64decode(audio_base64))
        out_path = temp_audio.name
        
    return FileResponse(out_path, media_type="audio/wav")

@app.post("/api/v1/support_voice")
async def support_voice_endpoint(file: UploadFile = File(...)):
    sarvam_key = os.getenv("SARVAM_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not sarvam_key or not gemini_key:
        raise HTTPException(status_code=500, detail="Missing API keys")

    # 1. Save incoming audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        audio_path = temp_audio.name

    try:
        # 2. Sarvam STT
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(audio_path, "rb") as f:
                stt_res = await client.post(
                    "https://api.sarvam.ai/speech-to-text-translate",
                    headers={"api-subscription-key": sarvam_key},
                    files={"file": (os.path.basename(audio_path), f, "audio/webm")},
                    data={"prompt": "", "model": "saaras:v3"}
                )
        if stt_res.status_code != 200:
            raise Exception(f"STT failed: {stt_res.text}")
            
        transcript = stt_res.json().get("transcript", "")
        if not transcript.strip():
            # Graceful fallback if user didn't speak clearly
            ai_text = "I didn't quite catch that. Could you please repeat?"
            ai_lang = "en-IN"
        else:
            # Read dynamic warning from alert file
            dynamic_warning = "We detected an unauthorized transaction. Did you authorize this?"
            alert_path = "latest_alert.txt"
            if os.path.exists(alert_path):
                with open(alert_path, "r") as f:
                    content = f.read().strip()
                    if content:
                        dynamic_warning = content

            # Load original prompt from fintech module
            import sys
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../fintech/fintech")))
            try:
                from prompts import SYSTEM_PROMPT
                base_prompt = SYSTEM_PROMPT.replace("{DYNAMIC_WARNING}", dynamic_warning)
            except Exception as e:
                print("Failed to load original prompt:", e)
                base_prompt = "You are Sentinel Voice AI, an Indian banking assistant."
            
            # 3. Gemini LLM (Multilingual Auto-Detect) WITHOUT global history
            ai_client = genai.Client(api_key=gemini_key)
            sys_prompt = f"""{base_prompt}
            
CRITICAL TECHNICAL INSTRUCTION:
Answer quickly (under 3 sentences).
You MUST detect the language the user is speaking in, and respond in that EXACT same language!
You MUST format your final output strictly as a JSON object with no markdown wrappers: 
{{"language_code": "code", "text": "your response"}}
Valid codes: hi-IN, bn-IN, ta-IN, te-IN, mr-IN, gu-IN, kn-IN, ml-IN, pa-IN, or-IN, en-IN.
"""
            
            llm_response = ai_client.models.generate_content(
                model='gemini-flash-latest',
                contents=transcript,
                config=genai.types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    response_mime_type="application/json"
                )
            )

            import json
            import re
            try:
                raw_text = llm_response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                    
                ai_data = json.loads(raw_text)
                ai_text = ai_data.get("text", "I'm sorry, I couldn't process that.")
                ai_lang = ai_data.get("language_code", "hi-IN")
                
                # Force format if Gemini outputs short codes like "ta" instead of "ta-IN"
                if len(ai_lang) == 2:
                    ai_lang = f"{ai_lang}-IN"
            except Exception as e:
                print("JSON Parse Error:", e)
                # Safe fallback text that doesn't dictate code
                ai_text = "I apologize, I am having trouble understanding that right now."
                ai_lang = "hi-IN"

        # 4. Sarvam TTS
        async with httpx.AsyncClient(timeout=30.0) as client:
            tts_res = await client.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={"api-subscription-key": sarvam_key, "Content-Type": "application/json"},
                json={
                    "inputs": [ai_text],
                    "target_language_code": ai_lang,
                    "speaker": "shubh",
                    "pace": 1.1,
                    "speech_sample_rate": 16000,
                    "enable_preprocessing": True,
                    "model": "bulbul:v3"
                }
            )
            
        if tts_res.status_code != 200:
            raise Exception(f"TTS failed: {tts_res.text}")
            
        tts_data = tts_res.json()
        audio_base64 = tts_data["audios"][0]
        
        # 5. Return Audio
        out_path = audio_path.replace(".webm", "_out.wav")
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(audio_base64))
            
        return FileResponse(out_path, media_type="audio/wav")

    except Exception as e:
        print(f"Voice pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.remove(audio_path)
        except:
            pass

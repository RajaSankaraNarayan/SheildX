# pipeline.py
import logging
from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

# Try loading from the new universal aggregator path
try:
    from pipecat.processors.aggregators.llm_response_universal import (
        LLMContextAggregatorPair,
        LLMUserAggregatorParams,
        LLMAssistantAggregatorParams
    )
except ImportError:
    from pipecat.processors.aggregators.llm_response import (
        LLMContextAggregatorPair,
        LLMUserAggregatorParams,
        LLMAssistantAggregatorParams
    )

# Try loading LLMContext from appropriate modules
try:
    from pipecat.processors.aggregators.llm_context import LLMContext
except ImportError:
    from pipecat.processors.aggregators.llm_response import LLMContext

import config
from prompts import SYSTEM_PROMPT

logger = logging.getLogger("sentinel.pipeline")

# Keywords in user transcripts to map security state changes
PIN_TRIGGERS = ["1234", "one two three four", "1 2 3 4"]
FREEZE_TRIGGERS = [
    "freeze my card",
    "lock it",
    "freeze kardo",
    "aama lock pannunga",
    "lock my card",
    "freeze card",
    "card freeze",
    "lock pannunga",
    "freeze karo",
    "lock kardo",
    "freeze pannu"
]

def check_and_audit_triggers(text: str, speaker: str, audit_engine):
    """
    Parses speech transcripts to track milestones in state audit.
    """
    if not text:
        return
        
    t = text.lower()
    if speaker == "User":
        # Check if correct PIN is spoken
        for pin in PIN_TRIGGERS:
            if pin in t:
                audit_engine.log_event("PIN_VERIFICATION_SUCCESS", f"User stated voice PIN: {text}")
                return
        
        # Check if card locking is requested
        for trigger in FREEZE_TRIGGERS:
            if trigger in t:
                audit_engine.log_event("CARD_FROZEN", f"User requested block: '{text}'")
                return

def create_pipeline(transport, audit_engine, dynamic_warning: str) -> Pipeline:
    """
    Initializes standard voice pipeline services:
    VAD -> STT (Sarvam) -> LLM (Gemini 1.5 Flash) -> TTS (Sarvam) -> Transport
    """
    # 1. Voice Activity Detection (VAD)
    vad_analyzer = SileroVADAnalyzer(
        params=VADParams(
            confidence=0.7,
            start_secs=0.2,
            stop_secs=0.3
        )
    )

    # 2. Sarvam Speech-to-Text (STT) Service
    # Uses regional 'saaras:v3' model optimized for Indian languages
    try:
        stt = SarvamSTTService(
            api_key=config.SARVAM_API_KEY,
            settings=SarvamSTTService.Settings(model="saaras:v3")
        )
    except AttributeError:
        stt = SarvamSTTService(
            api_key=config.SARVAM_API_KEY,
            model="saaras:v3"
        )

    # 3. Gemini 1.5 Flash (Google LLM) Service
    try:
        llm = GoogleLLMService(
            api_key=config.GEMINI_API_KEY,
            settings=GoogleLLMService.Settings(
                model="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT.replace("{DYNAMIC_WARNING}", dynamic_warning)
            )
        )
    except AttributeError:
        llm = GoogleLLMService(
            api_key=config.GEMINI_API_KEY,
            model="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT.replace("{DYNAMIC_WARNING}", dynamic_warning)
        )

    # 4. Sarvam Text-to-Speech (TTS) Service
    # Employs regional 'bulbul:v3' model with default Indian voice
    try:
        tts = SarvamTTSService(
            api_key=config.SARVAM_API_KEY,
            settings=SarvamTTSService.Settings(model="bulbul:v3", voice="shubh")
        )
    except AttributeError:
        tts = SarvamTTSService(
            api_key=config.SARVAM_API_KEY,
            model="bulbul:v3",
            voice="shubh"
        )

    # 5. Conversation Context Initialization
    # Pre-seeding user greeting "Hello" prompts the model to trigger its system rules immediately
    context = LLMContext()
    context.add_message({"role": "user", "content": "Hello"})
    
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=vad_analyzer),
        assistant_params=LLMAssistantAggregatorParams()
    )

    # 6. Bind Dialog Log Handlers
    @user_aggregator.event_handler("on_user_turn_stopped")
    async def on_user_turn_stopped(aggregator, strategy, message):
        content = ""
        if hasattr(message, "content"):
            content = message.content
        elif isinstance(message, str):
            content = message
            
        if content:
            audit_engine.log_message("User", content)
            check_and_audit_triggers(content, "User", audit_engine)

    @assistant_aggregator.event_handler("on_assistant_turn_stopped")
    async def on_assistant_turn_stopped(aggregator, message):
        content = ""
        if hasattr(message, "content"):
            content = message.content
        elif isinstance(message, str):
            content = message
            
        if content:
            audit_engine.log_message("Assistant", content)
            check_and_audit_triggers(content, "Assistant", audit_engine)

    # 7. Wire pipeline flow
    pipeline = Pipeline([
        transport.input(),
        stt,
        user_aggregator,
        llm,
        tts,
        transport.output(),
        assistant_aggregator
    ])

    return pipeline

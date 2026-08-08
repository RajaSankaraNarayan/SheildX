# agent.py
import asyncio
import logging
try:
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask, PipelineParams
except ImportError:
    from pipecat.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.frames.frames import LLMRunFrame, EndFrame

# Handle import variations for SingleClientWebsocketServerTransport dynamically
try:
    from pipecat.transports.websocket.server import (
        SingleClientWebsocketServerTransport,
        SingleClientWebsocketServerParams
    )
except ImportError:
    try:
        from pipecat.transports.network.websocket_server import (
            SingleClientWebsocketServerTransport,
            SingleClientWebsocketServerParams
        )
    except ImportError:
        # Fallback to legacy naming conventions if required
        from pipecat.transports.network.websocket_server import (
            WebsocketServerTransport as SingleClientWebsocketServerTransport,
            WebsocketServerParams as SingleClientWebsocketServerParams
        )

import config
from audit import AuditEngine
from pipeline import create_pipeline

logger = logging.getLogger("sentinel.agent")

async def main():
    # 1. Enforce environment credentials configuration
    config.validate_config()
    
    while True:
        try:
            # 2. Setup the auditing state for this lifecycle
            audit_engine = AuditEngine()
            audit_engine.log_event("SESSION_START", "Sentinel security session initialized.")
            
            # Read dynamic instruction
            dynamic_warning = "We detected an unauthorized transaction. Did you authorize this?"
            import os
            # agent.py is in SheildX/fintech/fintech, latest_alert.txt is in SheildX/
            alert_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "latest_alert.txt")
            if os.path.exists(alert_path):
                with open(alert_path, "r") as f:
                    content = f.read().strip()
                    if content:
                        dynamic_warning = content
            
            # 3. Initialize WebSocket single-client connection parameters
            params = SingleClientWebsocketServerParams(
                audio_out_enabled=True,
                add_wav_header=True,
                serializer=ProtobufFrameSerializer()
            )
            
            transport = SingleClientWebsocketServerTransport(
                host=config.HOST,
                port=config.PORT,
                params=params
            )
            
            # 4. Construct pipeline and map contextual turn events
            pipeline = create_pipeline(transport, audit_engine, dynamic_warning)
            
            # 5. Bind pipeline worker task and runner
            task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
            runner = PipelineRunner()
            
            # 6. WebSocket Connection lifecycle hooks
            @transport.event_handler("on_client_connected")
            async def on_client_connected(transport, client):
                logger.info(f"Connected to browser audio interface: {client}")
                audit_engine.log_event("CLIENT_CONNECTED", f"Client address: {client}")
                # Send LLMRunFrame to process initial state rules
                await task.queue_frames([LLMRunFrame()])
                
            @transport.event_handler("on_client_disconnected")
            async def on_client_disconnected(transport, client):
                logger.info(f"Browser audio interface disconnected: {client}")
                audit_engine.log_event("SESSION_DISCONNECTED", "Client closed connection.")
                # Queue clean shutdown frame
                await task.queue_frames([EndFrame()])
                
            # 7. Run WebSocket server loop with async lifecycle protection
            logger.info(f"Starting Sentinel Voice AI server at ws://{config.HOST}:{config.PORT}...")
            await runner.run(task)
            
            # Guarantee dispatching audit logs on loop exit
            audit_engine.log_event("SESSION_END", "Sentinel security session completed.")
            await audit_engine.send_audit_report(config.AUDIT_LOG_URL, config.ACCOUNT_ID)
            logger.info("Graceful shutdown sequence complete. Waiting for next caller...")
            
        except asyncio.CancelledError:
            logger.warning("Pipeline task cancellation requested.")
            break
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt captured. Cleaning up agent...")
            break
        except Exception as ex:
            logger.exception(f"Unexpected runtime error in Voice AI agent: {str(ex)}")
            try:
                audit_engine.log_event("SESSION_CRASHED", f"Error: {str(ex)}")
            except:
                pass
            await asyncio.sleep(1) # Prevent tight loop on error

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

from src.helpers import get_settings
from livekit.plugins import deepgram, google, silero, groq
from src.main import session_factory as async_session_maker

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    cli,
)
from .tools import BookingAgent
from src.services import RouteService

settings = get_settings()

# Initialize the LiveKit agent server, which manages worker sessions.
server = AgentServer(
    ws_url=settings.LIVEKIT_URL,
    api_key=settings.LIVEKIT_API_KEY,
    api_secret=settings.LIVEKIT_API_SECRET,
)


# Register the function that LiveKit calls when a new session is assigned to this worker.
@server.rtc_session()
async def my_agent(ctx: JobContext):
        
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    async with async_session_maker() as db:
        route_service = RouteService(session=db)
        cities = await route_service.get_available_cities()

    session = AgentSession(
    stt=deepgram.STT(
                    model="nova-3",
                    api_key=settings.DEEPGRAM_API_KEY,
                    language="en",
                    keyterm=cities,
                    endpointing_ms=1000,
                    ),
    llm=groq.LLM(model="openai/gpt-oss-20b", api_key=settings.GROQ_API_KEY),
    tts=deepgram.TTS(api_key=settings.DEEPGRAM_API_KEY),
    vad=silero.VAD.load(),
        # LiveKit decides when the customer's turn is over (separate from Deepgram's endpointing_ms).
    # Wait longer before answering, and don't start the LLM before the turn is confirmed.
    turn_handling=TurnHandlingOptions(
    endpointing={"mode": "fixed", "min_delay": 1.0, "max_delay": 4.0},
    preemptive_generation={"enabled": False},
    )
    )

    await ctx.connect()
    await session.start(agent=BookingAgent(), room=ctx.room)


    await session.generate_reply(
        instructions="Greet the user briefly and ask how you can help."
    )

if __name__ == "__main__":
    cli.run_app(server)

from helpers import get_settings
from livekit.plugins import deepgram, google, silero, groq

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
)
from .tools import BookingAgent

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

    session = AgentSession(
    stt=deepgram.STT(model="nova-3", api_key=settings.DEEPGRAM_API_KEY),
    llm=groq.LLM(model="openai/gpt-oss-20b", api_key=settings.GROQ_API_KEY),
    tts=deepgram.TTS(api_key=settings.DEEPGRAM_API_KEY),
    vad=silero.VAD.load(),
    )

    await session.start(agent=BookingAgent(), room=ctx.room)
    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user briefly and ask how you can help."
    )


if __name__ == "__main__":
    cli.run_app(server)

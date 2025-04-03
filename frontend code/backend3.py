#code which is deployed
import os
import csv
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero, turn_detector
from livekit.plugins.aws.tts import TTS as PollyTTS
from livekit.plugins.aws.stt import STT as TranscribeSTT
from livekit.api import DeleteRoomRequest
from livekit.plugins import deepgram
 
import redis
import time
 
 
from services.loader import load_service
import json
 
load_dotenv(dotenv_path=".env.local")

 
# Connect to Azure Redis
redis_client = redis.StrictRedis(
    # host='your-redis-name.redis.cache.windows.net',
    host='RedisLivekit.redis.cache.windows.net',
    port=6380,
    # password='your-access-key',
    password='zpir55fUl0BFP6cBXykbyWqfHN1ZBj22AAzCaF6YHSQ=',
    ssl=True,
    decode_responses=True,
    db=0
)
DEFAULT_LANGUAGE = "English"
redis_client.set("selected_lang", DEFAULT_LANGUAGE)
DEFAULT_CONTEXT = "hello, my name is Abhilash"
redis_client.set("context", DEFAULT_CONTEXT)
 

stt_model_selected = "deepgram"

 
 
cerebras_api_key = os.getenv("CEREBRAS_API_KEY")
 

 
# -------------------- LOAD ENV VARIABLES -------------------- #
 
# -------------------- AWS CONFIGURATION -------------------- #
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
# aws_region = os.getenv("AWS_REGION", "us-east-1")
 
# -------------------- STT & TTS PLUGINS (Amazon) -------------------- #
amazon_stt = TranscribeSTT(
    speech_region="us-east-1",
    api_key=aws_access_key,
    api_secret=aws_secret_key,
    sample_rate=48000,
    language="en-IN",
    encoding="pcm",
    enable_partial_results_stabilization=True,
    partial_results_stability="high",
    show_speaker_label=False,
)
 
polly_tts = PollyTTS(
    voice="Kajal",
    language="en-IN",
    speech_engine="generative",
    sample_rate=16000,
    speech_region="us-east-1",
    api_key=aws_access_key,
    api_secret=aws_secret_key,
)
from livekit.plugins.cartesia import tts
cartesia_tts =tts.TTS(
 
            model="sonic-2",
            voice="3b554273-4299-48b9-9aaf-eefd438e3941",
            speed=-0.2,
            # speed = 0.3
            # emotion=["angry:high"]
        )
# -------------------- LOGGING SETUP -------------------- #
logger = logging.getLogger("voice-assistant")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
 
# -------------------- INITIALIZATION -------------------- #
 
 
 
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
 
async def entrypoint(ctx: JobContext):
    """Main function that runs the AI voice agent."""
 
    speech_rate = os.getenv("POLLY_SPEECH_RATE", "130%")  # Default to 130%
   
   
    print("/n /n hiiiii /n \n \n ")
    # system_instructions = await redis_client.get("context")
    system_instructions = redis_client.get("context") or " "
    languageselected = redis_client.get("selected_lang") or "English"
    tts_model_selected_value = redis_client.get("selected_tts_provider") or "openai"    
    tts_model_selected = tts_model_selected_value.lower()
    # tts_model_selected = "cartesia"
    voicename = redis_client.get("selected_voice") or "shimmer"
    # voicename = "Kajal"
    selected_llm_value = redis_client.get("selected_llm") or "openai"
    selected_llm = selected_llm_value.lower()
 
 
   
    print(f"\n--------------------------- language selected {languageselected} -------------------------------\n")
    print(f"\n--------------------------- stt model selected {stt_model_selected} -------------------------------\n")
    print(f"\n --------------------------voice  selected {voicename} ----------------------------------- \n")
    print(f"\n --------------------------llm selected {selected_llm} ----------------------------------- \n")
    print(f"\n --------------------------tts model selected {tts_model_selected} ----------------------------------- \n")
    llm_model = load_service("llm",selected_llm)
    stt_model = load_service("stt",stt_model_selected,language=languageselected)
    tts_model = load_service("tts", tts_model_selected, voice=voicename)
    initial_ctx = llm.ChatContext().append(role="system", text=system_instructions)
 
   
    room = ctx.room
    logger.info(f"Connecting to room {ctx.room.name}")
    redis_client.set("room_name",ctx.room.name)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
 
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting assistant for participant {participant.identity}")
   
    # Initialize the agent with SSML
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        # stt=amazon_stt,
        stt =stt_model,
        # llm=openai.LLM.with_groq(),
        llm = llm_model,
        tts=tts_model,
        # tts = cartesia_tts,
        chat_ctx=initial_ctx,
        #turn_detector=turn_detector.EOUModel(),
        min_endpointing_delay=0.1,
       # noise_cancellation=noise_cancellation.NC(),
        # noise_cancellation=noise_cancellation.BVC(),
       
       
       
    )
 
    agent.start(ctx.room, participant)
 
    usage_collector = metrics.UsageCollector()
 
    @agent.on("metrics_collected")
    def on_metrics_collected(mtrcs: metrics.AgentMetrics):
    #     sequence_id = mtrcs.sequence_id  
    #     log_metrics(sequence_id, mtrcs)
        usage_collector.collect(mtrcs)
 
    async def log_usage():
        """Logs final aggregated metrics at session end."""
        summary = usage_collector.get_summary()
        logger.info(f"{summary}")
        # log_metrics("SESSION-END", summary)
   
 
 
 
    ctx.add_shutdown_callback(log_usage)    
   
 
 
# -------------------- START WORKER -------------------- #
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
 
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    RoomInputOptions,
    cli,
    function_tool,
    RunContext,
    MetricsCollectedEvent,
    metrics
)

from livekit.plugins import google, deepgram, murf, silero, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env.local")
logger = logging.getLogger("agent")

# ---------------------------------------------------------
# LOAD PW FAQ CONTENT
# ---------------------------------------------------------
CONTENT_PATH = Path(__file__).parent.parent / "shared-data/pw_content.json"

DEFAULT_CONTENT = {
    "company": {
        "name": "Physics Wallah",
        "description": "PW is India’s leading affordable EdTech platform offering courses for NEET, JEE, UPSC and countless competitive exams.",
        "mission": "Deliver high-quality education at the lowest price in India."
    },

    "faq": [
        {"q": "What is PW?", "a": "PW is an affordable EdTech platform offering online & offline classes for competitive exams in India."},
        {"q": "Is there a free trial?", "a": "Yes! Many PW courses include free demo lectures and sample chapter tests."},
        {"q": "What courses do you offer?", "a": "PW offers courses for NEET, JEE, UPSC, GATE, banking, and school-level boards."},
        {"q": "Who are PW teachers?", "a": "PW features highly qualified educators, including Alakh Pandey Sir and other top faculty."},
        {"q": "What about pricing?", "a": "PW courses are among the most affordable, starting from ₹299 to ₹5000 depending on class and exam type."}
    ]
}

def load_content():
    if not CONTENT_PATH.exists():
        CONTENT_PATH.write_text(json.dumps(DEFAULT_CONTENT, indent=2))
    return json.loads(CONTENT_PATH.read_text())

CONTENT = load_content()

# ---------------------------------------------------------
# LEAD STORAGE
# ---------------------------------------------------------
LEADS_PATH = Path(__file__).parent.parent / "shared-data/pw_leads.json"
if not LEADS_PATH.exists():
    LEADS_PATH.write_text("[]")


# ---------------------------------------------------------
# SDR Agent
# ---------------------------------------------------------
class PWSDRAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=f"""
You are a friendly SDR for Physics Wallah (PW).

GOALS:
1. Greet warmly.
2. Answer questions ONLY using the PW FAQ provided.
3. Collect lead details naturally:
   - name
   - email
   - role
   - exam/course interest
   - timeline (now / soon / later)
4. When user says anything like "I'm done", "that's all", "thank you":
   - Stop asking questions
   - Give a short verbal summary of the lead
   - Then call the save_lead tool with the collected data

ANSWERING RULES:
- If the user asks a question, search FAQ via find_faq_answer and answer.
- If answer not found: “I don’t have information on that, but I can connect you to a specialist.”
- Keep answers short, conversational, and helpful.

LEAD MEMORY FORMAT (store in your mind while talking):
- lead_name
- lead_email
- lead_role
- lead_interest
- lead_timeline

When conversation ends:
Say something like:
“Here’s a quick summary. <NAME> is interested in <INTEREST>. They’re planning to start <TIMELINE>. Saving this now.”

Then call save_lead.
"""
        )

        # in-memory lead capture
        self.lead_data = {
            "name": None,
            "email": None,
            "role": None,
            "interest": None,
            "timeline": None
        }

    # ----------------- TOOL: Save Lead ---------------------
    @function_tool
    async def save_lead(
        self,
        ctx: RunContext,
        name: str,
        email: str,
        role: str,
        interest: str,
        timeline: str
    ):
        """Save lead to pw_leads.json"""
        lead = {
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "email": email,
            "role": role,
            "interest": interest,
            "timeline": timeline
        }

        try:
            leads = json.loads(LEADS_PATH.read_text())
        except:
            leads = []

        leads.append(lead)
        LEADS_PATH.write_text(json.dumps(leads, indent=2))

        return "Lead saved successfully ✔"

    # ----------------- FAQ SEARCH FUNCTION ---------------------
    def find_faq_answer(self, text: str):
        text = text.lower()
        for item in CONTENT["faq"]:
            if any(keyword in text for keyword in item["q"].lower().split()):
                return item["a"]
        return None

    # ----------------- DETECT END + TRIGGER SUMMARY ---------------------
    def detect_end_of_call(self, text: str):
        text = text.lower()
        return any(phrase in text for phrase in [
            "i'm done", "that's all", "thank you", "thanks", "i am done"
        ])

    def create_summary(self):
        return (
            f"Here's a quick summary. "
            f"{self.lead_data.get('name', 'The user')} is interested in {self.lead_data.get('interest', 'a PW course')}. "
            f"They are planning to start {self.lead_data.get('timeline', 'soon')}. "
            f"I'll save this lead now."
        )


# ---------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    agent = PWSDRAgent()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-matthew", style="Conversation"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    usage = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _metrics(ev: MetricsCollectedEvent):
        usage.collect(ev.metrics)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await ctx.connect()


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm
        )
    )

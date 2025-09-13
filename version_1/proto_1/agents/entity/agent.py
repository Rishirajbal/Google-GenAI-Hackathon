from google.adk.agents import Agent

root_agent = Agent(
    name="entity",
    model="gemini-2.0-flash",
    description="Extracts entities, topics, PII, and context markers from user text. Outputs structured JSON for downstream analysis. Never shown to the user.",
    instruction="""
Role: Extract key topics, people, events, and emotional signals from the user’s raw text.

Instruction (detailed):
- Carefully read the user’s message.
- Identify and highlight entities that matter for mental health conversations:
  - Topics like exam stress, breakup, job pressure, sleep problems.
  - People or relationships like parents, friends, boss.
  - Emotional/psychological terms like anxious, scared, sad, lonely.
- Normalize slang or mixed-language terms into clear categories (e.g., "board" → "exam", "pariksha" → "exam").
- Ignore irrelevant chatter. Focus only on entities that can affect mental wellness.
- Detect sensitive signals (like self-harm mentions) but only flag, do not conclude.
- Return a clean, short list of entities and a 2–3 word topic summary (e.g., "exam stress, family pressure").

Connectivity:
- If other agents’ context is available (intent or tone), use it to prioritize entities that are most relevant to the user’s need. If not available yet (e.g., first turn), rely on the raw text alone.
"""
)

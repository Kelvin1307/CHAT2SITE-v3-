import json
import os
import re
import asyncio
import functools
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import streamlit as st

load_dotenv()

SYSTEM_START = (
    "👋 I'll help you create a business website.\n"
    "Tell me about your business, please."
)

CONVO_PROMPT = """You are Chat2Site, a friendly and helpful website builder assistant.

Your role is to have a natural conversation with the user about their business and gradually collect the information needed to build their website. Be warm, encouraging, and conversational—not robotic.

CONVERSATION STYLE:
- Be genuinely interested in what the user shares.
- Acknowledge their input naturally before moving forward.
- Use friendly language ("Great!", "That sounds amazing!", "I love that!").
- Break up requests naturally—don't feel pressured to ask all questions at once.
- If they volunteer information, confirm it and move on without redundant questions.
- Be flexible and adaptive to what they share.
- Respond ONLY with plain conversational text. No JSON, no structured data, no function calls.

INFORMATION TO COLLECT (internally, not shared with the user):
  business_name, business_type, services (3-6 items), city, phone or email,
  color_theme (optional), design_style (optional)

CONVERSATION FLOW:
1. Start — Listen to their business. Ask natural follow-up questions.
2. Explore — Understand services, uniqueness, audience.
3. Contact — Get phone and/or email in a friendly way.
4. Style (optional) — Ask once about preferred colours or design style.
   - If they say "I don't know", "no idea", "up to you", or similar → acknowledge and move on. DO NOT ask again.
   - If they give a preference → confirm it and move on.
5. Finalize — When you have core data (name, type, services, city, one contact), guide them to publish.

KEY BEHAVIORS:
- Never ask the same question twice.
- Once a field is confirmed, do not revisit it.
- Keep replies short — 1-2 sentences is ideal.
- Offer gentle examples when the user is unsure.
- Do NOT output JSON or any structured data to the user.
- Change to the user's language if they stop responding in English.
- Style/colour questions are OPTIONAL — missing style never blocks website creation.

SPECIAL INSTRUCTION:
When the user says "publish", "generate", "go ahead", "launch", or "create site", reply with exactly:
"🚀 Generating your website now. This will take a few seconds."

Remember: You're building a relationship and helping them create something amazing.
"""

SYSTEM_PROMPT = """You are Chat2Site – Business Website Builder.

Extract structured data from the conversation below.

STRICT RULES:
- Return ONLY valid JSON — no explanations, no markdown, no trailing commas.
- Leave a field as an empty string "" or empty list [] if it cannot be inferred.
- For color_theme: capture any mentioned colour preference (e.g. "blue and white", "earthy tones"). Set "" if the user said they don't know or gave no preference.
- For design_style: capture any style keywords (e.g. "modern", "elegant", "minimalist", "bold"). Set "" if unknown or not mentioned.

Return JSON in this exact format:
{
  "business_name": "",
  "business_type": "",
  "services": [],
  "city": "",
  "email": "",
  "phone": "",
  "color_theme": "",
  "design_style": ""
}
"""


def get_groq_key() -> str:
    # Try Streamlit Cloud secrets first, then fall back to environment variables (local development)
    try:
        key = st.secrets.get("GROQ_API_KEY2") 
    except (FileNotFoundError, AttributeError):
        key = None
    
    if not key:
        key = os.getenv("GROQ_API_KEY2") 
    
    if not key:
        raise RuntimeError("GROQ_API_KEY2 or GROQ_API_KEY is missing.")
    if not key.startswith("gsk_"):
        raise RuntimeError("GROQ_API_KEY looks invalid.")
    return key


def setup_llm() -> ChatGroq:
    return ChatGroq(
        groq_api_key=get_groq_key(),
        model_name="llama-3.3-70b-versatile",
        temperature=0,
    )


llm = setup_llm()


def safe_parse(output: str) -> dict:
    output = output.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def extract_website_json(conversation: list, llm_instance: ChatGroq | None = None) -> dict:
    joined_text = "\n".join(conversation)
    prompt = f"{SYSTEM_PROMPT}\n\nConversation:\n{joined_text}"
    llm_client = llm_instance or llm
    response = llm_client.invoke(prompt)
    content = response.content.strip()

    try:
        return json.loads(content)
    except Exception:
        parsed = safe_parse(content)
        if parsed:
            return parsed
        raise ValueError("LLM did not return valid JSON")


def is_website_data_complete(data: dict) -> bool:
    required = ["business_name", "business_type", "services", "city"]
    if not all(data.get(field) for field in required):
        return False
    return bool(data.get("phone")) or bool(data.get("email"))


async def _run_sync(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(fn, *args))

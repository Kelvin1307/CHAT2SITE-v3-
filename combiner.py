# combiner.py

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

try:
    import streamlit as st
except ImportError:
    st = None

load_dotenv()

# ------------------ LLM SETUP ------------------

def get_groq_key() -> str:
    key = None
    if st is not None:
        try:
            key = st.secrets.get("GROQ_API_KEY2") 
        except (FileNotFoundError, AttributeError):
            key = None

    key = key or os.getenv("GROQ_API_KEY2") or os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY2 or GROQ_API_KEY is missing.")
    return key

llm = ChatGroq(
    groq_api_key=get_groq_key(),
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=8192
)

# ------------------ TARGET TEMPLATE ------------------

with open("data2.json", "r", encoding="utf-8") as f:
    TARGET_JSON = json.load(f)


# ------------------ PROMPT ------------------

COMBINER_PROMPT = """
You are a JSON combiner. Merge user data with target structure perfectly.
Rules:
- Output ONLY valid JSON - NO explanations, NO markdown
- Merge both JSONs
- NEVER delete user values
- Fill missing fields with realistic content
- No empty arrays/strings
- Complete structure exactly like target
"""

# ------------------ MAIN FUNCTION ------------------

def _fix_incomplete_json(json_str: str) -> str:
    """Fix truncated JSON from LLM by closing incomplete structures."""
    json_str = json_str.rstrip()
    
    # Close unterminated strings first
    if json_str.count('"') % 2 != 0:
        # Odd number of quotes - unterminated string
        last_quote = json_str.rfind('"')
        if last_quote != -1:
            json_str = json_str[:last_quote+1]
    
    # Count unclosed braces and brackets
    open_braces = json_str.count('{') - json_str.count('}')
    open_brackets = json_str.count('[') - json_str.count(']')
    
    # Close any unclosed structures
    if open_braces > 0 or open_brackets > 0:
        json_str += '}' * max(0, open_braces) + ']' * max(0, open_brackets)
    
    return json_str


def combine_json(primary_json: dict) -> dict:
    prompt = f"""
PRIMARY JSON:
{json.dumps(primary_json, indent=2)}

TARGET STRUCTURE:
{json.dumps(TARGET_JSON, indent=2)}

{COMBINER_PROMPT}

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, just the JSON object."""

    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Remove markdown code blocks if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    try:
        final = json.loads(content)
        for key in ("business_name", "business_type", "services", "city", "email", "phone"):
            if key not in final and key in primary_json:
                final[key] = primary_json[key]
        return final

    except json.JSONDecodeError as e:
        print("❌ JSON parsing failed, attempting to fix...")
        try:
            fixed_content = _fix_incomplete_json(content)
            return json.loads(fixed_content)
        except Exception as fix_error:
            print("❌ Could not fix JSON")
            print(f"Original error: {e}")
            print(f"Response content:\n{content}")
            raise fix_error


# ------------------ TEST ------------------

if __name__ == "__main__":
    sample_primary = {
        "business_name": "Kelvin Cakes",
        "business_type": "store",
        "services_or_products": ["Custom Cakes", "Wedding Cakes"],
        "contact": {
            "phone": "+919999999999",
            "email": "kelvin@email.com"
        }
    }

    final_json = combine_json(sample_primary)

    print(json.dumps(final_json, indent=2))
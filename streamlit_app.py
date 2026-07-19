import os
from dotenv import load_dotenv
import streamlit as st

import chat2site_core as core
from combiner import combine_json
from renderer3 import render_page
from deployer import deploy_site

load_dotenv()

PUBLISH_TRIGGERS = {"publish", "generate", "go ahead", "launch", "create site"}
SYSTEM_START = (
    "👋 I'll help you create a business website.\n"
    "Tell me about your business, please."
)

def init_state() -> None:
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "style_asked" not in st.session_state:
        st.session_state.style_asked = False
    if "status" not in st.session_state:
        st.session_state.status = ""
    if "publish_url" not in st.session_state:
        st.session_state.publish_url = ""
    if "last_error" not in st.session_state:
        st.session_state.last_error = ""
    if "llm" not in st.session_state:
        st.session_state.llm = core.setup_llm()
        core.llm = st.session_state.llm

    if not st.session_state.conversation:
        st.session_state.conversation.append({"role": "assistant", "content": core.SYSTEM_START})
        st.session_state.chat_history.append(("assistant", core.SYSTEM_START))


def format_message(role: str, content: str) -> None:
    if role == "assistant":
        st.markdown(f"**Chat2Site:** {content}")
    else:
        st.markdown(f"**You:** {content}")


def get_user_transcript() -> list[str]:
    return [msg[1] for msg in st.session_state.chat_history if msg[0] == "user"]


def run_bot_reply() -> str:
    try:
        transcript = get_user_transcript()
        website_data = core.extract_website_json(transcript)
    except Exception as exc:
        st.session_state.last_error = f"Hidden fulfillment check error: {exc}"
        website_data = {}

    extra_system = []
    if core.is_website_data_complete(website_data):
        extra_system.append(
            {
                "role": "system",
                "content": (
                    "✅ All required website details have been collected. "
                    "Do NOT ask any more questions about the business. "
                    "Warmly confirm everything is ready and ask the user to say 'publish' or 'go ahead' to launch their site."
                ),
            }
        )
    else:
        style_filled = bool(website_data.get("color_theme")) or bool(website_data.get("design_style"))
        core_mostly_done = bool(website_data.get("business_name")) and bool(website_data.get("services"))

        if core_mostly_done and not style_filled and not st.session_state.style_asked:
            st.session_state.style_asked = True
            extra_system.append(
                {
                    "role": "system",
                    "content": (
                        "Core business info is mostly collected. "
                        "If you haven't yet, gently ask once about preferred colour palette or design style. "
                        "If the user says they don't know or don't mind, accept that and move on immediately — do NOT ask again."
                    ),
                }
            )

    messages = [
        {"role": "system", "content": core.CONVO_PROMPT},
        *extra_system,
        *st.session_state.conversation[-18:],
    ]

    response = st.session_state.llm.invoke(messages)
    return response.content


def run_publish() -> None:
    try:
        st.session_state.status = "⚙️ Step 1/4: Extracting business details from conversation..."
        transcript = get_user_transcript()
        website_json = core.extract_website_json(transcript)

        st.session_state.status = "🪄 Step 2/4: Generating detailed site content, copy, and layout schemas..."
        website_json = combine_json(website_json)

        st.session_state.status = "🎨 Step 3/4: Choosing the matching design style and rendering template..."
        output_dir = render_page(website_json, output_dir="site_output", strategy="smart")

        st.session_state.status = "🚀 Step 4/4: Deploying your website live on the web..."
        live_url = deploy_site(output_dir, business_name=website_json.get("business_name"))

        st.session_state.publish_url = live_url
        if live_url.startswith("Local preview"):
            st.session_state.chat_history.append(("assistant", f"🛠️ Your site was generated locally.\n{live_url}"))
        else:
            st.session_state.chat_history.append(("assistant", f"🎉 Your website is live!\n{live_url}"))
    except Exception as exc:
        st.session_state.last_error = str(exc)
        st.session_state.chat_history.append(("assistant", f"❌ Sorry, something went wrong while building your site:\n{exc}"))
    finally:
        st.session_state.status = ""


def handle_user_input(user_text: str) -> None:
    user_text = user_text.strip()
    if not user_text:
        return

    st.session_state.chat_history.append(("user", user_text))
    st.session_state.conversation.append({"role": "user", "content": user_text})

    if any(trigger in user_text.lower() for trigger in PUBLISH_TRIGGERS):
        st.session_state.chat_history.append(("assistant", "🚀 Generating your website now. This will take a few seconds."))
        run_publish()
        return

    try:
        bot_text = run_bot_reply()
    except Exception as exc:
        bot_text = f"❌ Chat2Site error: {exc}"
        st.session_state.last_error = str(exc)

    st.session_state.chat_history.append(("assistant", bot_text))


def main() -> None:
    st.set_page_config(page_title="Chat2Site Web Chat", layout="wide")
    st.title("Chat2Site Web Chat")
    st.write("Use this app to chat with Chat2Site and generate a business website from your conversation.")

    init_state()

    sidebar = st.sidebar
    sidebar.header("Controls")
    if sidebar.button("Restart conversation"):
        for key in ["conversation", "chat_history", "style_asked", "status", "publish_url", "last_error"]:
            if key in st.session_state:
                del st.session_state[key]

    if st.session_state.publish_url:
        sidebar.success("Site published")
        sidebar.write(st.session_state.publish_url)

    if st.session_state.last_error:
        sidebar.error(st.session_state.last_error)

    if sidebar.button("Publish now"):
        st.session_state.chat_history.append(("assistant", "🚀 Generating your website now. This will take a few seconds."))
        run_publish()

    if st.session_state.status:
        st.info(st.session_state.status)

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message", value="", key="user_input")
        submit = st.form_submit_button("Send")
        if submit and user_input:
            handle_user_input(user_input)

    st.divider()
    for role, text in st.session_state.chat_history:
        format_message(role, text)


if __name__ == "__main__":
    main()

"""
╔══════════════════════════════════════════════════════════════╗
║     🏥  MediMate AI  —  Web App (runs in Chrome/browser)      ║
║     Run:  streamlit run web_app.py                            ║
╚══════════════════════════════════════════════════════════════╝

Same AI brain as app.py, but as a beautiful browser chat.
Bas ye command chalao aur Chrome apne aap khul jayega:

    streamlit run web_app.py

Terminal me kuch type nahi karna — sab browser me hota hai. 😎
"""

import asyncio

import streamlit as st

import config
import healthcare_agent as agent


# ─────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────
st.set_page_config(
    page_title=f"{config.APP_NAME} — Health Companion",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded",
)


def _run(coro):
    """
    Run an async coroutine from Streamlit's sync world.

    IMPORTANT (cloud fix): Streamlit Cloud runs each script in a worker THREAD
    that has NO event loop. The old asyncio.get_event_loop() raised there and
    left the page blank. We always create a FRESH loop, run, then close it —
    works both locally and on Streamlit Cloud.
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


# ─────────────────────────────────────────────
# 🎨 CUSTOM CSS  —  makes the chat look premium
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
      /* ---- Global background: soft gradient ---- */
      .stApp {
        background: linear-gradient(160deg, #f5f7fa 0%, #e8f0fe 100%);
      }

      /* ---- Hero header card ---- */
      .medimate-hero {
        background: linear-gradient(135deg, #E92063 0%, #F55036 100%);
        padding: 1.6rem 1.8rem;
        border-radius: 20px;
        color: #ffffff;
        box-shadow: 0 10px 30px rgba(233, 32, 99, 0.25);
        margin-bottom: 1.2rem;
      }
      .medimate-hero h1 { margin: 0; font-size: 2.1rem; font-weight: 800; }
      .medimate-hero p  { margin: 0.4rem 0 0; opacity: 0.95; font-size: 1rem; }

      /* ---- Chat bubbles ---- */
      [data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 0.4rem 0.6rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 3px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.04);
      }

      /* ---- Chat input box ---- */
      [data-testid="stChatInput"] {
        border-radius: 16px;
        border: 2px solid #E92063;
        box-shadow: 0 4px 14px rgba(233,32,99,0.15);
      }

      /* ---- Sidebar polish ---- */
      [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #eceff4;
      }

      /* ---- Buttons ---- */
      .stButton > button {
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, #E92063, #F55036);
        color: #fff;
        font-weight: 600;
        transition: transform 0.12s ease;
      }
      .stButton > button:hover { transform: translateY(-2px); }

      /* ---- Feature status pills ---- */
      .feat-pill {
        display: inline-block; padding: 3px 10px; margin: 3px 2px;
        border-radius: 999px; font-size: 0.82rem; font-weight: 600;
      }
      .feat-on  { background: #dcfce7; color: #15803d; }
      .feat-off { background: #f1f5f9; color: #94a3b8; }

      /* hide the default Streamlit menu/footer for a clean look */
      #MainMenu { visibility: hidden; }
      footer    { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# SIDEBAR  —  settings + live feature status
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🏥 " + config.APP_NAME)
    st.caption(config.APP_TAGLINE + f"  ·  v{config.VERSION}")

    st.subheader("👤 Your details")
    patient_name = st.text_input("Name", value="You")
    language = st.selectbox("Reply language", config.SUPPORTED_LANGUAGES, index=0)
    country = st.selectbox(
        "Country (for emergency numbers)",
        list(config.EMERGENCY_NUMBERS.keys()),
        index=list(config.EMERGENCY_NUMBERS.keys()).index(config.DEFAULT_COUNTRY)
        if config.DEFAULT_COUNTRY in config.EMERGENCY_NUMBERS else 0,
    )

    st.subheader("🔌 Feature status")
    pills = ""
    for feature, on in config.feature_status().items():
        cls = "feat-on" if on else "feat-off"
        dot = "🟢" if on else "⚪"
        pills += f'<span class="feat-pill {cls}">{dot} {feature}</span>'
    st.markdown(pills, unsafe_allow_html=True)

    st.write("")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("⚠️ AI assistant, not a doctor. For emergencies call your local helpline.")


# ─────────────────────────────────────────────
# HEADER  —  hero card
# ─────────────────────────────────────────────
st.markdown(
    """
    <div class="medimate-hero">
      <h1>🏥 MediMate AI</h1>
      <p>Apna health sawaal likho — AI turant jawab dega.
      Emergency detect hote hi helpline number bhi milega. 🚑</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not config.HAS_LLM:
    st.warning("⚠️ Koi GROQ_API_KEY nahi mili — abhi offline mode chalega. "
               "Streamlit **Secrets** me key daalo full AI ke liye.")


# ─────────────────────────────────────────────
# CHAT STATE
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Friendly welcome bubble on first load
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🏥"):
        st.markdown(
            "Namaste! 👋 Main **MediMate AI** hoon.\n\n"
            "Aap mujhse pooch sakte ho — jaise:\n"
            "- *\"I have a headache and fever, what should I do?\"*\n"
            "- *\"What are the symptoms of diabetes?\"*\n"
            "- *\"Is my BMI healthy for 70kg and 175cm?\"*\n\n"
            "Neeche box me apna sawaal type karo. 😊"
        )

# Replay past chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🏥"):
        st.markdown(msg["content"])


# ─────────────────────────────────────────────
# INPUT  —  the chat box at the bottom
# ─────────────────────────────────────────────
prompt = st.chat_input("Type your health question here…")

if prompt:
    # show user's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # get AI answer
    with st.chat_message("assistant", avatar="🏥"):
        with st.spinner("Soch raha hoon… 🤔"):
            try:
                resp = _run(agent.answer_question(
                    prompt,
                    patient_name=patient_name,
                    language=language,
                    country=country,
                    save=True,
                ))
            except Exception as e:
                # Never show a blank screen — surface the error kindly.
                st.error(f"😔 Kuch gadbad ho gayi: `{e}`\n\n"
                         "Thodi der baad phir try karo, ya /status check karo.")
                st.stop()

        # ── Build a rich, readable reply ──
        urgency_emoji = {
            "emergency": "🚨", "urgent": "⚠️", "routine": "📋",
            "self-care": "🌿", "informational": "ℹ️",
        }.get(resp.urgency_level, "ℹ️")

        if resp.is_emergency:
            st.error(f"{urgency_emoji}  EMERGENCY — {resp.urgency_level.upper()}")
        else:
            # Show honestly whether this came from the AI or the offline brain.
            source_badge = {
                "ai": "🧠 AI answer",
                "offline": "📴 Offline mode",
                "emergency": "🚨 Emergency",
            }.get(resp.source, "🧠 AI answer")
            st.markdown(f"**{urgency_emoji} {resp.urgency_level.title()}**  ·  "
                        f"{source_badge}  ·  confidence: `{resp.confidence}`")
            if resp.source == "offline" and resp.note:
                st.warning(f"⚠️ {resp.note}  Showing an offline answer instead.")

        parts = [resp.answer]

        if resp.possible_causes:
            parts.append("\n**🔎 Possible causes:**\n" +
                         "\n".join(f"- {c}" for c in resp.possible_causes))

        if resp.recommended_actions:
            parts.append("\n**📋 Recommended actions:**\n" +
                         "\n".join(f"- {a}" for a in resp.recommended_actions))

        if resp.when_to_see_doctor:
            parts.append(f"\n**👩‍⚕️ When to see a doctor:** {resp.when_to_see_doctor}")

        if resp.follow_up_questions:
            parts.append("\n**💬 You could also ask:**\n" +
                         "\n".join(f"- {q}" for q in resp.follow_up_questions))

        parts.append(f"\n\n---\n_{resp.disclaimer}_")

        full = "\n".join(parts)
        st.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})

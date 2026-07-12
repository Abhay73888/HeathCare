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
)


def _run(coro):
    """Run an async coroutine from Streamlit's sync world."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


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
    for feature, on in config.feature_status().items():
        st.write(("🟢 " if on else "⚪ ") + feature)

    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

    st.caption("⚠️ AI assistant, not a doctor. For emergencies call your local helpline.")


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🏥 MediMate AI")
st.caption("Apna health sawaal likho — AI turant jawab dega. Emergency detect hote hi helpline number bhi milega. 🚑")

if not config.HAS_LLM:
    st.warning("⚠️ Koi GROQ_API_KEY nahi mili — abhi offline mode chalega. .env me key daalo full AI ke liye.")


# ─────────────────────────────────────────────
# CHAT STATE
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

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
            resp = _run(agent.answer_question(
                prompt,
                patient_name=patient_name,
                language=language,
                country=country,
                save=True,
            ))

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

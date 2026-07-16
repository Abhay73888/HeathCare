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
import ml_predictor
import calculators


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
# ⚖️ BMI CALCULATOR  —  instant, offline, no API needed
# ─────────────────────────────────────────────
with st.expander("⚖️ BMI Calculator — apna BMI turant check karo"):
    c1, c2 = st.columns(2)
    with c1:
        bmi_weight = st.number_input("Weight (kg)", 10.0, 300.0, 70.0, step=0.5, key="bmi_wt")
    with c2:
        bmi_height = st.number_input("Height (cm)", 50.0, 250.0, 170.0, step=0.5, key="bmi_ht")

    if st.button("⚖️ Calculate BMI", use_container_width=True, key="bmi_btn"):
        res = calculators.bmi(bmi_weight, bmi_height)
        rng = calculators.ideal_weight(bmi_height, "male")["healthy_range_kg"]

        # Color-coded result card by WHO category
        show = (st.success if res["category"] == "Normal weight"
                else st.error if res["category"] == "Obese"
                else st.warning)
        show(f"{res['emoji']} **BMI: {res['bmi']}** — {res['category']}")

        # Scale: 18.5–25 normal band; progress bar as a quick visual (capped at 40)
        st.progress(min(res["bmi"] / 40, 1.0))
        st.caption("Scale: <18.5 Underweight · 18.5–24.9 Normal ✅ · 25–29.9 Overweight · 30+ Obese")

        st.markdown(f"- 💡 {res['note']}\n"
                    f"- 🎯 Aapki height ({bmi_height:.0f} cm) ke liye healthy weight range: "
                    f"**{rng[0]}–{rng[1]} kg**")
        st.caption("⚠️ BMI ek simple screening number hai — muscle mass, age, body type "
                   "consider nahi karta. Sahi assessment ke liye doctor se milo.")



with st.expander("🧠 ML Risk Predictor — diabetes & heart risk check karo (real ML!)"):
    if not ml_predictor.models_ready():
        st.info("🤖 Models abhi trained nahi hain. Terminal me ek baar chalao:\n\n"
                "```\npython ml_predictor.py\n```\n"
                "(internet chahiye sirf pehli baar — phir offline chalega)")
    else:
        m = ml_predictor.get_metrics()
        if m:
            st.caption(f"📊 Model accuracy — Diabetes: {m['diabetes']['accuracy']*100:.0f}% · "
                       f"Heart: {m['heart']['accuracy']*100:.0f}% (on unseen test data)")

        tab_dia, tab_heart = st.tabs(["🍬 Diabetes risk", "❤️ Heart risk"])

        # ── 🍬 Diabetes tab ──
        with tab_dia:
            c1, c2 = st.columns(2)
            with c1:
                d_glucose = st.number_input("Fasting glucose (mg/dL)", 40, 400, 100, key="d_glu")
                d_bmi = st.number_input("BMI", 10.0, 60.0, 24.0, step=0.5, key="d_bmi")
            with c2:
                d_age = st.number_input("Age (years)", 1, 120, 30, key="d_age")
                d_bp = st.number_input("Blood pressure (diastolic, mm Hg)", 40, 140, 72, key="d_bp")

            if st.button("🔮 Predict diabetes risk", use_container_width=True, key="d_btn"):
                res = ml_predictor.predict_diabetes(
                    glucose=d_glucose, bmi=d_bmi, age=d_age, blood_pressure=d_bp)
                if res["ok"]:
                    lvl = res["risk_level"]
                    show = st.error if lvl == "HIGH" else st.warning if lvl == "MODERATE" else st.success
                    show(f"{res['emoji']} **{res['condition']} risk: {lvl}** "
                         f"(~{res['risk_percent']}% probability)")
                    st.progress(min(res["risk_percent"] / 100, 1.0))
                    for a in res["advice"]:
                        st.markdown(f"- {a}")
                    st.caption(f"{res['model']}  ·  {res['disclaimer']}")
                else:
                    st.info(res["error"])

        # ── ❤️ Heart tab ──
        with tab_heart:
            c1, c2 = st.columns(2)
            with c1:
                h_age = st.number_input("Age (years)", 1, 120, 45, key="h_age")
                h_sex = st.selectbox("Sex", ["Male", "Female"], key="h_sex")
                h_bp = st.number_input("Resting BP (systolic, mm Hg)", 70, 250, 120, key="h_bp")
            with c2:
                h_chol = st.number_input("Cholesterol (mg/dL)", 100, 600, 200, key="h_chol")
                h_hr = st.number_input("Max heart rate achieved", 60, 220, 150, key="h_hr")
                h_angina = st.checkbox("Exercise me chest pain hota hai?", key="h_ang")

            if st.button("🔮 Predict heart risk", use_container_width=True, key="h_btn"):
                res = ml_predictor.predict_heart(
                    age=h_age, sex=h_sex.lower(), resting_bp=h_bp,
                    cholesterol=h_chol, max_heart_rate=h_hr,
                    exercise_angina=h_angina)
                if res["ok"]:
                    lvl = res["risk_level"]
                    show = st.error if lvl == "HIGH" else st.warning if lvl == "MODERATE" else st.success
                    show(f"{res['emoji']} **{res['condition']} risk: {lvl}** "
                         f"(~{res['risk_percent']}% probability)")
                    st.progress(min(res["risk_percent"] / 100, 1.0))
                    for a in res["advice"]:
                        st.markdown(f"- {a}")
                    st.caption(f"{res['model']}  ·  {res['disclaimer']}")
                else:
                    st.info(res["error"])


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

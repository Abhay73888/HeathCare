"""
╔══════════════════════════════════════════════════════════════╗
║        🏥  MediMate AI  —  Advanced Healthcare AI Agent       ║
║        Powered by Groq (LLaMA-3.3) + Serper + PydanticAI      ║
╚══════════════════════════════════════════════════════════════╝

This is the BRAIN of the app. It:

  1. 🚨 Scans EVERY question for medical emergencies first (safety-first).
  2. 🧠 Uses a fast Groq LLM with SEVEN tools to give smart, structured answers.
  3. 📴 Falls back to an offline knowledge base + calculators when there is
        no API key or no internet — so it is NEVER useless.

Run this file directly for a quick demo, or run `app.py` for the full
interactive chat experience.

SETUP
-----
    pip install -r requirements.txt

Create a `.env` file (see `.env.example`):
    GROQ_API_KEY=your_groq_key_here
    SERPER_API_KEY=your_serper_key_here
"""

import asyncio
import json
from dataclasses import dataclass, field, asdict

import httpx

import config
import calculators
import emergency
import knowledge
import history
import nutrition
import weather_health
import news
import reminders
import ml_predictor


# ─────────────────────────────────────────────
# THE RESPONSE  —  what every answer looks like
# A plain dataclass so it works even without pydantic-ai installed.
# ─────────────────────────────────────────────
@dataclass
class HealthcareResponse:
    answer: str
    urgency_level: str = "informational"      # emergency | urgent | routine | self-care | informational
    possible_causes: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    when_to_see_doctor: str = "Consult a doctor if symptoms persist or worsen."
    web_searched: bool = False
    confidence: str = "medium"                 # high | medium | low
    disclaimer: str = ("⚠️ I'm an AI assistant, not a doctor. This is general "
                       "information only — please consult a qualified healthcare "
                       "professional for diagnosis and treatment.")
    follow_up_questions: list[str] = field(default_factory=list)
    is_emergency: bool = False
    source: str = "ai"                         # ai | offline | emergency
    note: str = ""                             # extra status line (e.g. why offline)

    def to_dict(self) -> dict:
        return asdict(self)


# ═════════════════════════════════════════════════════════════
#  TOOL IMPLEMENTATIONS  (plain async functions — reusable)
#  The LLM agent calls these; the offline path can too.
# ═════════════════════════════════════════════════════════════

async def web_search(query: str) -> str:
    """🌐 Live web search via Serper. Returns formatted top results."""
    if not config.HAS_WEB_SEARCH:
        return "Web search is not configured (no SERPER_API_KEY)."

    print(f"   🔍 [tool] web_search: '{query}'")
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": config.SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": f"{query} medical health", "num": 5}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            data = resp.json()
    except Exception as e:  # network hiccup -> don't crash the whole answer
        return f"Web search failed: {e}"

    results = []
    for item in data.get("organic", [])[:4]:
        results.append(f"• {item.get('title','')}\n  {item.get('snippet','')}\n  {item.get('link','')}")
    return "\n\n".join(results) if results else "No relevant results found."


def triage(symptoms: str, country: str = config.DEFAULT_COUNTRY) -> str:
    """🚨 Check symptoms for emergency red flags. Returns a triage summary."""
    print(f"   🚨 [tool] triage: '{symptoms}'")
    hit = emergency.detect_emergency(symptoms, country)
    if hit:
        nums = ", ".join(f"{k}: {v}" for k, v in hit["numbers"].items())
        return (f"EMERGENCY DETECTED — {hit['name']}. Advice: {hit['advice']} "
                f"Emergency numbers ({country}): {nums}")
    return "No emergency red flags detected. Proceed with normal guidance."


def health_calculator(kind: str, **params) -> str:
    """🧮 Run a health calculation (bmi, calories, water, ideal_weight, heart_rate, body_fat)."""
    print(f"   🧮 [tool] health_calculator: {kind} {params}")
    try:
        if kind == "bmi":
            return json.dumps(calculators.bmi(params["weight_kg"], params["height_cm"]))
        if kind == "calories":
            return json.dumps(calculators.daily_calories(
                params["weight_kg"], params["height_cm"], params["age"],
                params.get("sex", "male"), params.get("activity", "moderate")))
        if kind == "water":
            return json.dumps(calculators.water_intake(params["weight_kg"], params.get("activity_minutes", 30)))
        if kind == "ideal_weight":
            return json.dumps(calculators.ideal_weight(params["height_cm"], params.get("sex", "male")))
        if kind == "heart_rate":
            return json.dumps(calculators.heart_rate_zones(params["age"]))
        if kind == "body_fat":
            return json.dumps(calculators.body_fat(
                params["weight_kg"], params["height_cm"], params["age"], params.get("sex", "male")))
    except KeyError as e:
        return f"Missing parameter for {kind}: {e}"
    return f"Unknown calculation: {kind}"


def first_aid_guide(condition: str) -> str:
    """🩹 Get step-by-step first-aid instructions (offline)."""
    print(f"   🩹 [tool] first_aid_guide: '{condition}'")
    guide = emergency.first_aid(condition)
    if guide:
        steps = "\n".join(f"{i}. {s}" for i, s in enumerate(guide["steps"], 1))
        return f"First aid for {guide['condition']}:\n{steps}"
    topics = ", ".join(emergency.available_first_aid_topics())
    return f"No first-aid guide for '{condition}'. Available: {topics}"


def knowledge_lookup(topic: str) -> str:
    """📖 Look up a condition in the offline knowledge base."""
    print(f"   📖 [tool] knowledge_lookup: '{topic}'")
    entry = knowledge.lookup(topic)
    return knowledge.format_entry(entry) if entry else f"No offline entry for '{topic}'."


async def nutrition_lookup(meal: str) -> str:
    """🍎 Analyze a meal's calories & macros (e.g. '2 roti + 1 cup dal')."""
    print(f"   🍎 [tool] nutrition_lookup: '{meal}'")
    return nutrition.format_meal(await nutrition.analyze_meal(meal))


async def weather_alert(city: str = "") -> str:
    """🌤️ Get weather + air-quality health advice for a city."""
    print(f"   🌤️ [tool] weather_alert: '{city or config.DEFAULT_CITY}'")
    return weather_health.format_weather(await weather_health.get_weather_health(city or None))


async def health_news(topic: str = "health") -> str:
    """📰 Get the latest health news headlines."""
    print(f"   📰 [tool] health_news: '{topic}'")
    return news.format_news(await news.get_health_news(topic))


def set_reminder(medicine: str, time_hhmm: str, patient: str = "You") -> str:
    """💊 Set a daily medicine reminder at HH:MM."""
    print(f"   💊 [tool] set_reminder: {medicine} @ {time_hhmm}")
    result = reminders.add_reminder(medicine, time_hhmm, patient)
    if result["ok"]:
        return f"Reminder set: {medicine} daily at {result['reminder']['time']}."
    return result["error"]


def ml_risk_prediction(condition: str, **params) -> str:
    """🧠 REAL ML prediction — trained scikit-learn models (not the LLM guessing!).
    condition = 'diabetes' | 'heart' | 'stroke' | 'breast_cancer'.
    Returns formatted risk + advice."""
    print(f"   🧠 [tool] ml_risk_prediction: {condition} {params}")
    try:
        if condition == "diabetes":
            result = ml_predictor.predict_diabetes(
                glucose=float(params["glucose"]),
                bmi=float(params["bmi"]),
                age=int(params["age"]),
                blood_pressure=float(params.get("blood_pressure", 72)),
            )
        elif condition == "heart":
            result = ml_predictor.predict_heart(
                age=int(params["age"]),
                sex=str(params.get("sex", "male")),
                resting_bp=float(params.get("resting_bp", 120)),
                cholesterol=float(params.get("cholesterol", 200)),
                max_heart_rate=float(params.get("max_heart_rate", 150)),
                exercise_angina=bool(params.get("exercise_angina", False)),
            )
        elif condition == "stroke":
            result = ml_predictor.predict_stroke(
                age=int(params["age"]),
                sex=str(params.get("sex", "male")),
                avg_glucose=float(params.get("avg_glucose", 100)),
                bmi=float(params.get("bmi", 25)),
                hypertension=bool(params.get("hypertension", False)),
                heart_disease=bool(params.get("heart_disease", False)),
                smoking=str(params.get("smoking", "never")),
            )
        elif condition == "breast_cancer":
            result = ml_predictor.predict_breast_cancer(
                mean_radius=float(params["mean_radius"]),
                mean_texture=float(params["mean_texture"]),
                mean_perimeter=float(params["mean_perimeter"]),
                mean_area=float(params["mean_area"]),
            )
        else:
            return (f"Unknown condition '{condition}'. "
                    "Use 'diabetes', 'heart', 'stroke' or 'breast_cancer'.")
    except (KeyError, ValueError) as e:
        return f"Missing/invalid parameter for {condition} prediction: {e}"
    return ml_predictor.format_prediction(result)


# ═════════════════════════════════════════════════════════════
#  THE LLM AGENT  (built lazily so offline mode needs no extra deps)
# ═════════════════════════════════════════════════════════════

_AGENT = None  # cached singleton

SYSTEM_PROMPT = """
You are MediMate AI — a warm, careful, and knowledgeable Healthcare AI Assistant.

YOUR RULES:
1. SAFETY FIRST. If the user describes a possible emergency (chest pain,
   stroke signs, trouble breathing, severe bleeding, suicidal thoughts, etc.),
   set urgency_level to "emergency", tell them to call emergency services
   immediately, and keep advice brief and calm.
2. NEVER give a definitive diagnosis. Explain possibilities and always
   recommend seeing a real doctor.
3. Use your TOOLS wisely:
   - triage: to check any symptoms for danger signs.
   - web_search: for latest/current medical info, drugs, or local help.
   - health_calculator: for BMI, calories, water, ideal weight, heart-rate, body-fat.
   - first_aid_guide: for step-by-step emergency first aid.
   - knowledge_lookup: for well-known conditions.
   - nutrition_lookup: when the user mentions food/meals/diet/calories eaten.
   - weather_alert: when asked about weather, pollution/AQI, or outdoor safety.
   - health_news: when asked for latest health news/updates.
   - set_reminder: when the user wants a medicine reminder (needs medicine + HH:MM time).
   - ml_risk_prediction: REAL trained ML models for diabetes, heart-disease,
     stroke, and breast-cancer risk. Use when the user shares health numbers
     and asks about their risk. Ask for missing required numbers first:
       diabetes: glucose+bmi+age
       heart: age+sex+resting_bp+cholesterol+max_heart_rate
       stroke: age+sex+avg_glucose+bmi (optional: hypertension, heart_disease, smoking)
       breast_cancer: mean_radius+mean_texture+mean_perimeter+mean_area
         (from a biopsy/FNA report — for other breast-health questions
         answer normally without this tool).
4. Be empathetic and clear. Use simple language. Reply in the user's language
   (deps.language).
5. FORMAT the `answer` field for easy reading:
   - Short paragraphs (2-3 sentences max), separated by blank lines.
   - Use **bold** for key terms and bullet points ("- ") for any list.
   - NEVER return one giant wall of text.
   - Do NOT repeat causes/actions inside `answer` — those go in their own
     fields (possible_causes, recommended_actions). Keep `answer` focused
     on directly answering the question.
6. Rate confidence honestly: high (well-established), medium (general), low (uncertain).
7. Provide 2-3 helpful follow-up questions.
8. You MAY receive earlier conversation turns as message history. USE them:
   remember the patient's previously shared symptoms, numbers and context,
   and answer follow-up questions ("aur uska kya matlab hai?") in that light
   instead of asking for the same information again.

Fill EVERY field of the structured response thoughtfully.
"""


def _build_agent():
    """Create the PydanticAI agent + register tools. Called once, lazily."""
    from typing import Literal
    from pydantic import BaseModel, Field
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.models.groq import GroqModel

    # Deps injected into every run (session context)
    class Deps(BaseModel):
        patient_name: str = "Patient"
        language: str = "English"
        country: str = config.DEFAULT_COUNTRY

    # Structured output the LLM MUST return
    class LLMResponse(BaseModel):
        answer: str = Field(description="Clear, empathetic main answer")
        urgency_level: Literal["emergency", "urgent", "routine", "self-care", "informational"] = "informational"
        possible_causes: list[str] = Field(default_factory=list)
        recommended_actions: list[str] = Field(default_factory=list)
        when_to_see_doctor: str = "Consult a doctor if symptoms persist or worsen."
        web_searched: bool = False
        confidence: Literal["high", "medium", "low"] = "medium"
        disclaimer: str = "⚠️ I'm an AI, not a doctor. Please consult a healthcare professional."
        follow_up_questions: list[str] = Field(default_factory=list)

    import os
    os.environ["GROQ_API_KEY"] = config.GROQ_API_KEY  # SDK reads it from env
    model = GroqModel(config.GROQ_MODEL)

    # retries=5: some Groq models occasionally emit a malformed tool-call
    # (e.g. a literal "<function=...>" string instead of proper JSON). A few
    # extra retries let the model recover and produce valid structured output.
    agent = Agent(model=model, deps_type=Deps, output_type=LLMResponse,
                  retries=5, system_prompt=SYSTEM_PROMPT)

    # ── Register tools (thin wrappers around our reusable functions) ──
    @agent.tool
    async def tool_web_search(ctx: RunContext[Deps], query: str) -> str:
        """Search the web for current medical information."""
        return await web_search(query)

    @agent.tool
    async def tool_triage(ctx: RunContext[Deps], symptoms: str) -> str:
        """Check symptoms for emergency red flags."""
        return triage(symptoms, ctx.deps.country)

    @agent.tool
    async def tool_calculator(ctx: RunContext[Deps], kind: str, params_json: str = "{}") -> str:
        """Run a health calculation. kind = bmi|calories|water|ideal_weight|heart_rate|body_fat.
        params_json is a JSON object of arguments, e.g. {"weight_kg":70,"height_cm":175}."""
        try:
            params = json.loads(params_json) if params_json else {}
        except json.JSONDecodeError:
            params = {}
        return health_calculator(kind, **params)

    @agent.tool
    async def tool_first_aid(ctx: RunContext[Deps], condition: str) -> str:
        """Get step-by-step first-aid instructions for a condition."""
        return first_aid_guide(condition)

    @agent.tool
    async def tool_knowledge(ctx: RunContext[Deps], topic: str) -> str:
        """Look up a common condition in the offline knowledge base."""
        return knowledge_lookup(topic)

    @agent.tool
    async def tool_nutrition(ctx: RunContext[Deps], meal: str) -> str:
        """Analyze calories & macros of a meal, e.g. '2 roti + 1 cup dal + 1 egg'."""
        return await nutrition_lookup(meal)

    @agent.tool
    async def tool_weather(ctx: RunContext[Deps], city: str = "") -> str:
        """Weather + air-quality (AQI) health advice for a city."""
        return await weather_alert(city)

    @agent.tool
    async def tool_news(ctx: RunContext[Deps], topic: str = "health") -> str:
        """Latest health news headlines."""
        return await health_news(topic)

    @agent.tool
    async def tool_reminder(ctx: RunContext[Deps], medicine: str, time_hhmm: str) -> str:
        """Set a daily medicine reminder at HH:MM (24-hour time)."""
        return set_reminder(medicine, time_hhmm, ctx.deps.patient_name)

    @agent.tool
    async def tool_ml_prediction(ctx: RunContext[Deps], condition: str, params_json: str = "{}") -> str:
        """REAL trained ML risk prediction. condition = diabetes|heart|stroke|breast_cancer.
        params_json for diabetes: {"glucose":150,"bmi":32,"age":45,"blood_pressure":80}
        params_json for heart: {"age":58,"sex":"male","resting_bp":145,"cholesterol":250,"max_heart_rate":140,"exercise_angina":true}
        params_json for stroke: {"age":68,"sex":"male","avg_glucose":210,"bmi":33,"hypertension":true,"heart_disease":false,"smoking":"smokes"}
        params_json for breast_cancer: {"mean_radius":20.5,"mean_texture":25,"mean_perimeter":135,"mean_area":1300}"""
        try:
            params = json.loads(params_json) if params_json else {}
        except json.JSONDecodeError:
            params = {}
        return ml_risk_prediction(condition, **params)

    return agent, Deps, LLMResponse


def _get_agent():
    global _AGENT
    if _AGENT is None:
        _AGENT = _build_agent()
    return _AGENT


# ═════════════════════════════════════════════════════════════
#  MAIN ENTRY  —  answer_question()
#  This is what app.py and the demo call.
# ═════════════════════════════════════════════════════════════

MEMORY_TURNS = 8   # last N messages (4 user + 4 assistant) LLM ko dikhte hain


def _with_memory(question: str, chat_history: list[dict] | None) -> str:
    """
    🧠 Pichhle chat turns ko prompt me jodo taaki AI follow-ups samjhe.

    Transcript-style approach rakha (pydantic-ai ke message_history objects
    ke bajaye) — simple hai, purane pydantic-ai versions pe bhi chalta hai,
    aur structured-output ke saath koi conflict nahi. Assistant replies ko
    truncate karte hain taaki tokens control me rahen.
    """
    if not chat_history:
        return question
    recent = [m for m in chat_history if m.get("content")][-MEMORY_TURNS:]
    if not recent:
        return question
    lines = []
    for m in recent:
        who = "Patient" if m.get("role") == "user" else "You (MediMate)"
        content = str(m["content"]).strip()
        if len(content) > 500:                      # long answers -> summary-cut
            content = content[:500] + " …"
        lines.append(f"{who}: {content}")
    transcript = "\n".join(lines)
    return (f"CONVERSATION SO FAR (for context — use it to understand follow-ups):\n"
            f"{transcript}\n\n"
            f"NEW QUESTION from the patient:\n{question}")


async def answer_question(question: str, patient_name: str = "User",
                          language: str = "English",
                          country: str = config.DEFAULT_COUNTRY,
                          save: bool = True,
                          chat_history: list[dict] | None = None) -> HealthcareResponse:
    """
    The one function to rule them all. Give it a health question, get back a
    rich, structured HealthcareResponse.

    chat_history (optional) = pichhle turns, taaki AI follow-ups samjhe:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    Sirf last few turns hi bheje jaate hain (token bachao 💰).

    Flow:
      1) 🚨 Emergency scan (always, offline, instant).
      2) 🧠 If LLM available -> smart AI answer with tools + memory.
      3) 📴 Else -> offline knowledge base + calculators fallback.
    """
    # ── STEP 1: Emergency scan (safety first, runs no matter what) ──
    em = emergency.detect_emergency(question, country)
    if em:
        nums = em["numbers"]
        primary = nums.get("mental_health") if em["is_mental_health"] else nums.get("ambulance", nums.get("general"))
        actions = [em["advice"], f"📞 Call now: {primary}"]
        actions += [f"{k.replace('_', ' ').title()}: {v}" for k, v in nums.items()]
        resp = HealthcareResponse(
            answer=f"{em['emoji']}  This may be an emergency: {em['name']}.\n\n{em['advice']}",
            urgency_level="emergency",
            recommended_actions=actions,
            when_to_see_doctor="Call emergency services or go to the nearest hospital NOW.",
            confidence="high",
            is_emergency=True,
            source="emergency",
            follow_up_questions=["Is someone with you right now?",
                                 "Do you want first-aid steps while help arrives?"],
        )
        if save:
            history.save_consultation(patient_name, question, resp.answer, "emergency")
        return resp

    # ── STEP 2: Smart AI path ──
    offline_note = ""  # if the AI fails, we explain WHY in the offline reply
    if config.HAS_LLM:
        # Some Groq models occasionally emit a malformed tool-call and the whole
        # run fails to format ("Exceeded maximum output retries"). That failure
        # is INTERMITTENT — the very same question usually succeeds on a fresh
        # attempt. So we retry the ENTIRE run a few times before giving up and
        # dropping to offline mode. This is what keeps answers consistently "AI".
        MAX_ATTEMPTS = 3
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                agent, Deps, _ = _get_agent()
                deps = Deps(patient_name=patient_name, language=language, country=country)
                prompt = _with_memory(question, chat_history)
                result = await agent.run(prompt, deps=deps)
                data = getattr(result, "output", None) or getattr(result, "data", None)

                resp = HealthcareResponse(
                    answer=data.answer,
                    urgency_level=data.urgency_level,
                    possible_causes=list(data.possible_causes),
                    recommended_actions=list(data.recommended_actions),
                    when_to_see_doctor=data.when_to_see_doctor,
                    web_searched=data.web_searched,
                    confidence=data.confidence,
                    disclaimer=data.disclaimer,
                    follow_up_questions=list(data.follow_up_questions),
                    source="ai",
                )
                if save:
                    history.save_consultation(patient_name, question, resp.answer, resp.urgency_level)
                return resp
            except Exception as e:
                offline_note = _explain_llm_error(e)
                # A format/validation miss is intermittent -> retry the whole run.
                text = str(e).lower()
                retryable = ("maximum output retries" in text or "validation" in text
                             or "unexpectedmodelbehavior" in type(e).__name__.lower())
                if retryable and attempt < MAX_ATTEMPTS:
                    print(f"   🔄 AI format hiccup (attempt {attempt}/{MAX_ATTEMPTS}). Retrying…")
                    continue
                # Rate-limit / bad-key / network -> no point retrying; fall through.
                print(f"   ⚠️  LLM unavailable ({offline_note}). Falling back to offline mode.")
                break

    # ── STEP 3: Offline fallback ──
    resp = _offline_answer(question)
    resp.note = offline_note
    if save:
        history.save_consultation(patient_name, question, resp.answer, resp.urgency_level)
    return resp


def _explain_llm_error(e: Exception) -> str:
    """Turn a raw LLM exception into a short, user-friendly reason string."""
    text = str(e).lower()
    if "rate_limit" in text or "429" in text or "tokens per day" in text:
        # Try to surface Groq's "try again in Xm" hint if present.
        import re
        m = re.search(r"try again in ([\dhms]+(?:\.\d+)?s?)", str(e))
        when = f" Try again in ~{m.group(1).rstrip('.')}." if m else ""
        return f"AI daily limit reached.{when}"
    if "api_key" in text or "invalid" in text and "key" in text or "401" in text:
        return "AI key looks invalid — check GROQ_API_KEY in .env."
    if "maximum output retries" in text or "validation" in text:
        return "AI struggled to format its answer."
    if "timeout" in text or "connect" in text or "network" in text:
        return "Couldn't reach the AI (network issue)."
    return "AI temporarily unavailable."


def _offline_answer(question: str) -> HealthcareResponse:
    """Best-effort answer with zero internet using the local knowledge base."""
    entry = knowledge.lookup(question)
    if entry:
        return HealthcareResponse(
            answer=knowledge.format_entry(entry),
            possible_causes=entry["symptoms"],
            recommended_actions=entry["self_care"],
            when_to_see_doctor=entry["see_doctor"],
            confidence="medium",
            source="offline",
            follow_up_questions=[
                f"Would you like self-care tips for {entry['title'].lower()}?",
                "Do you want me to check your symptoms for danger signs?",
            ],
        )

    # nothing matched — helpful generic reply.
    # Word it based on WHY we're offline: no key at all, vs a key that's
    # temporarily unavailable (rate limit / network / etc.).
    topics = ", ".join(knowledge.all_topics())
    if config.HAS_LLM:
        why = ("I'm temporarily in offline mode, so I can only answer common "
               "topics right now. Full AI answers will come back shortly.")
        tip = "👉 The AI will retry automatically on your next question."
    else:
        why = ("I'm running in offline mode (no AI key detected), so I can only "
               "answer common topics for now.")
        tip = "👉 Add a GROQ_API_KEY in your .env to unlock full AI answers."
    return HealthcareResponse(
        answer=(f"{why}\n\n"
                f"Try asking about: {topics}.\n"
                f"Or type /help to see calculators and first-aid guides.\n\n{tip}"),
        confidence="low",
        source="offline",
        follow_up_questions=["Want to calculate your BMI?", "Need a first-aid guide?"],
    )


# ═════════════════════════════════════════════════════════════
#  DEMO  —  run `python healthcare_agent.py` for a quick test
# ═════════════════════════════════════════════════════════════

def _print(resp: HealthcareResponse):
    print(f"\n{'='*64}")
    print(f"✅ ANSWER ({resp.urgency_level.upper()}):\n{resp.answer}")
    if resp.possible_causes:
        print(f"\n🔎 Possible causes: {', '.join(resp.possible_causes)}")
    if resp.recommended_actions:
        print("\n📋 Recommended actions:")
        for a in resp.recommended_actions:
            print(f"   • {a}")
    print(f"\n👩‍⚕️ When to see a doctor: {resp.when_to_see_doctor}")
    print(f"📊 Confidence: {resp.confidence}  |  🌐 Web searched: {resp.web_searched}")
    print(f"\n{resp.disclaimer}")
    if resp.follow_up_questions:
        print("\n💬 Follow-ups:")
        for q in resp.follow_up_questions:
            print(f"   - {q}")


async def _demo():
    print(f"\n🏥 {config.APP_NAME} v{config.VERSION} — {config.status_banner()}\n")
    for q in [
        "What are the symptoms of Type 2 Diabetes?",
        "I have crushing chest pain spreading to my left arm",   # emergency!
        "What's a healthy BMI for 70kg and 175cm?",
    ]:
        print(f"\n❓ {q}")
        _print(await answer_question(q, patient_name="Rahul"))


if __name__ == "__main__":
    asyncio.run(_demo())

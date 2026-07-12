<div align="center">

# 🏥 MediMate AI

### *Your friendly, always-on health companion — safety-first, AI-powered, and offline-ready.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/Groq-LLaMA--4-F55036?style=for-the-badge&logo=meta&logoColor=white)](https://console.groq.com/)
[![PydanticAI](https://img.shields.io/badge/PydanticAI-Agent-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://ai.pydantic.dev/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](#-license)

<br/>

**🚨 Detects emergencies · 🧠 Smart AI answers · 🧮 Health calculators · 🍎 Nutrition · 🌤️ AQI alerts · 💊 Reminders · 📴 Works offline**

</div>

---

## 📖 Overview

**MediMate AI** is **not just a chatbot** — it's a **safety-first health assistant** that scans *every*
message for medical emergencies *before* anything else, gives structured & validated AI answers, runs
health calculators, tracks nutrition, delivers first-aid steps, and searches the live web.

> 💡 **The best part?** It **still works with zero API keys and no internet** — thanks to a built-in
> knowledge base, calculators, Indian-food nutrition table, and offline first-aid guides. Add keys
> anytime and features light up automatically. **It is never useless.**

---

## ✨ Features

| # | Feature | What it does |
|:-:|---------|--------------|
| 🚨 | **Emergency Triage** | Scans every message for red flags (heart attack, stroke, breathing trouble, bleeding, suicidal thoughts…) and shows the right helpline **instantly**. |
| 🧠 | **AI Brain (Groq)** | Lightning-fast **LLaMA-4** answers with structured, schema-validated output. |
| 🛠️ | **9 Agent Tools** | web search · triage · calculators · first-aid · knowledge · nutrition · weather · news · reminders. |
| 🍎 | **Nutrition Tracker** | `2 roti + 1 cup dal + 1 egg` → calories + protein/carbs/fat (offline Indian-food table). |
| 🌤️ | **Weather + AQI Alerts** | Live air-quality health advice — *"AQI 180 — wear a mask, skip outdoor exercise."* |
| 💊 | **Medicine Reminders** | Set reminders; get a real **SMS (Twilio)** or an on-screen alert. |
| 📰 | **Health News Feed** | Latest curated health headlines. |
| 🧮 | **Health Calculators** | BMI · daily calories (TDEE) · water intake · ideal weight · heart-rate zones · body-fat %. |
| 🩹 | **Offline First-Aid** | Step-by-step guides for choking, burns, CPR, bleeding, snake bite & more. |
| 📖 | **Offline Knowledge Base** | Answers common conditions with **zero internet**. |
| 🗂️ | **Consultation History** | Saves every Q&A locally + exports a **Markdown health report**. |
| 🌐 | **Multi-Language** | Replies in English, Hindi, Hinglish, Spanish, French & Arabic. |
| 🎨 | **Beautiful UI** | Colorful CLI (`rich`) **and** a browser chat app (`streamlit`). |
| 📴 | **Graceful Fallback** | No key / no internet? It still helps. Add keys anytime — features auto-enable. |

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph UI["🖥️ User Interfaces"]
        CLI["💬 CLI Chat<br/>app.py"]
        WEB["🌐 Web App<br/>web_app.py"]
    end

    subgraph BRAIN["🧠 Core Engine — healthcare_agent.py"]
        ENTRY["answer_question()"]
        SCAN["🚨 Emergency Scan<br/>(always first)"]
        AGENT["🤖 PydanticAI Agent<br/>Groq · LLaMA-4"]
        OFFLINE["📴 Offline Fallback<br/>Knowledge + Calculators"]
    end

    subgraph TOOLS["🛠️ 9 Agent Tools"]
        T1["🔍 web_search"]
        T2["🚨 triage"]
        T3["🧮 calculator"]
        T4["🩹 first_aid"]
        T5["📖 knowledge"]
        T6["🍎 nutrition"]
        T7["🌤️ weather"]
        T8["📰 news"]
        T9["💊 reminder"]
    end

    subgraph EXT["☁️ External APIs (all optional)"]
        G["Groq"]
        S["Serper"]
        O["OpenWeather"]
        U["USDA"]
        N["NewsAPI"]
        TW["Twilio"]
    end

    CLI --> ENTRY
    WEB --> ENTRY
    ENTRY --> SCAN
    SCAN -->|"⚠️ danger found"| RESP["📋 Structured Response"]
    SCAN -->|"✅ safe"| AGENT
    AGENT -->|"key OK"| TOOLS
    AGENT -->|"no key / error"| OFFLINE
    OFFLINE --> RESP
    TOOLS --> RESP

    T1 --> S
    T6 --> U
    T7 --> O
    T8 --> N
    T9 --> TW
    AGENT --> G

    RESP --> CLI
    RESP --> WEB

    classDef ui fill:#3776AB,stroke:#fff,color:#fff
    classDef brain fill:#E92063,stroke:#fff,color:#fff
    classDef tool fill:#F55036,stroke:#fff,color:#fff
    classDef ext fill:#22C55E,stroke:#fff,color:#fff
    class CLI,WEB ui
    class ENTRY,SCAN,AGENT,OFFLINE brain
    class T1,T2,T3,T4,T5,T6,T7,T8,T9 tool
    class G,S,O,U,N,TW ext
```

---

## 🔄 How a Question Flows (Safety-First Logic)

```mermaid
flowchart TD
    START(["❓ User asks a question"]) --> EM{"🚨 Emergency<br/>red flags?"}
    EM -->|"YES"| ALERT["📞 Show emergency helpline<br/>+ first-aid steps<br/><b>urgency = EMERGENCY</b>"]
    ALERT --> DONE(["✅ Return response"])

    EM -->|"NO"| HASKEY{"🔑 Groq key<br/>available?"}
    HASKEY -->|"YES"| AI["🧠 Run AI Agent<br/>with 9 tools"]
    AI --> OK{"✅ Valid<br/>answer?"}
    OK -->|"YES"| SAVE["🗂️ Save to history"]
    OK -->|"NO — retry ≤5"| AI
    OK -->|"still failing"| FB["📴 Offline fallback<br/>+ honest reason note"]

    HASKEY -->|"NO"| FB
    FB --> SAVE
    SAVE --> DONE

    style START fill:#3776AB,color:#fff
    style ALERT fill:#DC2626,color:#fff
    style AI fill:#E92063,color:#fff
    style FB fill:#F59E0B,color:#fff
    style DONE fill:#22C55E,color:#fff
    style SAVE fill:#8B5CF6,color:#fff
```

---

## 🚀 Quick Start

```bash
# 1️⃣  Clone the repo
git clone https://github.com/Abhay73888/HeathCare.git
cd HeathCare

# 2️⃣  Install dependencies
pip install -r requirements.txt

# 3️⃣  Add your API keys (optional but recommended)
cp .env.example .env       # then edit .env and paste your keys

# 4️⃣  Run it!
python app.py              # 💬 interactive CLI chat
streamlit run web_app.py   # 🌐 browser web app
python healthcare_agent.py # ⚡ quick demo
```

> ✅ **No keys? No problem.** MediMate boots straight into **offline mode** and still answers common
> conditions, runs calculators, and gives first-aid guides.

---

## 🔑 Getting API Keys *(all free tiers)*

| Service | Unlocks | Get a key |
|---------|---------|-----------|
| 🧠 **Groq** | AI brain (smart answers) | https://console.groq.com/keys |
| 🔍 **Serper** | Live web search | https://serper.dev |
| 🌤️ **OpenWeather** | Weather + AQI alerts | https://openweathermap.org/api |
| 🍎 **USDA** | Live nutrition lookup | https://fdc.nal.usda.gov/api-key-signup.html |
| 📰 **NewsAPI** | Health news feed | https://newsapi.org/register |
| 💊 **Twilio** | SMS reminders *(optional)* | https://www.twilio.com/try-twilio |

Paste them into `.env`. **Every key is optional** — add them one by one to unlock more features,
no code changes needed. Check what's live anytime with `/status`.

```mermaid
flowchart LR
    A["🔑 Add a key<br/>to .env"] --> B["⚙️ config.py<br/>auto-detects it"]
    B --> C["🟢 Feature turns ON<br/>automatically"]
    C --> D["😴 No key?<br/>Safe offline mode"]
    style A fill:#3776AB,color:#fff
    style B fill:#E92063,color:#fff
    style C fill:#22C55E,color:#fff
    style D fill:#F59E0B,color:#fff
```

---

## 💬 Commands *(inside the app)*

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/bmi` · `/calories` · `/water` | Health calculators |
| `/nutrition <meal>` | Calories & macros — e.g. `/nutrition 2 roti + 1 egg` |
| `/weather [city]` | Weather + air-quality health alert |
| `/news [topic]` | Latest health news |
| `/remind <med> <HH:MM>` | Set a medicine reminder — e.g. `/remind BP tablet 14:00` |
| `/reminders` | List your medicine reminders |
| `/firstaid <x>` | First-aid steps — e.g. `/firstaid choking` |
| `/topics` · `/history` · `/report` | Offline topics · past Q&A · export report |
| `/status` | See which features are **ON / OFF** |
| `/name <you>` · `/lang <language>` | Personalize |
| `/clear` · `/quit` | Clear history · exit |

---

## 📁 Project Structure

```
healthcare-ai/
├── 🖥️  app.py                # Interactive CLI chat (start here)
├── 🌐  web_app.py            # Streamlit browser chat app
├── 🧠  healthcare_agent.py   # The AI agent brain + 9 tools
├── ⚙️  config.py             # Settings, API keys, emergency numbers
├── 🧮  calculators.py        # Health math (no API needed)
├── 🚨  emergency.py          # Triage + first-aid engine
├── 📖  knowledge.py          # Offline medical knowledge base
├── 🍎  nutrition.py          # Meal calorie/macro tracker
├── 🌤️  weather_health.py     # Weather + air-quality alerts
├── 📰  news.py               # Health news feed
├── 💊  reminders.py          # Medicine reminders (+ SMS)
├── 🗂️  history.py            # Save consultations + export reports
├── 📦  requirements.txt      # Dependencies
├── 🔑  .env.example          # API key template
└── 📄  README.md             # You are here
```

---

## 🛠️ Tech Stack

```mermaid
mindmap
  root(("🏥<br/>MediMate AI"))
    ("🧠 AI")
      ("Groq — LLaMA-4")
      ("PydanticAI Agent")
      ("Structured Output")
    ("🎨 Interfaces")
      ("Streamlit — Web")
      ("Rich — CLI")
    ("☁️ APIs")
      ("Serper — Search")
      ("OpenWeather — AQI")
      ("USDA — Nutrition")
      ("NewsAPI — News")
      ("Twilio — SMS")
    ("🐍 Core")
      ("Python 3.11+")
      ("httpx — async")
      ("python-dotenv")
```

---

## ⚠️ Medical Disclaimer

> **MediMate AI is for educational and informational purposes only.** It is **not** a substitute for
> professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.
> **In an emergency, call your local emergency number immediately.**

---

## 📜 License

Released under the **MIT License** — free to use, modify, and share.

---

<div align="center">

### 💚 Made with care for healthier lives

**If MediMate helped you, drop a ⭐ on the repo!**

<sub>Built by <a href="https://github.com/Abhay73888">Abhay Kumar Maurya</a> · Powered by Groq + PydanticAI</sub>

</div>

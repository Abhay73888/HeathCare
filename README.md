# 🏥 MediMate AI — Advanced Healthcare AI Agent

> Your friendly, always-on health companion.
> Built with **Groq (LLaMA-3.3)** · **Serper** · **PydanticAI** · **Rich**.

MediMate is not just a chatbot — it's a **safety-first health assistant** that
detects emergencies, runs health calculators, gives first-aid steps, searches
the live web, and remembers your consultations. And it **still works offline**
(no API key needed) thanks to a built-in knowledge base.

---

## ✨ Features

| # | Feature | What it does |
|---|---------|--------------|
| 🚨 | **Emergency triage** | Scans every message for red flags (heart attack, stroke, breathing trouble, bleeding, suicidal thoughts…) and shows the right helpline instantly. |
| 🧠 | **AI brain (Groq)** | Fast LLaMA-3.3 answers with structured, validated output. |
| 🛠️ | **9 agent tools** | web search, triage, calculators, first-aid, knowledge, nutrition, weather, news, reminders. |
| 🍎 | **Nutrition tracker** | "2 roti + 1 cup dal + 1 egg" → calories + protein/carbs/fat (works offline with an Indian-food table). |
| 🌤️ | **Weather + AQI alerts** | Live air-quality & weather health advice ("AQI 180 — wear a mask, skip outdoor exercise"). |
| 💊 | **Medicine reminders** | Set reminders; get a real SMS (Twilio) or an on-screen alert. |
| 📰 | **Health news feed** | Latest health headlines. |
| 🧮 | **Health calculators** | BMI, daily calories (TDEE), water intake, ideal weight, heart-rate zones, body-fat %. |
| 🩹 | **Offline first-aid** | Step-by-step guides for choking, burns, CPR, bleeding, snake bite & more. |
| 📖 | **Offline knowledge base** | Answers common conditions with zero internet. |
| 🗂️ | **Consultation history** | Saves every Q&A locally + exports a Markdown health report. |
| 🌐 | **Multi-language** | Reply in English, Hindi, Hinglish, and more. |
| 🎨 | **Beautiful CLI** | Colorful panels, tables & spinners via `rich`. |
| 📴 | **Graceful fallback** | No key / no internet? It still helps. Add keys anytime — features auto-enable. |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API keys (optional but recommended)
cp .env.example .env      # then edit .env and paste your keys

# 3. Run the interactive app
python app.py
```

Just want a quick demo?

```bash
python healthcare_agent.py
```

---

## 🔑 Getting API Keys (free)

- **Groq** (AI brain): https://console.groq.com/keys
- **Serper** (web search): https://serper.dev
- **OpenWeather** (weather + AQI): https://openweathermap.org/api
- **USDA** (nutrition): https://fdc.nal.usda.gov/api-key-signup.html
- **NewsAPI** (health news): https://newsapi.org/register
- **Twilio** (SMS reminders, optional): https://www.twilio.com/try-twilio

Put them in your `.env` file. **Every key is optional** — without keys, MediMate
runs in **offline mode** using its built-in knowledge base, calculators, food
table, and first-aid guides. Add keys anytime and features turn on automatically
(check with `/status`).

---

## 💬 Commands (inside the app)

```
/help                  Show all commands
/bmi                   BMI calculator
/calories              Daily calorie needs
/water                 Daily water intake
/nutrition <meal>      Calories & macros of food (e.g. /nutrition 2 roti + 1 egg)
/weather [city]        Weather + air-quality health alert
/news [topic]          Latest health news
/remind <med> <HH:MM>  Set a medicine reminder (e.g. /remind BP tablet 14:00)
/reminders             List your medicine reminders
/firstaid <x>          First-aid steps (e.g. /firstaid choking)
/topics                List offline health topics
/history               Show recent consultations
/report                Export a Markdown health report
/status                See which features are ON/OFF
/name <you>            Set your name
/lang <language>       Set reply language
/clear                 Clear history
/quit                  Exit
```

---

## 📁 Project Structure

```
healthcare-ai/
├── app.py                # ⭐ Interactive CLI chat (start here)
├── healthcare_agent.py   # 🧠 The AI agent brain + 9 tools
├── config.py             # ⚙️  Settings, API keys, emergency numbers
├── calculators.py        # 🧮 Health math (no API needed)
├── emergency.py          # 🚨 Triage + first-aid engine
├── knowledge.py          # 📖 Offline medical knowledge base
├── nutrition.py          # 🍎 Meal calorie/macro tracker
├── weather_health.py     # 🌤️  Weather + air-quality alerts
├── news.py               # 📰 Health news feed
├── reminders.py          # 💊 Medicine reminders (+ SMS)
├── history.py            # 🗂️  Save consultations + export reports
├── requirements.txt      # 📦 Dependencies
├── .env.example          # 🔑 API key template
└── README.md             # 📄 You are here
```

---

## ⚠️ Medical Disclaimer

MediMate AI is for **educational and informational purposes only**. It is **not**
a substitute for professional medical advice, diagnosis, or treatment. Always
consult a qualified healthcare provider. **In an emergency, call your local
emergency number immediately.**

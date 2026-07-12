"""
╔══════════════════════════════════════════════════════════════╗
║        🏥  MediMate AI  —  Interactive Health Companion       ║
║        Run:  python app.py                                    ║
╚══════════════════════════════════════════════════════════════╝

A beautiful, friendly command-line chat with your Healthcare AI Agent.

FEATURES
  • Natural chat — just type your health question.
  • 🚨 Instant emergency detection with the right helpline number.
  • Slash commands for calculators, first-aid, history & reports.

COMMANDS (type these anytime)
  /help            Show all commands
  /bmi             BMI calculator
  /calories        Daily calorie needs
  /water           Daily water intake
  /firstaid <x>    First-aid steps (e.g. /firstaid choking)
  /topics          List offline health topics
  /history         Show your recent consultations
  /report          Export a Markdown health report
  /name <you>      Set your name
  /lang <language> Set reply language (English, Hindi, Hinglish...)
  /clear           Clear consultation history
  /quit            Exit
"""

from __future__ import annotations

import asyncio
import sys

import config
import calculators
import emergency
import knowledge
import history
import nutrition
import weather_health
import news
import reminders
from healthcare_agent import answer_question, HealthcareResponse

# ── Try to use 'rich' for pretty output; fall back to plain print ──
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.text import Text
    from rich.markup import escape
    from rich import box
    _RICH = True
    console = Console()
except ImportError:  # rich not installed -> graceful plain-text mode
    _RICH = False
    console = None


# ─────────────────────────────────────────────
# Small print helpers (work with or without rich)
# ─────────────────────────────────────────────
def say(text: str, style: str = ""):
    if _RICH:
        console.print(text, style=style)
    else:
        print(text)


def panel(body: str, title: str = "", style: str = "cyan"):
    if _RICH:
        console.print(Panel(body, title=title, border_style=style, box=box.ROUNDED))
    else:
        print(f"\n=== {title} ===\n{body}\n")


def ask(prompt: str, default: str = "") -> str:
    if _RICH:
        return Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]", default=default)
    raw = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return raw or default


# ─────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────
BANNER = r"""
 __  __          _ _ __  __       _         _    ___
|  \/  | ___  __| (_)  \/  | __ _| |_ ___  | |  |_ _|
| |\/| |/ _ \/ _` | | |\/| |/ _` | __/ _ \ | |   | |
| |  | |  __/ (_| | | |  | | (_| | ||  __/ | |   | |
|_|  |_|\___|\__,_|_|_|  |_|\__,_|\__\___| |_|  |___|
"""


def show_banner():
    if _RICH:
        console.print(Text(BANNER, style="bold cyan"))
        console.print(f"[bold]{config.APP_NAME}[/bold] v{config.VERSION} — "
                      f"[italic]{config.APP_TAGLINE}[/italic]")
        console.print(f"[dim]{config.status_banner()}[/dim]")
        console.print("[dim]Type your health question, or /help for commands. /quit to exit.[/dim]\n")
    else:
        print(BANNER)
        print(f"{config.APP_NAME} v{config.VERSION} — {config.APP_TAGLINE}")
        print(config.status_banner())
        print("Type your question, or /help. /quit to exit.\n")


# ─────────────────────────────────────────────
# Pretty-print a HealthcareResponse
# ─────────────────────────────────────────────
_URGENCY_STYLE = {
    "emergency": ("🚨 EMERGENCY", "bold white on red"),
    "urgent":    ("⚠️  URGENT", "bold yellow"),
    "routine":   ("🩺 ROUTINE", "cyan"),
    "self-care": ("🏠 SELF-CARE", "green"),
    "informational": ("ℹ️  INFO", "blue"),
}


def render_response(resp: HealthcareResponse):
    label, style = _URGENCY_STYLE.get(resp.urgency_level, ("ℹ️  INFO", "blue"))

    body = resp.answer
    if resp.possible_causes:
        body += "\n\n🔎 Possible causes:\n" + "\n".join(f"  • {c}" for c in resp.possible_causes)
    if resp.recommended_actions:
        body += "\n\n📋 What to do:\n" + "\n".join(f"  • {a}" for a in resp.recommended_actions)
    body += f"\n\n👩‍⚕️ When to see a doctor: {resp.when_to_see_doctor}"

    # Be honest about where the answer came from (AI vs offline brain).
    source_badge = {"ai": "🧠 AI", "offline": "📴 Offline", "emergency": "🚨 Emergency"}.get(resp.source, "🧠 AI")
    if resp.source == "offline" and resp.note:
        body += f"\n\n⚠️ {resp.note}  (Showing an offline answer.)"
    body += (f"\n\n📊 Confidence: {resp.confidence}   {source_badge}"
             f"   🌐 Web searched: {'Yes' if resp.web_searched else 'No'}")

    panel(body, title=label, style="red" if resp.urgency_level == "emergency" else "cyan")

    if resp.follow_up_questions:
        say("\n💬 You might also ask:", "dim")
        for q in resp.follow_up_questions:
            say(f"   → {q}", "dim")
    say(f"\n{resp.disclaimer}", "dim italic")


# ─────────────────────────────────────────────
# SLASH COMMANDS
# ─────────────────────────────────────────────
def cmd_help():
    rows = [
        ("/help", "Show this help"),
        ("/bmi", "BMI calculator"),
        ("/calories", "Daily calorie needs (TDEE)"),
        ("/water", "Daily water intake"),
        ("/nutrition <meal>", "Calories & macros of food eaten 🍎"),
        ("/weather [city]", "Weather + air-quality health alert 🌤️"),
        ("/news [topic]", "Latest health news 📰"),
        ("/remind <med> <HH:MM>", "Set a medicine reminder 💊"),
        ("/reminders", "List your medicine reminders"),
        ("/firstaid <topic>", "First-aid steps (choking, burns, cpr...)"),
        ("/topics", "List offline health topics"),
        ("/history", "Your recent consultations"),
        ("/report", "Export a Markdown health report"),
        ("/status", "Which features are ON/OFF"),
        ("/name <you>", "Set your name"),
        ("/lang <language>", "Set reply language"),
        ("/clear", "Clear consultation history"),
        ("/quit", "Exit the app"),
    ]
    if _RICH:
        t = Table(title="💡 Commands", box=box.ROUNDED, border_style="cyan")
        t.add_column("Command", style="bold green")
        t.add_column("What it does")
        for c, d in rows:
            t.add_row(c, d)
        console.print(t)
    else:
        print("\nCommands:")
        for c, d in rows:
            print(f"  {c:<20} {d}")


def cmd_bmi():
    try:
        w = float(ask("Weight (kg)"))
        h = float(ask("Height (cm)"))
    except ValueError:
        return say("Please enter valid numbers.", "red")
    r = calculators.bmi(w, h)
    panel(f"{r['emoji']}  Your BMI is [bold]{r['bmi']}[/bold] → {r['category']}\n\n{r['note']}"
          if _RICH else f"{r['emoji']} BMI {r['bmi']} → {r['category']}\n{r['note']}",
          title="BMI Result", style="green")


def cmd_calories():
    try:
        w = float(ask("Weight (kg)"))
        h = float(ask("Height (cm)"))
        age = int(ask("Age"))
    except ValueError:
        return say("Please enter valid numbers.", "red")
    sex = ask("Sex (male/female)", "male")
    act = ask("Activity (sedentary/light/moderate/active/very_active)", "moderate")
    r = calculators.daily_calories(w, h, age, sex, act)
    body = (f"🔥 BMR (at rest): {r['bmr']} kcal/day\n"
            f"🍽️  Maintenance:  {r['maintenance']} kcal/day\n"
            f"📉 Weight loss:  {r['weight_loss']} kcal/day\n"
            f"📈 Weight gain:  {r['weight_gain']} kcal/day")
    panel(body, title="Daily Calorie Needs", style="green")


def cmd_water():
    try:
        w = float(ask("Weight (kg)"))
        mins = int(ask("Daily activity (minutes)", "30"))
    except ValueError:
        return say("Please enter valid numbers.", "red")
    r = calculators.water_intake(w, mins)
    panel(f"💧 Drink about [bold]{r['litres']} litres[/bold] (~{r['glasses']} glasses) per day."
          if _RICH else f"💧 Drink about {r['litres']} litres (~{r['glasses']} glasses) per day.",
          title="Daily Water Intake", style="blue")


def cmd_firstaid(arg: str):
    if not arg:
        topics = ", ".join(emergency.available_first_aid_topics())
        return say(f"Usage: /firstaid <topic>. Available: {topics}", "yellow")
    guide = emergency.first_aid(arg)
    if not guide:
        topics = ", ".join(emergency.available_first_aid_topics())
        return say(f"No guide for '{arg}'. Available: {topics}", "yellow")
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(guide["steps"], 1))
    panel(steps, title=f"🩹 First Aid — {guide['condition'].title()}", style="red")


def cmd_topics():
    kb = ", ".join(knowledge.all_topics())
    fa = ", ".join(emergency.available_first_aid_topics())
    panel(f"📖 Health topics: {kb}\n\n🩹 First-aid guides: {fa}", title="Offline Topics", style="cyan")


async def cmd_nutrition(arg: str):
    meal = arg or ask("What did you eat? (e.g. 2 roti + 1 cup dal + 1 egg)")
    if not meal.strip():
        return
    result = await nutrition.analyze_meal(meal)
    panel(nutrition.format_meal(result), title="🍎 Nutrition", style="green")


async def cmd_weather(arg: str):
    city = arg or ask("Which city?", config.DEFAULT_CITY)
    data = await weather_health.get_weather_health(city)
    panel(weather_health.format_weather(data), title="🌤️ Weather & Air Quality", style="blue")


async def cmd_news(arg: str):
    data = await news.get_health_news(arg or "health")
    panel(news.format_news(data), title="📰 Health News", style="cyan")


def cmd_remind(arg: str):
    # Expect: "<medicine> <HH:MM>"  e.g. "BP tablet 14:00"
    parts = arg.rsplit(maxsplit=1)
    if len(parts) < 2:
        med = ask("Medicine name")
        t = ask("Time (HH:MM, 24-hour)")
    else:
        med, t = parts[0], parts[1]
    result = reminders.add_reminder(med, t, patient="You")
    if result["ok"]:
        r = result["reminder"]
        say(f"✅ Reminder set: 💊 {r['medicine']} daily at {r['time']}.", "green")
        if not config.HAS_SMS:
            say("   (Local mode — I'll show it on screen. Add Twilio keys for real SMS.)", "dim")
    else:
        say(f"⚠️ {result['error']}", "yellow")


def cmd_reminders():
    items = reminders.list_reminders()
    if _RICH and items:
        t = Table(title="💊 Medicine Reminders", box=box.ROUNDED, border_style="cyan")
        t.add_column("ID", style="dim")
        t.add_column("Time", style="bold green")
        t.add_column("Medicine")
        t.add_column("Note", style="dim")
        for r in items:
            t.add_row(str(r["id"]), r["time"], r["medicine"], r.get("note", ""))
        console.print(t)
    else:
        panel(reminders.format_reminders(items), title="Reminders", style="cyan")


def cmd_status():
    feats = config.feature_status()
    if _RICH:
        t = Table(title="⚙️  Feature Status", box=box.ROUNDED, border_style="cyan")
        t.add_column("Feature")
        t.add_column("Status", justify="center")
        for name, on in feats.items():
            t.add_row(name, "[green]🟢 ON[/green]" if on else "[dim]⚪ off (add key)[/dim]")
        console.print(t)
    else:
        for name, on in feats.items():
            print(f"  {'🟢 ON ' if on else '⚪ off'}  {name}")


def check_due_reminders():
    """On startup: gently warn about any reminders due soon."""
    due = reminders.due_now(window_min=60)
    for r in due:
        when = "now" if r["in_minutes"] == 0 else f"in {r['in_minutes']} min"
        msg = f"💊 Reminder: take your {r['medicine']} ({when}, at {r['time']})"
        say(msg, "bold yellow")
        reminders.send_sms(msg)  # SMS if configured, else silent local


def cmd_history(patient: str):
    records = history.get_history(patient, limit=10)
    if not records:
        return say("No consultations yet.", "dim")
    if _RICH:
        t = Table(title=f"🗂️  Recent consultations — {patient}", box=box.ROUNDED, border_style="cyan")
        t.add_column("When", style="dim")
        t.add_column("Question")
        t.add_column("Urgency", style="bold")
        for r in records:
            t.add_row(r["timestamp"], r["question"][:50], r.get("urgency", ""))
        console.print(t)
    else:
        for r in records:
            print(f"  [{r['timestamp']}] ({r.get('urgency','')}) {r['question']}")


def cmd_report(patient: str):
    path = history.export_report(patient)
    say(f"📄 Report saved to: {path}", "green")


# ─────────────────────────────────────────────
# MAIN CHAT LOOP
# ─────────────────────────────────────────────
async def chat_loop():
    show_banner()

    patient = ask("👋 What's your name?", "Friend")
    language = "English"
    say(f"\nNice to meet you, {patient}! How can I help you today? 🩺", "green")

    # Gently surface any medicine reminders due within the next hour
    check_due_reminders()
    say("", "")

    while True:
        try:
            if _RICH:
                user = Prompt.ask(f"\n[bold magenta]{escape(patient)} ›[/bold magenta]")
            else:
                user = input(f"\n{patient} > ")
        except (KeyboardInterrupt, EOFError):
            say("\n👋 Take care! Stay healthy.", "cyan")
            break

        user = user.strip()
        if not user:
            continue

        # ---- Slash commands ----
        if user.startswith("/"):
            parts = user[1:].split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("quit", "exit", "q"):
                say("\n👋 Take care! Stay healthy.", "cyan")
                break
            elif cmd == "help":
                cmd_help()
            elif cmd == "bmi":
                cmd_bmi()
            elif cmd == "calories":
                cmd_calories()
            elif cmd == "water":
                cmd_water()
            elif cmd == "firstaid":
                cmd_firstaid(arg)
            elif cmd == "topics":
                cmd_topics()
            elif cmd == "nutrition":
                await cmd_nutrition(arg)
            elif cmd == "weather":
                await cmd_weather(arg)
            elif cmd == "news":
                await cmd_news(arg)
            elif cmd == "remind":
                cmd_remind(arg)
            elif cmd == "reminders":
                cmd_reminders()
            elif cmd == "status":
                cmd_status()
            elif cmd == "history":
                cmd_history(patient)
            elif cmd == "report":
                cmd_report(patient)
            elif cmd == "name":
                patient = arg or patient
                say(f"Got it — I'll call you {patient}. 🙂", "green")
            elif cmd == "lang":
                language = arg or language
                say(f"I'll reply in {language} from now on. 🌐", "green")
            elif cmd == "clear":
                history.clear_history()
                say("🧹 History cleared.", "green")
            else:
                say(f"Unknown command '/{cmd}'. Type /help.", "yellow")
            continue

        # ---- Natural health question -> the AI agent ----
        if _RICH:
            with console.status("[cyan]🩺 Thinking...", spinner="dots"):
                resp = await answer_question(user, patient, language)
        else:
            print("🩺 Thinking...")
            resp = await answer_question(user, patient, language)

        render_response(resp)


def main():
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\n👋 Bye!")
        sys.exit(0)


if __name__ == "__main__":
    main()

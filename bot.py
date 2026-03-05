"""
Social Team AI Agent — Telegram Bot
====================================
Commands:
  /start    — Welcome message
  /help     — Show all commands
  /tasks    — Show all tasks by status
  /kpi      — KPI analysis across all platforms
  /report   — Full weekly team report
  /urgent   — HIGH priority + overdue tasks only
  /assign   — How to assign a task
  + natural language for anything else

Auto:
  - 9 AM daily briefing
  - 6 PM overdue task check
  - Monday 9 AM weekly report
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

from config import (
    TELEGRAM_BOT_TOKEN, MANAGER_CHAT_ID, TEAM_GROUP_ID,
    DAILY_BRIEF_HOUR, TIMEZONE
)
from sheets import get_tasks, get_kpi_data, get_team_config, write_task, write_agent_log
from agent import ask_claude, build_context

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ─── COMMAND HANDLERS ───────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚡ *Social Team AI Agent* — Online\n\n"
        "I manage your social team's tasks and KPIs across:\n"
        "📘 FB  📸 IG  ✈️ TG  💬 WA  🎵 TikTok  ▶️ YT  🐦 X\n\n"
        "*Commands:*\n"
        "/tasks — All tasks by status\n"
        "/kpi — Platform KPI analysis\n"
        "/report — Full team report\n"
        "/urgent — High priority + overdue only\n"
        "/help — All commands\n\n"
        "Or just type anything in natural language.\n"
        "_e.g. 'assign Raj to fix YouTube by Friday'_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚡ *Available Commands*\n\n"
        "*/tasks* — All tasks grouped by status\n"
        "*/kpi* — KPI analysis for all 7 platforms\n"
        "*/report* — Weekly performance report\n"
        "*/urgent* — HIGH priority + overdue tasks\n"
        "*/start* — Welcome message\n\n"
        "*Natural Language:*\n"
        "• _'assign Ana to post IG reels by Friday'_\n"
        "• _'why is YouTube underperforming?'_\n"
        "• _'what did Raj complete this week?'_\n"
        "• _'show me overdue tasks for Mia'_\n"
        "• _'generate daily brief'_\n\n"
        "📊 Data is pulled live from Google Sheets.\n"
        "🤖 Powered by Claude AI."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Fetching tasks...", parse_mode="Markdown")
    tasks = get_tasks()
    kpi = get_kpi_data()
    ctx = build_context(tasks, kpi)
    reply = ask_claude(
        user_message="Show all current tasks grouped by status (To Do, In Progress, Done). "
                     "For each task include assignee, platform, priority, and due date. "
                     "Flag any overdue or HIGH priority items prominently. "
                     "Format for Telegram with emojis and bold text.",
        context=ctx
    )
    await update.message.reply_text(reply, parse_mode="Markdown")
    write_agent_log("📩 User", "/tasks", update.effective_user.username or "Manager", reply[:100])


async def cmd_kpi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Analyzing KPIs...", parse_mode="Markdown")
    tasks = get_tasks()
    kpi = get_kpi_data()
    ctx = build_context(tasks, kpi)
    reply = ask_claude(
        user_message="Analyze KPI performance across all platforms. "
                     "1) Rank platforms best to worst. "
                     "2) Flag any critical platforms (below 50% goal). "
                     "3) Give 2-3 specific action items with platform and assignee names. "
                     "Format clearly for Telegram.",
        context=ctx
    )
    await update.message.reply_text(reply, parse_mode="Markdown")
    write_agent_log("📩 User", "/kpi", update.effective_user.username or "Manager", reply[:100])


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Generating report...", parse_mode="Markdown")
    tasks = get_tasks()
    kpi = get_kpi_data()
    ctx = build_context(tasks, kpi)
    reply = ask_claude(
        user_message="Generate a comprehensive weekly team performance report. Include: "
                     "1) Overall team score and trend. "
                     "2) Platform KPI summary table (all 7 platforms). "
                     "3) Task completion rate per team member. "
                     "4) Top performer shoutout. "
                     "5) 3 priority actions for next week. "
                     "Format for Telegram with clear sections.",
        context=ctx
    )
    await update.message.reply_text(reply, parse_mode="Markdown")
    write_agent_log("📩 User", "/report", update.effective_user.username or "Manager", reply[:100])


async def cmd_urgent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 Checking urgent items...", parse_mode="Markdown")
    tasks = get_tasks()
    kpi = get_kpi_data()
    ctx = build_context(tasks, kpi)
    reply = ask_claude(
        user_message="Show ONLY: 1) All HIGH priority tasks not yet done. "
                     "2) All overdue tasks (past due date). "
                     "3) Any platforms in CRITICAL status. "
                     "Be concise. Use 🔴 for each item. Sort by urgency.",
        context=ctx
    )
    await update.message.reply_text(reply, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all natural language messages."""
    user_text = update.message.text
    if not user_text:
        return

    await update.message.reply_text("🤔 Thinking...", parse_mode="Markdown")

    tasks = get_tasks()
    kpi = get_kpi_data()
    ctx = build_context(tasks, kpi)

    # Detect task assignment intent
    lower = user_text.lower()
    is_assignment = any(w in lower for w in ["assign", "create task", "new task", "add task"])

    reply = ask_claude(
        user_message=user_text,
        context=ctx,
        extra_instruction=(
            "If this is a task assignment request, extract: title, assignee, platform, priority, due date. "
            "Confirm the assignment clearly. At the end add a line starting with 'TASK_DATA:' followed by "
            "JSON like: {\"title\":\"...\",\"assignee\":\"...\",\"platform\":\"...\",\"priority\":\"HIGH/MED/LOW\",\"due\":\"YYYY-MM-DD\"}"
            if is_assignment else ""
        )
    )

    # Parse and save task if assignment detected
    if is_assignment and "TASK_DATA:" in reply:
        try:
            import json, re
            json_str = reply.split("TASK_DATA:")[1].strip()
            json_str = re.sub(r'```json|```', '', json_str).strip()
            task_data = json.loads(json_str)
            write_task(task_data)
            # Clean reply for user (remove raw JSON)
            reply = reply.split("TASK_DATA:")[0].strip()
            reply += "\n\n✅ *Task saved to Google Sheets.*"
        except Exception as e:
            logger.warning(f"Could not parse task JSON: {e}")

    await update.message.reply_text(reply, parse_mode="Markdown")
    write_agent_log("📩 User", "NL Command", update.effective_user.username or "User", user_text[:60])


# ─── SCHEDULED JOBS ─────────────────────────────────────

async def job_daily_brief(app: Application):
    """Send daily morning briefing to manager."""
    logger.info("Running daily brief job")
    try:
        tasks = get_tasks()
        kpi = get_kpi_data()
        ctx = build_context(tasks, kpi)
        reply = ask_claude(
            user_message=(
                "Generate the daily morning briefing. Include: "
                "1) 🔴 HIGH priority tasks due today with assignee names. "
                "2) Any overdue tasks with days overdue. "
                "3) KPI alerts — any platform below 70% goal. "
                "4) Quick motivational note. "
                "Keep it under 300 words. Format for Telegram."
            ),
            context=ctx
        )
        await app.bot.send_message(chat_id=MANAGER_CHAT_ID, text=reply, parse_mode="Markdown")
        write_agent_log("⏰ Schedule", "Daily Brief", "Manager", reply[:100])
    except Exception as e:
        logger.error(f"Daily brief failed: {e}")


async def job_overdue_check(app: Application):
    """Evening overdue task check."""
    logger.info("Running overdue check job")
    try:
        tasks = get_tasks()
        kpi = get_kpi_data()
        ctx = build_context(tasks, kpi)
        reply = ask_claude(
            user_message=(
                "Check for overdue tasks. List ONLY tasks past their due date that are not done. "
                "For each: task name, assignee, how many days overdue. "
                "If none: say 'No overdue tasks today ✅'. "
                "Be brief and direct."
            ),
            context=ctx
        )
        await app.bot.send_message(chat_id=MANAGER_CHAT_ID, text=f"🌙 *Evening Check*\n\n{reply}", parse_mode="Markdown")
        write_agent_log("⏰ Schedule", "Overdue Check", "Manager", reply[:100])
    except Exception as e:
        logger.error(f"Overdue check failed: {e}")


async def job_weekly_report(app: Application):
    """Monday weekly report."""
    logger.info("Running weekly report job")
    try:
        tasks = get_tasks()
        kpi = get_kpi_data()
        ctx = build_context(tasks, kpi)
        reply = ask_claude(
            user_message=(
                "Generate the weekly performance report. "
                "1) Best and worst performing platforms this week. "
                "2) Task completion rate per team member with scores. "
                "3) Top 3 actions needed this coming week. "
                "4) One platform to watch closely. "
                "Format clearly for Telegram."
            ),
            context=ctx
        )
        msg = f"📊 *Weekly Report — {__import__('datetime').date.today().strftime('%b %d, %Y')}*\n\n{reply}"
        await app.bot.send_message(chat_id=MANAGER_CHAT_ID, text=msg, parse_mode="Markdown")
        write_agent_log("⏰ Schedule", "Weekly Report", "Manager", reply[:100])
    except Exception as e:
        logger.error(f"Weekly report failed: {e}")


# ─── MAIN ────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(CommandHandler("kpi", cmd_kpi))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("urgent", cmd_urgent))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Scheduler
    tz = pytz.timezone(TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    # Daily brief: 9 AM
    scheduler.add_job(
        lambda: asyncio.ensure_future(job_daily_brief(app)),
        "cron", hour=DAILY_BRIEF_HOUR, minute=0
    )
    # Evening check: 6 PM
    scheduler.add_job(
        lambda: asyncio.ensure_future(job_overdue_check(app)),
        "cron", hour=18, minute=0
    )
    # Weekly report: Monday 9 AM
    scheduler.add_job(
        lambda: asyncio.ensure_future(job_weekly_report(app)),
        "cron", day_of_week="mon", hour=DAILY_BRIEF_HOUR, minute=0
    )

    scheduler.start()
    logger.info("Scheduler started. Bot running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

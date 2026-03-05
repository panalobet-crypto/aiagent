"""
agent.py — Claude API integration for Social Team AI Agent
==========================================================
Builds context from Sheets data and calls Claude API.
"""

import json
import logging
from datetime import date
from typing import List, Dict, Optional

import anthropic

from config import (
    CLAUDE_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS,
    TEAM_MEMBERS, PLATFORMS
)

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    return _client


SYSTEM_PROMPT = """You are the Social Team Operations AI Agent. You manage a social media team across 7 platforms: Facebook, Instagram, Telegram, WhatsApp, TikTok, YouTube, and Twitter/X.

Your two core specialties:
1. KPI ANALYSIS — Analyze platform performance, identify underperformers, give specific improvement actions with measurable targets.
2. TASK MANAGEMENT — Track tasks, create new ones, assign work, set priorities, report on completion.

Team members:
- Ana Lima: Facebook & Instagram manager
- Raj Kumar: TikTok & YouTube specialist
- Mia Nguyen: Telegram & WhatsApp community manager
- Jun Chen: Twitter/X & data analytics

Response rules:
- Always format for Telegram: use **bold** for headers, emoji for visual cues
- Be direct and operational — no fluff or filler
- Always mention specific names when assigning or reviewing tasks
- Flag CRITICAL/overdue items first with 🔴
- Keep responses under 400 words unless generating a full report
- Use simple language — avoid technical jargon
- Never make up data — only use what's in the provided context
"""


def build_context(tasks: List[Dict], kpi_data: List[Dict]) -> str:
    """Format tasks and KPI data into a context string for Claude."""
    today = date.today().isoformat()

    # Summarize tasks
    if tasks:
        todo = [t for t in tasks if "To Do" in str(t.get("Status", ""))]
        in_progress = [t for t in tasks if "Progress" in str(t.get("Status", ""))]
        done = [t for t in tasks if "Done" in str(t.get("Status", ""))]
        overdue = [
            t for t in tasks
            if t.get("Due Date") and str(t.get("Due Date")) < today
            and "Done" not in str(t.get("Status", ""))
        ]
        task_summary = (
            f"TASKS: {len(tasks)} total | "
            f"{len(todo)} To Do | {len(in_progress)} In Progress | {len(done)} Done | "
            f"{len(overdue)} OVERDUE\n"
        )
        task_details = json.dumps(tasks, ensure_ascii=False, indent=1)
    else:
        task_summary = "TASKS: No task data available.\n"
        task_details = "[]"

    # Summarize KPIs
    if kpi_data:
        critical = [k for k in kpi_data if "Critical" in str(k.get("Status", ""))]
        kpi_summary = (
            f"KPI PLATFORMS: {len(kpi_data)} tracked | "
            f"{len(critical)} CRITICAL\n"
        )
        kpi_details = json.dumps(kpi_data, ensure_ascii=False, indent=1)
    else:
        kpi_summary = "KPI DATA: No KPI data available.\n"
        kpi_details = "[]"

    return (
        f"Today: {today}\n\n"
        f"{task_summary}"
        f"{kpi_summary}\n"
        f"=== TASK DATA ===\n{task_details}\n\n"
        f"=== KPI DATA ===\n{kpi_details}"
    )


def ask_claude(
    user_message: str,
    context: str,
    extra_instruction: str = ""
) -> str:
    """
    Send a message to Claude with current team context.
    Returns the response text.
    """
    try:
        client = _get_client()

        # Build full prompt
        full_message = user_message
        if extra_instruction:
            full_message += f"\n\nAdditional instruction: {extra_instruction}"

        full_message += f"\n\n--- CURRENT TEAM DATA ---\n{context}"

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": full_message}
            ]
        )

        return response.content[0].text

    except anthropic.APIConnectionError:
        logger.error("Claude API connection failed")
        return "⚠️ Cannot connect to AI. Check your API key and internet connection."
    except anthropic.RateLimitError:
        logger.error("Claude API rate limit hit")
        return "⚠️ AI rate limit reached. Please try again in a moment."
    except anthropic.APIStatusError as e:
        logger.error(f"Claude API error: {e.status_code} — {e.message}")
        return f"⚠️ AI error ({e.status_code}). Please try again."
    except Exception as e:
        logger.error(f"ask_claude unexpected error: {e}")
        return "⚠️ Something went wrong. Please try again."

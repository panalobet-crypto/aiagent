"""
sheets.py — Google Sheets read/write for Social Team AI Agent
=============================================================
Reads: Task Tracker, KPI Dashboard
Writes: Task Tracker (new tasks), Agent Log
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

import gspread
from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_SHEET_ID,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SERVICE_ACCOUNT_JSON
)

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]

_client: Optional[gspread.Client] = None


def _get_client() -> gspread.Client:
    global _client
    if _client is None:
        if GOOGLE_SERVICE_ACCOUNT_JSON:
            # Railway / cloud: JSON passed as env var string
            info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        else:
            # Local: JSON file on disk
            creds = Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client


def _get_sheet(tab_name: str) -> gspread.Worksheet:
    client = _get_client()
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    return spreadsheet.worksheet(tab_name)


def get_tasks() -> List[Dict]:
    """Read all tasks from the Task Tracker tab."""
    try:
        ws = _get_sheet("Task Tracker")
        records = ws.get_all_records()
        # Clean up empty rows
        return [r for r in records if r.get("Task Title", "").strip()]
    except Exception as e:
        logger.error(f"get_tasks failed: {e}")
        return []


def get_kpi_data() -> List[Dict]:
    """Read KPI data from the Dashboard tab."""
    try:
        ws = _get_sheet("Dashboard")
        records = ws.get_all_records()
        return [r for r in records if r.get("Platform", "").strip()]
    except Exception as e:
        logger.error(f"get_kpi_data failed: {e}")
        return []


def get_team_config() -> Dict:
    """Read config values from the Config tab."""
    try:
        ws = _get_sheet("Config")
        records = ws.get_all_records()
        return {r["Key"]: r["Value"] for r in records if r.get("Key")}
    except Exception as e:
        logger.error(f"get_team_config failed: {e}")
        return {}


def write_task(task_data: Dict) -> bool:
    """
    Write a new task to the Task Tracker tab.
    task_data keys: title, assignee, platform, priority, due, notes (optional)
    """
    try:
        ws = _get_sheet("Task Tracker")

        # Generate task ID based on row count
        all_rows = ws.get_all_values()
        task_id = f"T{len(all_rows):03d}"

        now = datetime.now().strftime("%Y-%m-%d")
        row = [
            task_id,
            task_data.get("title", ""),
            task_data.get("platform", ""),
            task_data.get("assignee", ""),
            task_data.get("priority", "MED"),
            "To Do",
            task_data.get("due", ""),
            now,
            "",  # completed date
            task_data.get("notes", "AI-assigned"),
            "✅"  # reminder sent
        ]
        ws.append_row(row)
        logger.info(f"Task written: {task_id} — {task_data.get('title')}")
        return True
    except Exception as e:
        logger.error(f"write_task failed: {e}")
        return False


def update_task_status(task_id: str, new_status: str) -> bool:
    """Update the status of a task by Task ID."""
    try:
        ws = _get_sheet("Task Tracker")
        cell = ws.find(task_id)
        if cell:
            # Status is column 6 (F)
            ws.update_cell(cell.row, 6, new_status)
            if new_status == "Done":
                ws.update_cell(cell.row, 9, datetime.now().strftime("%Y-%m-%d"))
            return True
        return False
    except Exception as e:
        logger.error(f"update_task_status failed: {e}")
        return False


def write_agent_log(trigger: str, action: str, target: str, summary: str) -> bool:
    """Append a line to the Agent Log tab."""
    try:
        ws = _get_sheet("Agent Log")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [now, trigger, action, target, summary, "✅ Done", ""]
        ws.append_row(row)
        return True
    except Exception as e:
        logger.warning(f"write_agent_log failed (non-critical): {e}")
        return False

"""
sheets.py — Google Sheets read/write for Social Team AI Agent
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
            info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client


def _get_sheet(tab_name: str) -> gspread.Worksheet:
    client = _get_client()
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    return spreadsheet.worksheet(tab_name)


def get_tasks() -> List[Dict]:
    try:
        ws = _get_sheet("Task Tracker")
        records = ws.get_all_records(head=2)
        return [r for r in records if str(r.get("Task ID", "")).strip()]
    except Exception as e:
        logger.error(f"get_tasks failed: {e}")
        return []


def get_kpi_data() -> List[Dict]:
    try:
        ws = _get_sheet("Dashboard")
        records = ws.get_all_records(head=2)
        return [r for r in records if str(r.get("Platform", "")).strip()]
    except Exception as e:
        logger.error(f"get_kpi_data failed: {e}")
        return []


def get_team_config() -> Dict:
    try:
        ws = _get_sheet("Config")
        records = ws.get_all_records(head=2)
        return {r["Key"]: r["Value"] for r in records if r.get("Key")}
    except Exception as e:
        logger.error(f"get_team_config failed: {e}")
        return {}


def write_task(task_data: Dict) -> bool:
    try:
        ws = _get_sheet("Task Tracker")
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
            "",
            task_data.get("notes", "AI-assigned"),
            "✅"
        ]
        ws.append_row(row)
        logger.info(f"Task written: {task_id} — {task_data.get('title')}")
        return True
    except Exception as e:
        logger.error(f"write_task failed: {e}")
        return False


def write_agent_log(trigger: str, action: str, target: str, summary: str) -> bool:
    try:
        ws = _get_sheet("Agent Log")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [now, trigger, action, target, summary, "✅ Done", ""]
        ws.append_row(row)
        return True
    except Exception as e:
        logger.warning(f"write_agent_log failed (non-critical): {e}")
        return False

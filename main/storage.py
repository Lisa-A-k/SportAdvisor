from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional
import streamlit as st
from data import DEFAULT_PROFILE

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "user_data.json"

def build_app_data() -> Dict:
    return {
        "profile": st.session_state.get("profile", {}),
        "progress_history": st.session_state.get("progress_history", []),
        "feedback_list": st.session_state.get("feedback_list", {}),
        "rest_days": st.session_state.get("rest_days", [6]),
        "view_year": st.session_state.get("view_year"),
        "view_month": st.session_state.get("view_month"),
        "saved_at": datetime.now().isoformat(),
    }
    
def apply_app_data(data: Dict) -> None:
    if "profile" in data:
        merged = DEFAULT_PROFILE.copy()
        merged.update(data["profile"])
        st.session_state["profile"] = merged
    if "progress_history" in data:
        st.session_state["progress_history"] = data["progress_history"]
    if "feedback_list" in data:
        st.session_state["feedback_list"] = data["feedback_list"]
    if "rest_days" in data:
        st.session_state["rest_days"] = data["rest_days"]
        st.session_state["profile"]["rest_days"] = data["rest_days"]
    if "view_year" in data:
        st.session_state["view_year"] = data["view_year"]
    if "view_month" in data:
        st.session_state["view_month"] = data["view_month"]
def save_app_data_to_disk() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(build_app_data(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def load_app_data_from_disk() -> Optional[Dict]:
    if not DATA_FILE.exists():
        return None
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

def init_session_state() -> None:
    if "storage_initialized" in st.session_state:
        return

    st.session_state["profile"] = DEFAULT_PROFILE.copy()
    st.session_state["progress_history"] = []
    st.session_state["feedback_list"] = {}
    st.session_state["rest_days"] = DEFAULT_PROFILE.get("rest_days", [6])
    st.session_state["view_year"] = date.today().year
    st.session_state["view_month"] = date.today().month
    st.session_state["selected_date"] = None

    saved_data = load_app_data_from_disk()
    if saved_data:
        apply_app_data(saved_data)

    st.session_state["storage_initialized"] = True

def load_feedback() -> dict:
    return st.session_state.get("feedback_list", {})

def save_feedback(feedback: dict) -> None:
    st.session_state["feedback_list"] = feedback
    save_app_data_to_disk()

def export_app_data() -> str:
    return json.dumps(build_app_data(), ensure_ascii=False, indent=2)

def import_app_data(uploaded_file) -> None:
    data = json.load(uploaded_file)
    apply_app_data(data)
    save_app_data_to_disk()

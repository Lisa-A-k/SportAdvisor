from __future__ import annotations

import json
from datetime import date, datetime

import streamlit as st

from data import DEFAULT_PROFILE


def init_session_state() -> None:
    if "profile" not in st.session_state:
        st.session_state["profile"] = DEFAULT_PROFILE.copy()
    else:
        merged = DEFAULT_PROFILE.copy()
        merged.update(st.session_state["profile"])
        st.session_state["profile"] = merged

    st.session_state.setdefault("progress_history", [])
    st.session_state.setdefault("feedback_list", {})
    st.session_state.setdefault("rest_days", st.session_state["profile"].get("rest_days", [6]))
    st.session_state.setdefault("view_year", date.today().year)
    st.session_state.setdefault("view_month", date.today().month)
    st.session_state.setdefault("selected_date", None)


def load_feedback() -> dict:
    return st.session_state.get("feedback_list", {})


def save_feedback(feedback: dict) -> None:
    st.session_state["feedback_list"] = feedback


def export_app_data() -> str:
    data = {
        "profile": st.session_state.get("profile", {}),
        "progress_history": st.session_state.get("progress_history", []),
        "feedback_list": st.session_state.get("feedback_list", {}),
        "rest_days": st.session_state.get("rest_days", [6]),
        "view_year": st.session_state.get("view_year"),
        "view_month": st.session_state.get("view_month"),
        "saved_at": datetime.now().isoformat(),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def import_app_data(uploaded_file) -> None:
    data = json.load(uploaded_file)
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

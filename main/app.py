from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from data import DAYS_OF_WEEK, MONTHS_RU_NUM, PSYCHOLOGY_GROUPS, PSYCHOLOGY_QUESTIONS
from logic import (
    QUALITY_ORDER,
    compute_qualities,
    generate_monthly_plan,
    get_top_psych_group,
    motivation_message,
    recommend_sports,
    summarize_feedback_for_month,
)
from storage import export_app_data, import_app_data, init_session_state, load_feedback, save_app_data_to_disk, save_feedback

EMOJI_LABELS = {
    "💪": "Силовая тренировка",
    "🔥": "Интенсивная тренировка",
    "😴": "Нужен отдых",
    "✅": "План выполнен",
    "❤️": "Тренировка понравилась",
    "": "Без отметки",
}

def plot_progress_figure(scores: Dict):
    labels = list(scores.keys())
    values = list(scores.values())
    values += values[:1]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"])
    ax.grid(alpha=0.35)
    ax.set_title("Физический профиль", pad=20)
    return fig


def render_profile_tab():
    st.header("Профиль")
    profile = st.session_state["profile"]

    col1, col2 = st.columns(2)
    with col1:
        profile["name"] = st.text_input("Имя", profile.get("name", "Пользователь"))
        profile["age"] = st.number_input("Возраст", min_value=5, max_value=100, value=int(profile.get("age", 25)))
        sex_options = ["м", "ж", "не указывать"]
        profile["sex"] = st.selectbox(
            "Пол",
            options=sex_options,
            index=sex_options.index(profile.get("sex", "м")) if profile.get("sex", "м") in sex_options else 0,
        )
        level_options = ["новичок", "средний", "продвинутый"]
        profile["activity_level"] = st.selectbox(
            "Уровень подготовки",
            options=level_options,
            index=level_options.index(profile.get("activity_level", "средний")),
        )
    with col2:
        profile["environment_pref"] = st.multiselect(
            "Где вам удобнее тренироваться",
            options=["дом", "зал", "улица", "бассейн", "корт", "поле"],
            default=profile.get("environment_pref", ["дом"]),
        )
        profile["equipment"] = st.multiselect(
            "Какой инвентарь у вас есть",
            options=["гантели", "скакалка", "коврик", "мяч", "ракетка", "велосипед"],
            default=profile.get("equipment", []),
        )
        profile["weekly_activity"] = st.slider(
            "Сколько раз в неделю вы обычно двигаетесь или тренируетесь",
            min_value=0,
            max_value=7,
            value=int(profile.get("weekly_activity", 3)),
        )

        if profile["age"] <= 17:
            health_options = ["I", "II", "III", "IV", "V"]
        else:
            health_options = ["I", "II", "IIIa", "IIIb"]
        current_health = profile.get("health_group", "I")
        if current_health not in health_options:
            current_health = "I"
        profile["health_group"] = st.selectbox(
            "Группа здоровья",
            options=health_options,
            index=health_options.index(current_health),
        )

    st.success("Профиль сохраняется в текущей сессии автоматически.")

def render_psychology_tab():
    st.header("Тест на выбор спорта")
    answers = []
    for question in PSYCHOLOGY_QUESTIONS:
        answer = st.radio(question["q"], list(question["options"].keys()), key=question["q"])
        answers.append(question["options"][answer])

    top_group, _ = get_top_psych_group(answers)
    st.session_state["profile"]["psych_group"] = top_group

    st.info(f"Ваш психотип: {top_group}")
    st.write(PSYCHOLOGY_GROUPS[top_group]["desc"])
    
    health_group = st.session_state["profile"].get("health_group")
    if health_group == "II":
        st.info(
            "Для II группы здоровья приложение понижает приоритет высокоинтенсивных видов спорта "
            "и чаще поднимает в выдаче щадящие и умеренные варианты."
        )
    elif health_group == "III":
        st.warning(
            "Для III группы здоровья приложение исключает наиболее интенсивные и рискованные виды спорта "
            "из автоматических рекомендаций."
        )
    elif health_group in {"IIIa", "IIIb"}:
        st.warning(
            "Для групп здоровья IIIa и IIIb приложение показывает только щадящие варианты активности. "
            "Это не заменяет допуск врача и индивидуальные медицинские рекомендации."
        )
    recommendations = recommend_sports(st.session_state["profile"], top_group)
    st.subheader("Рекомендованные виды спорта")

    if not recommendations:
        st.warning("Сейчас не удалось подобрать виды спорта под ваш профиль. Попробуйте изменить ограничения в профиле.")
        return

    for index, item in enumerate(recommendations, start=1):
        with st.container(border=True):
            st.markdown(f"**{index}. {item['name']}**")
            st.write(item["description"])
            st.caption(f"Тип: {item['sport_type']} | Совпадение: {item['score']} баллов")
            st.write("Почему рекомендовано:")
            for reason in item["reasons"]:
                st.write(f"- {reason}")
            if item["environment"]:
                st.write(f"Где заниматься: {', '.join(item['environment'])}")
            if item["equipment"]:
                st.write(f"Инвентарь: {', '.join(item['equipment'])}")
            else:
                st.write("Инвентарь: не требуется")


def render_physical_tab():
    st.header("Физический тест")
    profile = st.session_state["profile"]

    col1, col2 = st.columns(2)
    with col1:
        profile["lifestyle"] = st.selectbox(
            "Образ жизни",
            ["малоподвижный", "умеренно активный", "активный"],
            index=["малоподвижный", "умеренно активный", "активный"].index(profile.get("lifestyle", "умеренно активный")),
        )
        profile["push_ups"] = st.number_input("Отжимания подряд", min_value=0, max_value=300, value=int(profile.get("push_ups", 0)))
        profile["squats"] = st.number_input("Приседания за минуту", min_value=0, max_value=300, value=int(profile.get("squats", 0)))
        profile["plank_sec"] = st.number_input("Планка, секунд", min_value=0, max_value=1800, value=int(profile.get("plank_sec", 0)))

    with col2:
        profile["fatigue"] = st.selectbox(
            "Как часто чувствуете усталость после умеренной нагрузки",
            ["никогда", "редко", "иногда", "часто"],
            index=["никогда", "редко", "иногда", "часто"].index(profile.get("fatigue", "иногда")),
        )
        profile["flexibility_reach"] = st.select_slider(
            "Насколько легко дотянуться до пальцев ног",
            options=[1, 2, 3, 4, 5],
            value=int(profile.get("flexibility_reach", 3)),
            format_func=lambda value: {
                1: "Совсем не могу",
                2: "До голени",
                3: "До лодыжек",
                4: "Почти касаюсь",
                5: "Легко касаюсь",
            }[value],
        )
        profile["preferred_session_min"] = st.slider(
            "Комфортная длительность тренировки",
            min_value=15,
            max_value=120,
            value=int(profile.get("preferred_session_min", 30)),
        )
        profile["balance_test"] = st.radio(
            "Можете простоять на одной ноге 10 секунд с закрытыми глазами?",
            ["да", "нет"],
            index=["да", "нет"].index(profile.get("balance_test", "нет")),
        )
        profile["jumps_30s"] = st.number_input("Прыжки на месте за 30 секунд", min_value=0, max_value=150, value=int(profile.get("jumps_30s", 0)))

    if st.button("Сохранить результаты физического теста", type="primary"):
        entry = {
            "date": datetime.now().isoformat(),
            "scores": compute_qualities(profile),
            "repetition_history": {
                "отжимания": profile["push_ups"],
                "приседания": profile["squats"],
                "планка": profile["plank_sec"],
            },
        }
        st.session_state["progress_history"].append(entry)
        save_app_data_to_disk()
        st.success("Результаты сохранены.")

    current_scores = compute_qualities(profile)
    fig = plot_progress_figure(current_scores)
    st.pyplot(fig)

    strongest_quality = max(current_scores, key=current_scores.get)
    weakest_quality = min(current_scores, key=current_scores.get)
    st.caption(
        f"Сильнее всего сейчас выражено качество: {strongest_quality.lower()}. "
        f"Зона для роста: {weakest_quality.lower()}."
    )

    history_list = st.session_state.get("progress_history", [])
    if len(history_list) >= 2:
        previous_scores = history_list[-2]["scores"]
        st.subheader("Сравнение с предыдущим замером")
        for quality_name in QUALITY_ORDER:
            diff = current_scores[quality_name] - previous_scores.get(quality_name, 0)
            prefix = "+" if diff > 0 else ""
            st.write(f"{quality_name}: {prefix}{diff}")

def get_calendar_day_style(day, today, plan: Dict, feedback_entry: Dict, is_selected: bool) -> tuple[str, str, str]:
    border = "1px solid rgba(0,0,0,0.08)"
    if is_selected:
        border = "3px solid #2f6fed"
    if day == today:
        return "#fff3b0", "Сегодня", border
    if feedback_entry.get("emoji") in {"💪", "🔥", "✅", "❤️"}:
        return "#cfeccf", "Тренировка выполнена", border
    if plan.get("type") == "отдых":
        return "#f8d7da", "День отдыха", border
    return "#edf2ff", plan.get("type", "Тренировка").capitalize(), border


def render_calendar_tab():
    st.header("Календарь тренировок")
    year = st.session_state["view_year"]
    month = st.session_state["view_month"]
    today = date.today()
    feedback = load_feedback()

    nav_left, nav_center, nav_right = st.columns([1, 4, 1])
    with nav_left:
        if st.button("← Пред. месяц"):
            month -= 1
            if month < 1:
                month = 12
                year -= 1
            st.session_state["view_year"] = year
            st.session_state["view_month"] = month
            st.session_state["selected_date"] = None
            st.rerun()

    with nav_center:
        st.markdown(f"### {MONTHS_RU_NUM[month]} {year}")

    with nav_right:
        if st.button("След. месяц →"):
            month += 1
            if month > 12:
                month = 1
                year += 1
            st.session_state["view_year"] = year
            st.session_state["view_month"] = month
            st.session_state["selected_date"] = None
            st.rerun()

    rest_days = st.session_state.get("rest_days", [6])
    monthly_plan = generate_monthly_plan(year, month, rest_days, st.session_state["profile"])
    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))

    header_cols = st.columns(7)
    for index, day_name in enumerate(DAYS_OF_WEEK):
        header_cols[index].markdown(f"**{day_name}**")

    legend_cols = st.columns(3)
    legend_cols[0].markdown(
        "<div style='background:#fff3b0;padding:8px;border-radius:8px;text-align:center;'><b>Желтый</b><br>текущий день</div>",
        unsafe_allow_html=True,
    )
    legend_cols[1].markdown(
        "<div style='background:#cfeccf;padding:8px;border-radius:8px;text-align:center;'><b>Зеленый</b><br>выполненная тренировка</div>",
        unsafe_allow_html=True,
    )
    legend_cols[2].markdown(
        "<div style='background:#f8d7da;padding:8px;border-radius:8px;text-align:center;'><b>Красный</b><br>день отдыха</div>",
        unsafe_allow_html=True,
    )

    for week_start in range(0, len(month_days), 7):
        cols = st.columns(7)
        week = month_days[week_start:week_start + 7]

        for index, day in enumerate(week):
            col = cols[index]
            if day.month != month:
                col.empty()
                continue

            iso = day.isoformat()
            plan = monthly_plan.get(iso, {"type": "отдых", "exercises": [], "duration_min": 0})
            fb = feedback.get(iso, {})
            is_selected = st.session_state.get("selected_date") == iso
            background_color, badge, border_style = get_calendar_day_style(
                day, today, plan, fb, is_selected
            )

            with col.container(border=True):
                st.markdown(
                    f"""
                    <div style="
                        background:{background_color};
                        padding:10px;
                        border-radius:10px;
                        border:{border_style};
                        min-height:110px;
                    ">
                        <div style="font-weight:700;font-size:18px;">{day.day}</div>
                        <div style="font-size:12px;color:#444;margin-top:4px;">{badge}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.caption(badge)

                if plan["exercises"]:
                    for exercise in plan["exercises"][:3]:
                        st.write(f"- {exercise}")
                    if len(plan["exercises"]) > 3:
                        st.caption(f"Еще упражнений в плане: {len(plan['exercises']) - 3}")
                else:
                    st.write("Отдых")

                if st.button(f"Открыть {iso}", key=f"open_{iso}"):
                    st.session_state["selected_date"] = iso

                quick_cols = st.columns(4)
                quick_emoji = ["💪", "🔥", "😴", "✅"]
                for emoji_index, emoji in enumerate(quick_emoji):
                    if quick_cols[emoji_index].button(emoji, key=f"emoji_{iso}_{emoji_index}"):
                        feedback[iso] = {
                            **fb,
                            "emoji": emoji,
                            "duration": fb.get("duration", plan["duration_min"]),
                        }
                        save_feedback(feedback)
                        st.session_state["selected_date"] = iso

    with st.sidebar:
        st.header("Настройки календаря")
        selected_rest_days = st.multiselect(
            "Дни отдыха",
            options=list(range(7)),
            format_func=lambda day_index: DAYS_OF_WEEK[day_index],
            default=rest_days,
        )

        if len(selected_rest_days) == 7:
            st.error("Нельзя сделать отдыхом все 7 дней.")
        else:
            st.session_state["rest_days"] = selected_rest_days
            st.session_state["profile"]["rest_days"] = selected_rest_days
            save_app_data_to_disk()

        st.divider()
        st.header("Редактор дня")
        selected_date = st.session_state.get("selected_date")

        if not selected_date:
            st.info("Выберите день в календаре.")
        else:
            selected_feedback = feedback.get(selected_date, {})
            selected_plan = monthly_plan.get(selected_date, {"duration_min": 30, "exercises": []})
            st.markdown(f"### {selected_date}")

            if selected_date == today.isoformat():
                st.info("Это текущий день.")
            elif selected_feedback.get("emoji") in {"💪", "🔥", "✅", "❤️"}:
                st.success("Этот день отмечен как выполненная тренировка.")
            elif selected_plan.get("type") == "отдых":
                st.error("Этот день запланирован как день отдыха.")

            if selected_plan.get("exercises"):
                st.write("План на день:")
                for exercise in selected_plan["exercises"]:
                    st.write(f"- {exercise}")

            new_emoji = st.radio(
                "Эмоция",
                ["", "💪", "🔥", "😴", "✅", "❤️"],
                index=["", "💪", "🔥", "😴", "✅", "❤️"].index(selected_feedback.get("emoji", "")),
            )
            new_comment = st.text_area("Комментарий", value=selected_feedback.get("comment", ""))
            new_duration = st.number_input(
                "Длительность, мин",
                min_value=0,
                max_value=600,
                value=int(selected_feedback.get("duration", selected_plan.get("duration_min", 30))),
            )

            if st.button("Сохранить день"):
                feedback[selected_date] = {
                    "emoji": new_emoji,
                    "comment": new_comment,
                    "duration": int(new_duration),
                }
                save_feedback(feedback)
                st.success("Изменения сохранены.")

def render_statistics_tab():
    st.header("Статистика")
    feedback = load_feedback()
    year = st.session_state["view_year"]
    month = st.session_state["view_month"]
    month_days = list(calendar.Calendar(firstweekday=0).itermonthdates(year, month))
    summary = summarize_feedback_for_month(month_days, feedback, month)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Заполнено дней", f"{len(summary['filled'])} из {len(summary['month_keys'])}")
        st.metric("Средняя длительность", f"{summary['avg_duration']:.1f} мин")
    with col2:
        st.metric("Выполнение месяца", f"{summary['completion_ratio'] * 100:.0f}%")
        st.write(motivation_message(summary["completion_ratio"]))

    st.subheader("Эмоции за месяц")
    if summary["emoji_counter"]:
        readable_rows = []
        for emoji, count in summary["emoji_counter"].items():
            readable_rows.append(
                {
                    "Отметка": emoji,
                    "Расшифровка": EMOJI_LABELS.get(emoji, "Другая реакция"),
                    "Количество": count,
                }
            )
        df_emoji = pd.DataFrame(readable_rows)
        st.dataframe(df_emoji, hide_index=True)
        
        fig, ax = plt.subplots()
        ax.pie(
            df_emoji["Количество"],
            labels=df_emoji["Расшифровка"],
            autopct="%d%%",
        )
        ax.set_title("Распределение состояний по тренировкам")
        st.pyplot(fig)
    else:
        st.info("Пока нет отмеченных тренировочных дней.")

    st.subheader("История физического прогресса")
    history = st.session_state.get("progress_history", [])
    if history:
        history_rows = []
        for entry in history:
            row = {"Дата": entry["date"][:10]}
            row.update(entry["scores"])
            history_rows.append(row)
        history_df = pd.DataFrame(history_rows)
        st.dataframe(history_df, hide_index=True)
    else:
        st.info("Сначала сохраните хотя бы один физический тест.")


def render_data_controls():
    st.markdown("---")
    st.subheader("Управление данными")
    st.info("Данные сохраняются автоматически в локальный JSON-файл. Кнопка ниже нужна только для резервной копии.")

    col1, col2 = st.columns(2)
    with col1:
        json_payload = export_app_data()
        st.download_button(
            label="Скачать мои данные",
            data=json_payload,
            file_name=f"sportadvisor_data_{date.today()}.json",
            mime="application/json",
        )
    with col2:
        uploaded = st.file_uploader("Загрузить мои данные", type=["json"])
        if uploaded is not None:
            try:
                import_app_data(uploaded)
                st.success("Данные загружены. Страница будет обновлена.")
                st.rerun()
            except Exception as exc:
                st.error(f"Не удалось загрузить файл: {exc}")


st.set_page_config(page_title="SportAdvisor", layout="wide")
st.title("SportAdvisor")
st.caption("Подбор спорта, физический профиль и привычка к регулярным тренировкам.")

init_session_state()

tab_profile, tab_psychology, tab_physical, tab_calendar, tab_statistics = st.tabs(
    ["Профиль", "Выбор спорта", "Физический тест", "Календарь", "Статистика"]
)

with tab_profile:
    render_profile_tab()
with tab_psychology:
    render_psychology_tab()
with tab_physical:
    render_physical_tab()
with tab_calendar:
    render_calendar_tab()
with tab_statistics:
    render_statistics_tab()

render_data_controls()

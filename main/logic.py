from __future__ import annotations

import calendar
from collections import Counter

from data import EXERCISES_BY_CATEGORY, PSYCHOLOGY_GROUPS, SPORT_DB


QUALITY_ORDER = ["Сила", "Выносливость", "Ловкость", "Гибкость", "Координация"]


def normalize_health_group(group: str) -> str:
    if not group:
        return "I"
    if group.startswith("III"):
        return "III"
    return group


def compute_qualities(profile: dict) -> dict:
    push_ups = max(0, int(profile.get("push_ups", 0)))
    squats = max(0, int(profile.get("squats", 0)))
    plank_sec = max(0, int(profile.get("plank_sec", 0)))
    jumps_30s = max(0, int(profile.get("jumps_30s", 0)))
    weekly_activity = max(0, int(profile.get("weekly_activity", 0)))
    flexibility_reach = int(profile.get("flexibility_reach", 3))
    fatigue = profile.get("fatigue", "иногда")
    balance_test = profile.get("balance_test", "нет")

    strength = min(10, round(min(4, push_ups / 8) + min(3, squats / 20) + min(3, jumps_30s / 12)))
    fatigue_score = {"никогда": 3, "редко": 2, "иногда": 1, "часто": 0}.get(fatigue, 1)
    endurance = min(10, round(min(5, weekly_activity * 1.2) + min(2, plank_sec / 60) + fatigue_score))
    agility = min(10, round(min(4, jumps_30s / 10) + min(3, plank_sec / 50) + (2 if balance_test == "да" else 0)))
    flexibility = min(10, round(flexibility_reach * 2))
    coordination = min(
        10,
        round(min(4, plank_sec / 45) + min(3, flexibility_reach) + (3 if balance_test == "да" else 0)),
    )

    return {
        "Сила": strength,
        "Выносливость": endurance,
        "Ловкость": agility,
        "Гибкость": flexibility,
        "Координация": coordination,
    }


def get_top_psych_group(answers: list[str]) -> tuple[str, dict]:
    scores = {group_name: 0 for group_name in PSYCHOLOGY_GROUPS}
    for answer_group in answers:
        scores[answer_group] += 1
    top_group = max(scores, key=scores.get)
    return top_group, scores


def score_sport_match(profile: dict, sport_name: str, sport_info: dict, psych_group: str, qualities: dict) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    normalized_health = normalize_health_group(profile.get("health_group", "I"))
    health_ok = normalized_health in sport_info.get("health", [])
    if health_ok:
        score += 25
        reasons.append("подходит по группе здоровья")

    preferred_env = set(profile.get("environment_pref", []))
    sport_env = set(sport_info.get("environment", []))
    env_overlap = preferred_env & sport_env
    if env_overlap:
        score += 20
        reasons.append(f"совпадает по месту тренировок: {', '.join(sorted(env_overlap))}")

    user_equipment = set(profile.get("equipment", []))
    sport_equipment = set(sport_info.get("equipment", []))
    if not sport_equipment:
        score += 10
        reasons.append("не требует специального инвентаря")
    elif sport_equipment <= user_equipment:
        score += 15
        reasons.append("у вас уже есть нужный инвентарь")
    elif user_equipment & sport_equipment:
        score += 7
        reasons.append("часть нужного инвентаря уже есть")

    if psych_group and sport_name in PSYCHOLOGY_GROUPS.get(psych_group, {}).get("sports", []):
        score += 20
        reasons.append(f"поддерживает ваш психотип: {psych_group.lower()}")

    quality_fit = 0
    for quality_name, importance in sport_info.get("qualities", {}).items():
        quality_fit += min(qualities.get(quality_name, 0), importance * 2)
    score += quality_fit
    top_quality = max(sport_info.get("qualities", {}), key=sport_info.get("qualities", {}).get, default=None)
    if top_quality:
        reasons.append(f"совпадает с вашим профилем по качеству '{top_quality.lower()}'")

    return score, reasons


def recommend_sports(profile: dict, psych_group: str, limit: int = 5) -> list[dict]:
    qualities = compute_qualities(profile)
    normalized_health = normalize_health_group(profile.get("health_group", "I"))

    recommendations = []
    for sport_name, sport_info in SPORT_DB.items():
        if normalized_health not in sport_info.get("health", []):
            continue
        score, reasons = score_sport_match(profile, sport_name, sport_info, psych_group, qualities)
        recommendations.append(
            {
                "name": sport_name,
                "score": score,
                "reasons": reasons[:3],
                "description": sport_info.get("description", ""),
                "sport_type": sport_info.get("sport_type", ""),
                "environment": sport_info.get("environment", []),
                "equipment": sport_info.get("equipment", []),
            }
        )

    recommendations.sort(key=lambda item: item["score"], reverse=True)
    return recommendations[:limit]


def generate_monthly_plan(year: int, month: int, rest_days: list[int], profile: dict) -> dict:
    cal = calendar.Calendar(firstweekday=0)
    month_days = [day for day in cal.itermonthdates(year, month) if day.month == month]

    categories = list(EXERCISES_BY_CATEGORY.keys())
    qualities = compute_qualities(profile)
    load_factor = max(1, round(sum(qualities.values()) / len(qualities) / 2))
    preferred_minutes = int(profile.get("preferred_session_min", 30))
    plan = {}
    training_day_index = 0

    for day in month_days:
        if day.weekday() in rest_days:
            plan[day.isoformat()] = {
                "type": "отдых",
                "duration_min": 0,
                "exercises": [],
            }
            continue

        category = categories[training_day_index % len(categories)]
        training_day_index += 1
        base_load = load_factor + max(0, (training_day_index - 1) // 6)
        exercises = []
        for exercise in EXERCISES_BY_CATEGORY[category][:3]:
            if "планка" in exercise or "наклон" in exercise or "поза" in exercise:
                exercises.append(f"{exercise} — {20 + base_load * 10} сек")
            else:
                exercises.append(f"{exercise} — {8 + base_load * 2} повторений")

        plan[day.isoformat()] = {
            "type": category,
            "duration_min": preferred_minutes,
            "exercises": exercises,
        }

    return plan


def summarize_feedback_for_month(month_days: list, feedback: dict, month: int) -> dict:
    month_keys = [day.isoformat() for day in month_days if day.month == month]
    filled = [key for key in month_keys if feedback.get(key) and feedback[key].get("emoji")]
    durations = [
        feedback[key].get("duration", 0)
        for key in month_keys
        if feedback.get(key) and isinstance(feedback[key].get("duration", 0), (int, float))
    ]
    emoji_counter = Counter(feedback[key].get("emoji") for key in month_keys if feedback.get(key) and feedback[key].get("emoji"))
    completion_ratio = len(filled) / len(month_keys) if month_keys else 0

    return {
        "month_keys": month_keys,
        "filled": filled,
        "avg_duration": (sum(durations) / len(durations)) if durations else 0,
        "emoji_counter": emoji_counter,
        "completion_ratio": completion_ratio,
    }


def motivation_message(completion_ratio: float) -> str:
    if completion_ratio == 0:
        return "Начните месяц с первой тренировки и задайте ритм."
    if completion_ratio < 0.25:
        return "Старт уже есть. Дальше важнее регулярность, чем идеальность."
    if completion_ratio < 0.5:
        return "Вы уже набрали хороший темп. Сейчас главное его не терять."
    if completion_ratio < 0.75:
        return "Прогресс заметный. Вы близки к устойчивой спортивной привычке."
    return "Очень сильный месяц. У вас уже формируется стабильная система тренировок."

from __future__ import annotations

import calendar
from collections import Counter
from datetime import date, timedelta
from typing import Dict, List, Optional, Set, Tuple

from data import (
    CONSERVATIVE_SPORTS_FOR_SPECIAL_HEALTH,
    EXERCISES_BY_CATEGORY,
    PSYCHOLOGY_GROUPS,
    SPORT_DB,
)

QUALITY_ORDER = ["Сила", "Выносливость", "Ловкость", "Гибкость", "Координация"]

TRAINING_CATEGORY_SEQUENCE = [
    "руки/спина",
    "ноги",
    "пресс",
    "кардио",
    "комплексная",
    "растяжка",
]


def normalize_health_group(group: str) -> str:
    if not group:
        return "I"
    if group.startswith("III"):
        return "III"
    return group


def is_special_health_group(group: str) -> bool:
    return group in {"IIIa", "IIIb"}


def allowed_risk_levels_for_health_group(group: str) -> Set[str]:
    if group == "I":
        return {"low", "medium", "high"}
    if group == "II":
        return {"low", "medium", "high"}
    if group == "III":
        return {"low", "medium"}
    if group in {"IIIa", "IIIb"}:
        return {"low"}
    return {"low", "medium"}


def health_group_score_adjustment(group: str, risk_level: str) -> Tuple[int, Optional[str]]:
    if group == "I":
        return 0, None
    if group == "II":
        if risk_level == "high":
            return -18, "снижено в рейтинге из-за высокой интенсивности для II группы здоровья"
        if risk_level == "medium":
            return -5, "умеренная нагрузка учтена с осторожностью для II группы здоровья"
        return 6, "щадящая нагрузка хорошо подходит для II группы здоровья"
    if group == "III":
        if risk_level == "medium":
            return -10, "умеренная нагрузка учтена осторожно для III группы здоровья"
        if risk_level == "low":
            return 10, "щадящий формат лучше подходит для III группы здоровья"
    if group in {"IIIa", "IIIb"} and risk_level == "low":
        return 12, "щадящий формат подобран с учетом IIIa/IIIb"
    return 0, None


def compute_qualities(profile: Dict) -> Dict:
    push_ups = max(0, int(profile.get("push_ups", 0)))
    squats = max(0, int(profile.get("squats", 0)))
    plank_sec = max(0, int(profile.get("plank_sec", 0)))
    jumps_30s = max(0, int(profile.get("jumps_30s", 0)))
    weekly_activity = max(0, int(profile.get("weekly_activity", 0)))
    flexibility_reach = int(profile.get("flexibility_reach", 3))
    fatigue = profile.get("fatigue", "иногда")
    balance_test = profile.get("balance_test", "нет")

    strength = min(10, round(min(5, push_ups / 10) + min(3, squats / 25) + min(2, jumps_30s / 15)))
    fatigue_score = {"никогда": 3, "редко": 2, "иногда": 1, "часто": 0}.get(fatigue, 1)
    endurance = min(10, round(min(5, weekly_activity) + min(3, plank_sec / 75) + fatigue_score))
    agility = min(10, round(min(5, jumps_30s / 8) + min(2, squats / 30) + (2 if balance_test == "да" else 0)))
    flexibility = min(10, round(1 + flexibility_reach * 2))
    coordination = min(
        10,
        round(
            min(3, plank_sec / 60)
            + min(3, jumps_30s / 15)
            + min(2, flexibility_reach / 2)
            + (2 if balance_test == "да" else 0)
        ),
    )

    return {
        "Сила": strength,
        "Выносливость": endurance,
        "Ловкость": agility,
        "Гибкость": flexibility,
        "Координация": coordination,
    }


def get_top_psych_group(answers: List[str]) -> Tuple[str, Dict]:
    scores = {group_name: 0 for group_name in PSYCHOLOGY_GROUPS}
    for answer_group in answers:
        scores[answer_group] += 1
    top_group = max(scores, key=scores.get)
    return top_group, scores


def score_sport_match(
    profile: Dict,
    sport_name: str,
    sport_info: Dict,
    psych_group: str,
    qualities: Dict,
) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []

    normalized_health = normalize_health_group(profile.get("health_group", "I"))
    if normalized_health in sport_info.get("health", []):
        score += 25
        reasons.append("подходит по группе здоровья")

    raw_health_group = profile.get("health_group", "I")
    risk_level = sport_info.get("risk_level", "medium")
    risk_adjustment, risk_reason = health_group_score_adjustment(raw_health_group, risk_level)
    score += risk_adjustment
    if risk_reason:
        reasons.append(risk_reason)

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


def recommend_sports(profile: Dict, psych_group: str, limit: int = 5) -> List[Dict]:
    qualities = compute_qualities(profile)
    raw_health_group = profile.get("health_group", "I")
    normalized_health = normalize_health_group(raw_health_group)
    allowed_risk_levels = allowed_risk_levels_for_health_group(raw_health_group)

    recommendations: List[Dict] = []
    for sport_name, sport_info in SPORT_DB.items():
        if normalized_health not in sport_info.get("health", []):
            continue
        if sport_info.get("risk_level", "medium") not in allowed_risk_levels:
            continue
        if is_special_health_group(raw_health_group):
            if sport_name not in CONSERVATIVE_SPORTS_FOR_SPECIAL_HEALTH:
                continue
            if sport_info.get("risk_level") in {"medium", "high"}:
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


def get_training_weekdays(rest_days: List[int]) -> List[int]:
    training_days = [day for day in range(7) if day not in rest_days]
    return training_days or [0, 2, 4]


def get_category_for_day(day: date, training_weekdays: List[int]) -> str:
    year_anchor = date(day.year, 1, 1)
    first_monday = year_anchor - timedelta(days=year_anchor.weekday())
    week_start = day - timedelta(days=day.weekday())
    week_index = max(0, (week_start - first_monday).days // 7)
    day_slot = training_weekdays.index(day.weekday())
    sequence_index = (week_index * len(training_weekdays) + day_slot) % len(TRAINING_CATEGORY_SEQUENCE)
    return TRAINING_CATEGORY_SEQUENCE[sequence_index]


def get_progressive_block(day: date, training_weekdays: List[int]) -> int:
    year_anchor = date(day.year, 1, 1)
    first_monday = year_anchor - timedelta(days=year_anchor.weekday())
    week_start = day - timedelta(days=day.weekday())
    week_index = max(0, (week_start - first_monday).days // 7)
    day_slot = training_weekdays.index(day.weekday())
    training_days_passed = week_index * len(training_weekdays) + day_slot
    return max(0, training_days_passed // 6)


def build_exercise_list_for_category(category: str, profile: Dict, base_load: int) -> List[str]:
    """
    Генерирует список упражнений с прогрессией нагрузки.
    base_load: рассчитывается как load_factor + progressive_block (недели)
    """
    equipment = set(profile.get("equipment", []))
    exercises: List[str] = []
    
    # Базовые показатели пользователя
    push_ups = max(1, int(profile.get("push_ups", 0)))
    squats = max(1, int(profile.get("squats", 0)))
    plank_sec = max(10, int(profile.get("plank_sec", 0)))
    jumps_30s = max(1, int(profile.get("jumps_30s", 0)))
    
    # === НАСТРОЙКА ПРОГРЕССИИ ===
    # Базовый множитель: 1.0 + (неделя * 0.15) = +15% в неделю
    # Максимум +60% за 4 недели, потом плато
    progression_multiplier = 1.0 + min(base_load - 1, 4) * 0.15

    # Базовые значения упражнений (от которых считаем прогрессию)
    base_exercise_values = {
        "отжимания": max(3, round(push_ups * 0.6)),
        "тяга резинки": max(6, round(push_ups * 0.7)),
        "лодочка": max(8, round(plank_sec / 6)),
        "планка с касанием плеч": max(10, round(plank_sec / 5)),
        "приседания": max(6, round(squats * 0.7)),
        "выпады": max(6, round(squats * 0.35)),
        "ягодичный мост": max(8, round(squats * 0.5)),
        "подъемы на носки": max(12, round(squats * 0.8)),
        "планка": max(15, round(plank_sec * 0.6)),
        "скручивания": max(8, round(squats * 0.45)),
        "велосипед": max(10, round(jumps_30s * 0.6)),
        "подъем ног": max(6, round(plank_sec / 8)),
        "наклон к полу": max(20, round(plank_sec * 0.5)),
        "бабочка": max(20, round(plank_sec * 0.5)),
        "кошка-корова": max(20, round(plank_sec * 0.45)),
        "поза ребенка": max(25, round(plank_sec * 0.55)),
        "бег на месте": max(20, round(jumps_30s * 1.1)),
        "берпи": max(4, round(push_ups * 0.35)),
        "прыжки": max(10, round(jumps_30s * 0.8)),
        "шаги в планке": max(8, round(push_ups * 0.5)),
    }

    for exercise in EXERCISES_BY_CATEGORY[category]:
        # Комплексные упражнения (круговые)
        if exercise in {"круг: приседания + отжимания + планка", "выпады + прыжки + пресс"}:
            if exercise == "круг: приседания + отжимания + планка":
                circuit_value = max(
                    1,
                    round(
                        (
                            base_exercise_values["приседания"]
                            + base_exercise_values["отжимания"]
                            + max(10, round(base_exercise_values["планка"] / 3))
                        )
                        / 3
                    ),
                )
            else:
                circuit_value = max(
                    1,
                    round(
                        (
                            base_exercise_values["выпады"]
                            + base_exercise_values["прыжки"]
                            + base_exercise_values["скручивания"]
                        )
                        / 3
                    ),
                )
            exercises.append(f"{exercise} — {circuit_value} повторений на круг")
        
        # Упражнения на время (секунды)
        elif "планка" in exercise or "наклон" in exercise or "поза" in exercise or exercise in {"бабочка", "кошка-корова"}:
            duration_value = base_exercise_values.get(exercise, max(20, round(plank_sec * 0.5)))
            # Прогрессия для времени: +10 сек в неделю
            progressed_duration = min(180, round(duration_value * progression_multiplier))  # макс. 3 минуты
            exercises.append(f"{exercise} — {progressed_duration} сек")
        
        # Упражнения на повторения
        else:
            rep_value = base_exercise_values.get(exercise, max(6, round((push_ups + squats) / 4)))
            # Прогрессия для повторений: +2-3 повтора в неделю
            progressed_reps = min(50, round(rep_value * progression_multiplier))  # макс. 50 повторов
            exercises.append(f"{exercise} — {progressed_reps} повторений")

    # Бонусные упражнения при наличии инвентаря
    if category == "руки/спина" and "гантели" in equipment:
        dumbbell_value = max(6, round(push_ups * 0.6))
        progressed = min(40, round(dumbbell_value * progression_multiplier))
        exercises.append(f"жим гантелей — {progressed} повторений")
    
    if category == "кардио" and "скакалка" in equipment:
        rope_value = max(20, round(jumps_30s * 1.0))
        progressed = min(120, round(rope_value * progression_multiplier))  # макс. 2 минуты
        exercises.append(f"прыжки со скакалкой — {progressed} сек")
    
    if category in {"пресс", "растяжка"} and "коврик" in equipment:
        exercises.append("упражнения на коврике — комфортный темп")

    return exercises
    
def generate_monthly_plan(year: int, month: int, rest_days: List[int], profile: Dict) -> Dict:
    cal = calendar.Calendar(firstweekday=0)
    month_days = [day for day in cal.itermonthdates(year, month) if day.month == month]

    qualities = compute_qualities(profile)
    load_factor = max(1, round(sum(qualities.values()) / len(qualities) / 2))
    preferred_minutes = int(profile.get("preferred_session_min", 30))
    training_weekdays = get_training_weekdays(rest_days)

    plan: Dict = {}
    for day in month_days:
        if day.weekday() in rest_days:
            plan[day.isoformat()] = {
                "type": "отдых",
                "duration_min": 0,
                "exercises": [],
            }
            continue

        category = get_category_for_day(day, training_weekdays)
        progressive_block = get_progressive_block(day, training_weekdays)
        base_load = load_factor + progressive_block
        exercises = build_exercise_list_for_category(category, profile, base_load)

        warmup = [
            "разминка суставов — 5 мин",
            "легкая кардио-разминка — 3 мин",
        ]
        cooldown = [
            "спокойное дыхание — 2 мин",
            "заминка и растяжка — 5 мин",
        ]

        plan[day.isoformat()] = {
            "type": category,
            "duration_min": max(preferred_minutes, 25),
            "exercises": warmup + exercises + cooldown,
        }

    return plan


def summarize_feedback_for_month(month_days: List, feedback: Dict, month: int) -> Dict:
    month_keys = [day.isoformat() for day in month_days if day.month == month]
    filled = [key for key in month_keys if feedback.get(key) and feedback[key].get("emoji")]
    durations = [
        feedback[key].get("duration", 0)
        for key in month_keys
        if feedback.get(key) and isinstance(feedback[key].get("duration", 0), (int, float))
    ]
    emoji_counter = Counter(
        feedback[key].get("emoji")
        for key in month_keys
        if feedback.get(key) and feedback[key].get("emoji")
    )
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

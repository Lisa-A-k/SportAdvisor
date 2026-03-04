import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
import os
from datetime import date, datetime
import pandas as pd
from collections import Counter
import calendar

# КОНСТАНТЫ
DAYS_OF_WEEK = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
MONTHS_RU_NUM = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

# ФУНКЦИИ РАБОТЫ С ФАЙЛАМИ
def load_profile():
    # Берем из session_state или возвращаем пустые данные
    return {
        "profile": st.session_state.get('profile', {}),
        "repetition_history": st.session_state.get('repetition_history', {})
    }

def save_profile(profile_data, rep_history):
    # Сохраняем в session_state
    st.session_state['profile'] = profile_data
    st.session_state['repetition_history'] = rep_history
    return True

def load_json(path, default):
    # На Streamlit Cloud просто возвращаем данные из памяти или default
    if 'saved_data' in st.session_state:
        return st.session_state['saved_data']
    return default

def save_json(path, obj_to_save):
    # На Streamlit Cloud сохраняем только в памяти
    st.session_state['saved_data'] = obj_to_save
    return True
    
def load_feedback():
    return st.session_state.get('feedback_list', {})

def save_feedback(feedback):
    st.session_state['feedback_list'] = feedback
    return True

#  ЗАГРУЗКА ДАННЫХ
data = load_profile()
profile = data.get("profile", {})
repetition_history = data.get("repetition_history", {})

#  ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ СЕССИИ
if "profile" not in st.session_state:
    default_profile_values = {
        "name": "Пользователь",
        "age": 25,
        "sex": "м",
        "activity_level": "средний",
        "environment_pref": ["дом"],
        "constraints": [],
        "equipment": [],
        "health_group": "I",
        "push-ups": 0,
        "squats": 0,
        "plank_sec": 0,
        "weekly_activity": 0,
        "preferred_session_min": 30,
        "lifestyle": "умеренно активный",
        "fatigue": "иногда",
        "flexibility_reach": "нет",
        "psych_group": "",
        "rest_days": [6],
    }
    # Обновляем загруженный профиль значениями по умолчанию, если ключи отсутствуют
    for key, default_value in default_profile_values.items():
        profile.setdefault(key, default_value)
        st.session_state['profile'] = profile
        if "repetition_history" not in st.session_state:
            st.session_state['repetition_history'] = repetition_history
    if "rest_days" not in st.session_state:
     st.session_state['rest_days'] = st.session_state['profile'].get('rest_days', [6])

    # Остальная инициализация session_state...
    if "view_year" not in st.session_state:
        st.session_state.view_year = date.today().year
    if "view_month" not in st.session_state:
        st.session_state.view_month = date.today().month
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None

SPORT_DB = {
    "Бег": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["улица"],"description":"Кардио на свежем воздухе, улучшает выносливость."},
    "Плавание": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["бассейн","открытая вода"],"description":"Низкоударная нагрузка, укрепляет сердце и лёгкие."},
    "Велоспорт": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["улица","зал"],"description":"Аэробная нагрузка на велосипедах."},
    "Триатлон": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["улица","бассейн"],"description":"Плавание, вело и бег, комплексная нагрузка."},
    "Ходьба": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["улица"],"description":"Низкоударная активность, подходит всем."},
    "Йога": {"sport_type":"На развитие координации и гибкости","health":["I","II","III"], "equipment":["коврик"],"environment":["дом","зал"],"description":"Развивает гибкость и расслабление."},
    "Пилатес": {"sport_type":"На развитие координации и гибкости","health":["I","II","III"], "equipment":["коврик"],"environment":["дом","зал"],"description":"Укрепление корпуса и растяжка."},
    "Кроссфит": {"sport_type":"Силовая","health":["I","II","III"], "equipment":["гантели","скакалка"],"environment":["зал"],"description":"Функциональные высокоинтенсивные тренировки."},
    "Силовой тренинг": {"sport_type":"Силовая","health":["I","II","III"], "equipment":["гантели"],"environment":["зал","дом"],"description":"Тренировка силы и мышц с сопротивлением."},
    "Тяжёлая атлетика": {"sport_type":"Силовая","health":["I","II","III"], "equipment":[],"environment":["зал"],"description":"Поднятие тяжестей, развитие силы и мощности."},
    "Бокс": {"sport_type":"Боевой","health":["I","II","III"], "equipment":[],"environment":["зал"],"description":"Боевой контакт, улучшает силу и выносливость."},
    "Кикбоксинг": {"sport_type":"Боевой","health":["I","II","III"], "equipment":[],"environment":["зал"],"description":"Удары ногами и руками, выносливость и сила."},
    "Дзюдо": {"sport_type":"Боевой","health":["I","II","III"], "equipment":[],"environment":["зал"],"description":"Борьба, техника и координация."},
    "Тхэквондо": {"sport_type":"Боевой","health":["I","II","III"], "equipment":[],"environment":["зал"],"description":"Боевые искусства, ловкость и скорость."},
    "Горные лыжи": {"sport_type":"Экстримальный","health":["I","II","III"], "equipment":[],"environment":["горы"],"description":"Спуск с гор с контролируемым риском."},
    "Сноуборд": {"sport_type":"Экстримальный","health":["I","II","III"], "equipment":[],"environment":["горы"],"description":"Экстремальные зимние спуски на сноуборде."},
    "Лыжные гонки": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["горы"],"description":"Длительное аэробное упражнение на лыжах."},
    "Футбол": {"sport_type":"Командный","health":["I","II","III"], "equipment":[],"environment":["поле"],"description":"Командный вид спорта на открытом поле."},
    "Баскетбол": {"sport_type":"Командный","health":["I","II","III"], "equipment":["мяч"],"environment":["зал","улица"],"description":"Командный спорт, прыжки и координация."},
    "Волейбол": {"sport_type":"Командный","health":["I","II","III"], "equipment":["мяч"],"environment":["зал","пляж"],"description":"Командная игра, координация и реакция."},
    "Теннис": {"sport_type":"Индивидуальный","health":["I","II","III"], "equipment":[],"environment":["корт"],"description":"Ракеточный вид спорта, координация рук и глаз."},
    "Бадминтон": {"sport_type":"Индивидуальный","health":["I","II","III"], "equipment":[],"environment":["зал"],"description":"Лёгкий ракеточный спорт, ловкость и реакция."},
    "Настольный теннис": {"sport_type":"Индивидуальный","health":["I","II","III"], "equipment":[],"environment":["зал"],"description":"Развивает реакцию и координацию."},
    "Гребля": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["вода"],"description":"Сила верхнего корпуса и выносливость."},
    "Каякинг": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["вода"],"description":"Гребля на воде, координация и сила."},
    "Гольф": {"sport_type":"На развитие координации и гибкости","health":["I","II","III"], "equipment":[],"environment":["поле"],"description":"Низкоинтенсивный спорт, точность и концентрация."},
    "Скейтбординг": {"sport_type":"Экстримальный","health":["I","II"], "equipment":[],"environment":["улица"],"description":"Экстремальный спорт, баланс и ловкость."},
    "Сёрфинг": {"sport_type":"Экстримальный","health":["I","II","III"], "equipment":[],"environment":["море"],"description":"Баланс и выносливость на воде."},
    "SUP": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["вода"],"description":"Баланс и стабильность корпуса на воде."},
    "Скалолазание": {"sport_type":"Экстримальный","health":["I","II","III"], "equipment":[],"environment":["стена","скалы"],"description":"Сила хвата, ловкость и стратегия."},
    "Пляжный волейбол": {"sport_type":"Командный","health":["I","II","III"], "equipment":["мяч"],"environment":["пляж"],"description":"Пляжная командная игра, прыгучесть и координация."},
    "Регби": {"sport_type":"Командный","health":["I","II","III"], "equipment":[],"environment":["поле"],"description":"Контактный командный спорт, сила и выносливость."},
    "Спортивная ходьба": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["улица"],"description":"Соревновательная ходьба, выносливость."},
    "Спринт": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["трасса"],"description":"Короткие интенсивные забеги, скорость и мощность."},
    "Марафон": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["улица"],"description":"Длительные пробежки, выносливость."},
    "Фехтование": {"sport_type":"Боевой","health":["I","II","III"], "equipment":[],"environment":["зал"],"description":"Реакция, стратегия и координация."},
    "Биатлон": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":[],"environment":["трасса","стрельбище"],"description":"Лыжные гонки с стрельбой, выносливость и концентрация."},
    "Акробатика": {"sport_type":"На развитие координации и гибкости","health":["I","II","III"], "equipment":["коврик"],"environment":["зал"],"description":"Сила, гибкость и баланс."},
    "Танцы": {"sport_type":"На развитие координации и гибкости","health":["I","II","III"], "equipment":["коврик"],"environment":["зал"],"description":"Координация, пластика, ритм."},
    "Пейнтбол": {"sport_type":"Командный","health":["I","II","III"], "equipment":[],"environment":["улица"],"description":"Командная стратегия и тактика."},
    "Скакалка": {"sport_type":"На развитие выносливости","health":["I","II","III"], "equipment":["скакалка"],"environment":["зал","улица"],"description":"Кардио и координация."},
    "Гантели": {"sport_type":"Силовая","health":["I","II","III"], "equipment":["гантели"],"environment":["дом","зал"],"description":"Силовые упражнения с гантелями."},
    "Воркаут": {"sport_type":"Силовая","health":["I","II","III"], "equipment":["Воркаут"],"environment":["улица","дом"],"description":"Силовые упражнения с весом собственного тела."}
}

# Функции для визуализации
def compute_qualities(personal_profile):
    # Сила
    strength_pushups = min(5, personal_profile.get('push-ups', 0) / 5)
    strength_squats = min(3, personal_profile.get('squats', 0) / 10)
    strength_jumps = min(2, personal_profile.get('jumps_30s', 0) / 15)
    strength = min(10, round(strength_pushups + strength_squats + strength_jumps))

    #Выносливость
    fatigue_score = {"никогда": 3, "редко": 2, "иногда": 1, "часто": 0}.get(personal_profile.get('fatigue','иногда'), 1)
    endurance_activity = min(5, personal_profile.get('weekly_activity', 0) * 0.7)  # 7 раз в неделю = ~5 баллов
    endurance_plank = min(2, personal_profile.get('plank_sec', 0) / 60)  # 120 сек = 4 балла
    endurance = min(10, round(endurance_activity + fatigue_score + endurance_plank))

    #Ловкость
    agility_from_plank = personal_profile.get('plank_sec', 0) / 40
    agility_from_balance = 2 if personal_profile.get('balance_test') == 'да' else 0  # Баланс даёт бонус
    agility_from_flexibility = (personal_profile.get('flexibility_reach', 3) - 1) * 0.25 # 1->0, 5->2 балла
    agility = min(10, round(agility_from_plank + agility_from_flexibility + agility_from_balance))

    #Гибкость
    flexibility_quality = min(10, round(personal_profile.get('flexibility_reach', 3) * 2))

    #Координация
    core_plank = min(6, personal_profile.get('plank_sec', 0) / 25)  # 150 сек = 6 баллов
    core_balance = 4 if personal_profile.get('balance_test') == 'да' else 0  # Баланс даёт бонус
    core = min(10, round(core_plank + core_balance))

    return {
        "Сила": strength,
        "Выносливость": endurance,
        "Ловкость": agility,
        "Гибкость": flexibility_quality,
        "Координация": core
    }

def plot_progress_figure(scores):
    quality_names = list(scores.keys())
    values = list(scores.values())
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(quality_names), endpoint=False)
    angles = np.concatenate((angles, [angles[0]]))
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([q.capitalize() for q in quality_names])
    ax.set_yticklabels([])
    ax.set_theta_offset(np.pi / 2) #Поворот
    ax.set_theta_direction(-1) #Направление
    ax.set_title("Физический профиль", fontsize=14, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

    plt.tight_layout()
    return fig

# ФУНКЦИИ КАЛЕНДАРЯ
def go_prev_month():
    y = st.session_state.view_year
    m = st.session_state.view_month - 1
    if m < 1:
        m = 12
        y -= 1
    st.session_state.view_year = y
    st.session_state.view_month = m
    st.session_state.selected_date = None

def go_next_month():
    y = st.session_state.view_year
    m = st.session_state.view_month + 1
    if m > 12:
        m = 1
        y += 1
    st.session_state.view_year = y
    st.session_state.view_month = m
    st.session_state.selected_date = None

# БАЗА УПРАЖНЕНИЙ
EXERCISES_BY_CATEGORY = {
    "руки/спина": ["подтягивания", "отжимания", "супермен","планка с разворотом"],
    "ноги": ["приседания", "выпады", "ягодичный мостик", "подъёмы на носки", "велосипед"],
    "пресс": ["планка", "скручивания", "русские скручивания", "подъём ног в висе"],
    "растяжка": ["бабочка", "собака, мордой в пол", "кошка-корова", "наклон к полу", "подтягивание колена к груди"],
    "кардио": ["бёрпи", "прыжки через скакалку", "бег на месте", "прыжки накрест", "шаги в планке"],
    "комплексная": ["комплекс из приседаний, отжиманий и планки", "тяга + выпад + пресс", "бёрпи + планка + скручивания"]
}

def generate_monthly_plan(year, month, rest_days, user_progress):
    cal = calendar.Calendar(firstweekday=0)
    month_days_all = list(cal.itermonthdates(year, month))
    month_days_filtered = [d for d in month_days_all if d.month == month]
    
    if not month_days_filtered:
        return {}
        
    first_day_of_month_index = month_days_all.index(month_days_filtered[0])
    categories = ["руки/спина", "ноги", "пресс", "растяжка", "кардио", "комплексная"]
    plan = {}
    cat_day_counter = 0
    for day in month_days_filtered:
        weekday = day.weekday()
        if weekday in rest_days:
            plan[day.isoformat()] = {"тип": "отдых", "упражнения": []}
        else:
            category = categories[cat_day_counter % len(categories)]
            cat_day_counter += 1
            
            exercises = EXERCISES_BY_CATEGORY.get(category, ["активность"])
            exercises_with_load = []
            
            current_day_index_in_all = month_days_all.index(day)
            weeks_passed = (current_day_index_in_all - first_day_of_month_index) // 7
            
            for ex in exercises:
                base = user_progress.get(ex, 10)
                load = int(base + weeks_passed * 2)
                
                time_exercises = ["планка", "бабочка", "собака, мордой в пол", 
                                  "кошка-корова", "наклон к полу", "подтягивание колена к груди"]
                
                if any(t in ex for t in time_exercises):
                    exercises_with_load.append(f"{ex} — {load} сек")
                else:
                    exercises_with_load.append(f"{ex} — {load} раз")
            
            plan[day.isoformat()] = {"тип": category, "упражнения": exercises_with_load}
    return plan
    
# КОНФИГУРАЦИЯ СТРАНИЦЫ
st.set_page_config(page_title="SportAdvisor", layout="wide")
st.title("🏋️ SportAdvisor")

# ВКЛАДКИ
tab_profile, tab_psych, tab_phys, tab_calendar, tab_statistics = st.tabs(["Профиль", "Тест на выбор спорта", "Физический тест", "Календарь", "Статистика"])

# ВКЛАДКА: ПРОФИЛЬ
with tab_profile:
    st.header("Профиль")
    st.session_state['profile']['name'] = st.text_input("Имя", st.session_state['profile'].get('name','Пользователь'))
    st.session_state['profile']['age'] = st.number_input("Возраст", min_value=5, max_value=100, value=st.session_state['profile'].get('age',25))
    st.session_state['profile']['sex'] = st.selectbox("Пол", options=["м","ж","не выбирать"], index=0 if st.session_state['profile'].get('sex','м')=='м' else 1)
    st.session_state['profile']['activity_level'] = st.selectbox("Уровень подготовки", options=["новичок","средний","продвинутый"], index=["новичок","средний","продвинутый"].index(st.session_state['profile'].get('activity_level','средний')))
    st.session_state['profile']['environment_pref'] = st.multiselect("Предпочитаемое место тренировок", options=["дом","зал","улица","бассейн"], default=st.session_state['profile'].get('environment_pref',["дом"]))
    st.session_state['profile']['equipment'] = st.multiselect("Инвентарь", options=["гантели","скакалка","коврик","мяч","Воркаут"], default=st.session_state['profile'].get('equipment',[]))
    if st.session_state['profile']['age'] <= 17:
        st.session_state['profile']['health_group'] = st.selectbox("Группа здоровья (дети I–V)", options=["I","II","III","IV","V"], index=["I","II","III","IV","V"].index(st.session_state['profile'].get('health_group','I')))
    else:
        st.session_state['profile']['health_group'] = st.selectbox("Группа здоровья (взрослые)", options=["I","II","IIIa","IIIb"], index=["I","II","IIIa","IIIb"].index(st.session_state['profile'].get('health_group','I')))
    if st.button("Сохранить профиль"):
        save_json(PROFILE_FILE, st.session_state['profile'])
        st.success("Профиль сохранён локально")

# Тест на выбор спорта
with tab_psych:
    st.header("🧠 Тест на выбор спорта")

    # Словарь групп и видов спорта
    groups = {
        "Командный": {"desc": "Тебе важно взаимодействие, общение и дух соревнования.", "sports": ["Футбол", "Баскетбол", "Волейбол", "Регби", "Пейнтбол"]},
        "Индивидуальный": {"desc": "Ты независим, сам себе соперник и любишь самоконтроль.", "sports": ["Теннис", "Бадминтон", "Плавание", "Бег", "Сквош"]},
        "Боевой": {"desc": "Ты энергичный, решительный и не боишься соперничества.", "sports": ["Бокс", "Кикбоксинг", "Дзюдо", "Тхэквондо", "Борьба"]},
        "На развитие координации и гибкости": {"desc": "Ты стремишься к гармонии тела и разума, спокойствию и пластике.", "sports": ["Йога", "Пилатес", "Танцы", "Акробатика"]},
        "Экстримальный": {"desc": "Тебе нужна свобода, драйв и яркие ощущения.", "sports": ["Скалолазание", "Сноуборд", "Сёрфинг"]},
        "На развитие выносливости": {"desc": "Ты спокоен, терпелив и готов к длительным нагрузкам.", "sports": ["Триатлон", "Бег", "Ходьба", "Велоспорт", "Плавание"]},
        "На развитие силы": {"desc": "Ты стремишься к физической мощи и уверенности в теле.", "sports": ["Силовой тренинг", "Кроссфит", "Тяжёлая атлетика"]},
    }

    # Вопросы теста
    questions = [
        {"q": "Как вы реагируете на стрессовые ситуации?", "options": {"Активно действую, нужно выплеснуть энергию": "Боевой", "Предпочитаю успокоиться, сосредоточиться": "На развитие координации и гибкости", "Ищу поддержку, не люблю быть один": "Командный", "Отвлекаюсь на спокойные занятия": "На развитие выносливости",}},
        {"q": "Что для вас важнее в спорте?", "options": {"Победа и результат": "Боевой", "Процесс и удовольствие": "На развитие координации и гибкости", "Общение и командный дух": "Командный", "Гармония тела и разума": "На развитие координации и гибкости",}},
        {"q": "Как вы предпочитаете проводить свободное время?", "options": {"На природе или в движении": "На развитие выносливости", "С друзьями, в компании": "Командный", "Наедине с собой": "Индивидуальный", "Занимаясь чем-то творческим": "На развитие координации и гибкости"}},
        {"q": "Какой у вас уровень энергии в течение дня?", "options": {"Очень высокий, трудно усидеть на месте": "Экстримальный", "Средний, завишу от настроения": "Индивидуальный", "Низкий, предпочитаю спокойные занятия": "На развитие координации и гибкости"}},
        {"q": "Что вас больше мотивирует к занятиям?", "options": {"Соревнование, дух борьбы": "Боевой", "Улучшение здоровья и формы": "На развитие выносливости", "Саморазвитие, осознанность": "На развитие координации и гибкости", "Общение и поддержка других": "Командный",}},
        {"q": "Как вы относитесь к риску и адреналину?", "options": {"Люблю острые ощущения": "Экстримальный", "Иногда — если контролируемо": "Боевой", "Избегаю рисков, предпочитаю безопасность": "На развитие выносливости",}},
        {"q": "Вам комфортнее тренироваться:", "options": {"По чёткому плану, с графиком": "На развитие выносливости", "Когда есть свобода выбора": "Индивидуальный", "Когда рядом есть тренер или команда": "Командный", "Когда никто не мешает, в одиночку": "Индивидуальный",}},
        {"q": "Что вам больше всего нужно от спорта?", "options": {"Выплеснуть эмоции, снять стресс": "Боевой", "Почувствовать уверенность и силу": "На развитие силы", "Обрести спокойствие": "На развитие координации и гибкости", "Почувствовать единство с другими": "Командный",}},
    ]

    # Подсчёт результатов
    scores = {g: 0 for g in groups.keys()}
    for q in questions:
        answer = st.radio(q["q"], list(q["options"].keys()), key=q["q"])
        selected_group = q["options"][answer]
        scores[selected_group] += 1

    top_group = max(scores, key=scores.get)

    # Использование и отображение группы здоровья из профиля
    health_group = st.session_state['profile'].get("health_group", "I")
    st.info(f"**Ваша группа здоровья (из профиля): {health_group}**") # <-- Показываем группу

    st.subheader("🏁 Ваш спортивный профиль:")
    st.markdown(f"{top_group} — {groups[top_group]['desc']}")

    # Фильтрация видов спорта по группе здоровья
    recommended = []
    for sport in groups[top_group]["sports"]:
        sport_info = SPORT_DB.get(sport)
        if sport_info and health_group in sport_info.get("health", []):
            recommended.append(sport)

    st.subheader("🎯 Виды спорта, которые вам подойдут (с учётом группы здоровья):")
    if recommended:
        st.write(", ".join(recommended))
    else:
        st.warning(f"К сожалению, виды спорта из группы '{top_group}' не подходят вашей группе здоровья ({health_group}).")
        # Показать альтернативы
        alternative = [s for s, info in SPORT_DB.items() if health_group in info.get("health", [])]
        if alternative:
            st.info("💡 Однако вам подойдут следующие виды спорта, безопасные для вашей группы здоровья:\n" + ", ".join(alternative[:12]))
        else:
            st.error("⚠️ Не найдено видов спорта, безопасных для вашей группы здоровья.")

    # Сохранение результатов теста
    st.session_state['profile']["psych_group"] = top_group
    save_json(PROFILE_FILE, {"profile": st.session_state['profile'], "repetition_history": st.session_state['repetition_history']})
    st.success("Результат теста сохранён в ваш профиль.")

# ФИЗИЧЕСКИЙ ТЕСТ
with tab_phys:
    st.header("Физический тест")
    col1, col2 = st.columns(2)
    with col1:
        lifestyle = st.selectbox("Образ жизни", ["малоподвижный","умеренно активный","активный"])
        pushups = st.number_input("Отжимания подряд (сколько можете сделать)", min_value=0, max_value=500, value=st.session_state['profile'].get('push-ups',0))
        squats = st.number_input("Приседания за 1 минуту", min_value=0, max_value=500, value=st.session_state['profile'].get('squats',0))
        plank_sec = st.number_input("Планка (секунды)", min_value=0, max_value=2000, value=st.session_state['profile'].get('plank_sec',0))
    with col2:
        fatigue = st.selectbox("Как часто чувствуете усталость после умеренной нагрузки?", ["никогда","редко","иногда","часто"])
        flexibility_reach = st.select_slider("Оцените, насколько вы можете дотянуться до пальцев ног (не сгибая коленей):",options=[1, 2, 3, 4, 5],value=st.session_state['profile'].get('flexibility_reach', 3),format_func=lambda x: {1: "Совсем не могу", 2: "Дотягиваюсь до голени", 3: "Дотягиваюсь до лодыжек", 4: "Немного касаюсь", 5: "Легко дотягиваюсь до пальцев"}[x])
        preferred_session_min = st.slider("Удобная длительность тренировки (мин)", 15, 120, st.session_state['profile'].get('preferred_session_min',30))
        st.markdown("**Сможете ли вы постоять на одной ноге с закрытыми глазами 10 секунд?**")
        balance_test = st.radio("Баланс", ["да", "нет"],index=["да", "нет"].index(st.session_state['profile'].get('balance_test', 'нет')))
        st.markdown("**Сколько раз вы можете подпрыгнуть на месте за 30 секунд?**")
        jumps_30s = st.number_input("Прыжки за 30 секунд",min_value=0, max_value=100,value=st.session_state['profile'].get('jumps_30s', 0))

    if st.button("Сохранить результаты теста и обновить профиль", key="save_and_calc_button"):
        st.session_state['profile'].update({
            "lifestyle": lifestyle,
            "push-ups": int(pushups),
            "squats": int(squats),
            "plank_sec": int(plank_sec),
            "fatigue": fatigue,
            "flexibility": flexibility_reach,
            "preferred_session_min": int(preferred_session_min),
            "balance_test": balance_test,
            "jumps_30s": int(jumps_30s)
        })
    new_entry = {
        "date": datetime.now().isoformat(),
        "scores": compute_qualities(st.session_state['profile']),
        "repetition_history": {
            "отжимания": st.session_state['profile']['push-ups'],
            "приседания": st.session_state['profile']['squats'],
            "планка": st.session_state['profile']['plank_sec']
        }
    }
    
    if 'progress_history' not in st.session_state:
        st.session_state['progress_history'] = []
        
    st.session_state['progress_history'].append(new_entry)

    save_json(PROFILE_FILE, st.session_state['profile'])
    st.success("Результаты сохранены! История обновлена.")
    st.rerun() 

    current_scores = compute_qualities(st.session_state['profile'])
    current_reps = {
        "отжимания": st.session_state['profile']['push-ups'],
        "приседания": st.session_state['profile']['squats'],
        "планка": st.session_state['profile']['plank_sec']
    }

    history_list = st.session_state.get('progress_history', [])
    fig = plot_progress_figure(current_scores)
    st.pyplot(fig)
    
    if len(history_list) >= 2:
        prev_entry = history_list[-2]
        prev_scores = prev_entry["scores"]
        diffs = {k: current_scores[k] - prev_scores.get(k, 0) for k in current_scores.keys()}
        st.markdown("### Сравнение с предыдущим замером:")
        for k, v in diffs.items():
            emoji = "🟢" if v > 0 else ("🔴" if v < 0 else "⚪")
            st.write(f"{emoji} {k}: {'+' if v > 0 else ''}{v}")
    else:
        st.info("Нет предыдущих замеров для сравнения — пройдите тест позже для отслеживания прогресса.")

# КАЛЕНДАРЬ
with tab_calendar:
    st.header("📅 Календарь тренировок")
    col_nav = st.columns([1,6,1])
    with col_nav[0]:
        if st.button("← Пред. месяц"):
            go_prev_month()
    with col_nav[1]:
        month_name_ru = MONTHS_RU_NUM[st.session_state.view_month]
        st.markdown(f"### {month_name_ru} {st.session_state.view_year}")
    with col_nav[2]:
        if st.button("След. месяц →"):
            go_next_month()
    # Выбор дней отдыха
    # Используем боковую панель
    with st.sidebar:
        st.header("Настройки календаря")

        # Виджет multiselect для выбора дней отдыха
        selected_rest_days_names = st.multiselect(
            "Выберите дни отдыха",
            options=list(range(7)),
            format_func=lambda x: DAYS_OF_WEEK[x],
            default=st.session_state['rest_days'],
            key='rest_days_selector'
        )

        # Проверяем ограничения
        if len(selected_rest_days_names) == 7:
            st.error("Нельзя выбрать все 7 дней")
            # Возвращаем предыдущее значение
            selected_rest_days_names = st.session_state['rest_days']
        else:
            if set(selected_rest_days_names) != set(st.session_state['rest_days']):
                st.session_state['rest_days'] = selected_rest_days_names
                st.session_state['profile']['rest_days'] = selected_rest_days_names
                save_json(PROFILE_FILE, st.session_state['profile'])
                st.rerun()
            st.session_state['rest_days'] = selected_rest_days_names
            if len(selected_rest_days_names) == 0:
                st.warning("Не выбрано дней отдыха.")

    year = st.session_state.view_year
    month = st.session_state.view_month
    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))

    feedback = load_feedback()
    REST_DAYS = st.session_state['rest_days']
    USER_PROGRESS = { # Пример прогресса
        "подтягивания": st.session_state['profile'].get('push-ups', 0),
        "отжимания": st.session_state['profile'].get('push-ups', 0),
        "приседания": st.session_state['profile'].get('squats', 0),
        "планка": st.session_state['profile'].get('plank_sec', 0),
        "выпады": 15,
        "скручивания": 20
    }
    monthly_plan = generate_monthly_plan(year, month, REST_DAYS, USER_PROGRESS)

    weekdays = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
    cols = st.columns(7)
    for i, c in enumerate(cols):
        c.markdown(f"**{weekdays[i]}**")

    today = date.today()
    for week_start in range(0, len(month_days), 7):
        week = month_days[week_start:week_start+7]
        cols = st.columns(7)
        for i, d in enumerate(week):
            col = cols[i]
            is_current_month = (d.month == month)

            if is_current_month:
                iso = d.isoformat()
                fb = feedback.get(iso, {})
                emoji = fb.get("emoji", "")
                comment = fb.get("comment", "")
                focus = fb.get("focus", "")
                duration = fb.get("duration", 0)
                has_data = bool(fb)
                label = f"{d.day}"
                # Определение фона ячейки
                day_heading = f"<div style='padding:6px; border-radius:6px'>{label}</div>"
                if d == today:
                    day_heading = f"<div style='background:#fffacd; padding:6px; border-radius:6px'>{label}</div>"  # Светло-зелёный для сегодня
                elif d.weekday() in REST_DAYS and is_current_month:
                    day_heading = f"<div style='background:#e6ffe6; padding:6px; border-radius:6px'>{label}</div>"  # Зелёный фон для отдыха
                elif has_data:
                    day_heading = f"<div style='background:#e6f0ff; padding:6px; border-radius:6px'>{label}</div>"  # Светло-синий фон для тренировки

                if iso in monthly_plan:
                    exercises_list = monthly_plan[iso]["упражнения"]
                    exercises_html = "<br>".join(exercises_list)
                    # Добавляем тип (отдых/тренировка) к упражнениям
                    plan_type = monthly_plan[iso]["тип"]
                    day_heading_with_plan = f"{day_heading}<div style='font-size:12px;color:#555;'><b>{plan_type.capitalize()}:</b> {exercises_html}</div>"
                    col.markdown(day_heading_with_plan, unsafe_allow_html=True)
                else:
                    col.markdown(day_heading, unsafe_allow_html=True)

                info_lines = ""
                if emoji:
                    info_lines += f"{emoji} "
                if comment:
                    short = (comment[:40] + "...") if len(comment) > 40 else comment
                    info_lines += f"<div style='font-size:12px;color:#333'>{short}</div>"
                if focus and not info_lines:
                    info_lines += f"<div style='font-size:12px;color:#666'>{focus}</div>"

                if col.button(f"Открыть {iso}", key=f"btn_{iso}"):
                    st.session_state.selected_date = iso

                quick_cols = col.columns([1, 1, 1, 1, 1, 1])
                QUICK = ["💪", "🔥", "😅", "❤️", "😴", "✔️"]
                for qi, qc in enumerate(QUICK):
                    style_label = qc + " ✓" if qc == fb.get("emoji") else qc
                    if quick_cols[qi].button(style_label, key=f"quick_{iso}_{qi}"):
                        fb_cur = feedback.get(iso, {})
                        fb_cur["emoji"] = qc
                        fb_cur.setdefault("comment", fb_cur.get("comment", ""))
                        fb_cur.setdefault("focus", fb_cur.get("focus", ""))
                        fb_cur.setdefault("duration", fb_cur.get("duration", 0))
                        fb_cur.setdefault("exercises", fb_cur.get("exercises", []))
                        feedback[iso] = fb_cur
                        save_feedback(feedback)
                        st.session_state.selected_date = iso
            else:
                col.empty()


    # ПРАВАЯ ПАНЕЛЬ:редактор дня
    with st.sidebar:
        st.header("Редактор дня")
        sel = st.session_state.get("selected_date")
        if not sel:
            st.info("Выберите день в календаре для редактирования.")
        else:
            st.markdown(f"### {sel}")
            fb = feedback.get(sel, {})
            emoji_default = fb.get("emoji", "⚪️")
            comment_default = fb.get("comment", "")
            focus_default = fb.get("focus", "")
            duration_default = fb.get("duration", 30)
            exercises_default = ", ".join(fb.get("exercises", []))

            new_emoji = st.radio("Эмодзи", ["⚪️","💪","🔥","😅","❤️","😴","✔️"], index=["⚪️","💪","🔥","😅","❤️","😴","✔️"].index(emoji_default))
            new_comment = st.text_area("Комментарий", value=comment_default)
            new_duration = st.number_input("Длительность (мин)", min_value=0, max_value=600, value=int(duration_default))

            if st.button("Сохранить"):
                feedback[sel] = {
                    "emoji": new_emoji,
                    "comment": new_comment,
                    "duration": int(new_duration),
                }
                save_feedback(feedback)
                st.success("Сохранено ✅")
                st.session_state[f"saved_{sel}"] = datetime.now().isoformat()

# СТАТИСТИКА
with tab_statistics:
    st.header("📈 Статистика")
    history_list = st.session_state.get('progress_history', [])
    if history_list:
        current_entry = history_list[-1]
        current_scores = current_entry["scores"]
        current_reps = current_entry["repetition_history"]
    else:
        current_scores = {}
        current_reps = []
        
        # Статистика по выбранному месяцу
        st.subheader("Статистика месяца")
        month_keys = [d.isoformat() for d in month_days if d.month == month]
        filled = [k for k in month_keys if feedback.get(k) and feedback.get(k).get("emoji","⚪️") != "⚪️"]
        durations = [feedback[k].get("duration",0) for k in month_keys if feedback.get(k) and isinstance(feedback[k].get("duration",0), (int,float))]
        avg_duration = (sum(durations)/len(durations)) if durations else 0
        st.write(f"Выполнено дней: {len(filled)} из {len(month_keys)}")
        st.write(f"Средняя длительность (по выполненным дням): {avg_duration:.1f} мин")

        emojis = [feedback[k].get("emoji","⚪️") for k in month_keys if feedback.get(k)]
        if emojis:
            counts = Counter(emojis)
            df_emoji = pd.DataFrame(list(counts.items()), columns=["Эмодзи","Частота"])
            st.dataframe(df_emoji, hide_index=True)
            fig2, ax2 = plt.subplots()
            ax2.pie(df_emoji["Частота"], labels=df_emoji["Эмодзи"], autopct="%d%%")
            ax2.set_title("Распределение эмоций за месяц")
            st.pyplot(fig2)

         # Мотивация по прогрессу
            ratio = len(filled) / len(month_keys) if month_keys else 0
            if ratio == 0:
                motivation_dynamic = "🚀 Начни этот месяц с первой тренировки!"
            elif ratio < 0.25:
                motivation_dynamic = "💪 Отличное начало, не сдавайся!"
            elif ratio < 0.5:
                motivation_dynamic = "🔥 Почти половина месяца позади — держи темп!"
            elif ratio < 0.75:
                motivation_dynamic = "🏋️‍♀️ Отличный прогресс! Ты близок к цели!"
            else:
                motivation_dynamic = "🌟 Невероятно! Этот месяц — твой лучший!"
            st.markdown("---")
            st.markdown(f"### {motivation_dynamic}")
        else:
            st.warning("Данные прогресса отсутствуют. Пройдите физический тест, чтобы начать отслеживание.")

        week_counts = []
        week_labels = []
        for week_start in range(0, len(month_days), 7):
            week = month_days[week_start:week_start+7]
            ws = [d.isoformat() for d in week if d.month == month]
            done = sum(1 for k in ws if feedback.get(k) and feedback.get(k).get("emoji","⚪️") != "⚪️")
            week_counts.append(done)
            start_day = week[0].day
            start_month = MONTHS_RU_NUM[week[0].month][:3]
            week_labels.append(f"{start_day} {start_month}")
        fig3, ax3 = plt.subplots()
        ax3.bar(week_labels, week_counts)
        ax3.set_ylim(0, max(week_counts) + 1)
        ax3.set_yticks(range(0, max(week_counts) + 2))
        ax3.set_title("Выполнено дней по неделям месяца")
        st.pyplot(fig3)
        
#Кнопки сохранения и загрузки данных
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button('💾 Скачать мой прогресс'):
        import json
        data = {
            "profile": st.session_state.get('profile', {}),
            "progress_history": st.session_state.get('progress_history', [])
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        st.download_button(
            label='📥 Скачать JSON',
            data=json_str,
            file_name='my_sport_progress.json',
            mime='application/json'
        )

with col2:
    uploaded = st.file_uploader('📤 Загрузить прогресс', type=['json'])
    if uploaded:
        import json
        data = json.load(uploaded)
        if 'profile' in data:
            st.session_state['profile'] = data['profile']
        if 'progress_history' in data:
            st.session_state['progress_history'] = data['progress_history']
        st.success('Данные загружены! Обновите страницу.')        
        

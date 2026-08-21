import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

# --- ФУНКЦИЯ ДЛЯ ПОИСКА ФАЙЛА ---
def resource_path(relative_path):
    """Возвращает правильный путь к файлу (работает в .exe и в обычном режиме)"""
    try:
        # Если запущено как .exe
        base_path = sys._MEIPASS
    except Exception:
        # Если запущено как скрипт
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="Статистика бакалавриат", layout="wide")

# --- ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_data():
    file_path = resource_path("Bak.xlsx")
    df = pd.read_excel(file_path, sheet_name="Бакалавриат")

    # Очищаем категории
    df["Категория места"] = df["Категория места"].str.strip()

    # Объединяем "Отдельная квота" и "Отдельная квота, без ВИ"
    df["Категория места"] = df["Категория места"].replace(
        "Отдельная квота, без ВИ", "Отдельная квота"
    )

    # Преобразуем баллы в числа (прочерки -> NaN)
    df["Баллы ЕГЭ"] = pd.to_numeric(df["Баллы ЕГЭ"], errors="coerce")

    # Добавляем колонку "Есть баллы"
    df["Есть баллы"] = df["Баллы ЕГЭ"].notna()

    # --- ДОБАВЛЯЕМ КОЛОНКУ "Тип оплаты" (БЮДЖЕТ / ПЛАТНО) ---
    budget_categories = ["Основные места", "Особая квота", "Отдельная квота", "Целевая квота"]
    df["Тип оплаты"] = df["Категория места"].apply(
        lambda x: "Бюджет" if x in budget_categories else "Платно"
    )

    return df

df = load_data()

# --- БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ ---
st.sidebar.header("Фильтры")

directions = ["Все"] + sorted(df["Направление"].unique().tolist())
selected_direction = st.sidebar.selectbox("Направление", directions)

categories = ["Все"] + sorted(df["Категория места"].unique().tolist())
selected_category = st.sidebar.selectbox("Категория места", categories)

# --- ПРИМЕНЕНИЕ ФИЛЬТРОВ ---
filtered_df = df.copy()

if selected_direction != "Все":
    filtered_df = filtered_df[filtered_df["Направление"] == selected_direction]

if selected_category != "Все":
    filtered_df = filtered_df[filtered_df["Категория места"] == selected_category]

# --- БЛОК 1: ОБЩАЯ СВОДКА ---
st.header("Общая сводка")

# Общее количество мест
total_places = len(filtered_df)
budget_places = len(filtered_df[filtered_df["Тип оплаты"] == "Бюджет"])
paid_places = len(filtered_df[filtered_df["Тип оплаты"] == "Платно"])

col1, col2, col3 = st.columns(3)
col1.metric("Всего мест", total_places)
col2.metric("Бюджет", budget_places)
col3.metric("Платно", paid_places)

st.markdown("---")

# --- ПРОХОДНЫЕ БАЛЛЫ ПО НАПРАВЛЕНИЯМ ---
st.subheader("Проходные баллы по направлениям")

directions_list = sorted(filtered_df["Направление"].unique())
passing_scores = []

for direction in directions_list:
    direction_df = filtered_df[filtered_df["Направление"] == direction]

    main_scores = direction_df[
        (direction_df["Категория места"] == "Основные места") &
        (direction_df["Баллы ЕГЭ"].notna())
    ]

    paid_scores = direction_df[
        (direction_df["Категория места"] == "Платные места") &
        (direction_df["Баллы ЕГЭ"].notna())
    ]

    main_pass = int(main_scores["Баллы ЕГЭ"].min()) if len(main_scores) > 0 else "—"
    paid_pass = int(paid_scores["Баллы ЕГЭ"].min()) if len(paid_scores) > 0 else "—"

    main_count = len(main_scores)
    paid_count = len(paid_scores)

    passing_scores.append({
        "Направление": direction,
        "Основные места (проходной)": main_pass,
        "Основные места (кол-во)": main_count,
        "Платные места (проходной)": paid_pass,
        "Платные места (кол-во)": paid_count
    })

passing_df = pd.DataFrame(passing_scores)

st.dataframe(
    passing_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Направление": "Направление",
        "Основные места (проходной)": st.column_config.NumberColumn("Основные (проходной)", format="%d"),
        "Основные места (кол-во)": st.column_config.NumberColumn("Основные (кол-во)", format="%d"),
        "Платные места (проходной)": st.column_config.NumberColumn("Платные (проходной)", format="%d"),
        "Платные места (кол-во)": st.column_config.NumberColumn("Платные (кол-во)", format="%d")
    }
)

st.markdown("---")

# --- БЛОК 2: БАЛЛЫ ПО КАТЕГОРИЯМ ---
st.header("Баллы по категориям")

stats_list = []

for (direction, category), group in filtered_df.groupby(["Направление", "Категория места"]):
    with_scores = group[group["Баллы ЕГЭ"].notna()]
    without_scores = group[group["Баллы ЕГЭ"].isna()]

    bvi_count = len(without_scores)
    typ = group["Тип оплаты"].iloc[0]

    if len(with_scores) > 0:
        stats_list.append({
            "Направление": direction,
            "Категория места": category,
            "Тип оплаты": typ,
            "Минимальный": int(with_scores["Баллы ЕГЭ"].min()),
            "Средний": round(with_scores["Баллы ЕГЭ"].mean(), 1),
            "Максимальный": int(with_scores["Баллы ЕГЭ"].max()),
            "Сдававших": len(with_scores),
            "БВИ": bvi_count,
            "Всего": len(group)
        })
    else:
        stats_list.append({
            "Направление": direction,
            "Категория места": category,
            "Тип оплаты": typ,
            "Минимальный": "—",
            "Средний": "—",
            "Максимальный": "—",
            "Сдававших": 0,
            "БВИ": bvi_count,
            "Всего": len(group)
        })

stats_df = pd.DataFrame(stats_list)

st.dataframe(
    stats_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Направление": "Направление",
        "Категория места": "Категория",
        "Тип оплаты": "Тип оплаты",
        "Минимальный": "Минимальный",
        "Средний": "Средний",
        "Максимальный": "Максимальный",
        "Сдававших": st.column_config.NumberColumn("Сдававших", format="%d"),
        "БВИ": st.column_config.NumberColumn("БВИ", format="%d"),
        "Всего": st.column_config.NumberColumn("Всего", format="%d")
    }
)

st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")

# --- БЛОК 3: ПО НАПРАВЛЕНИЯМ ---
st.header("По направлениям")

all_directions = sorted(filtered_df["Направление"].unique())

for direction in all_directions:
    direction_df = filtered_df[filtered_df["Направление"] == direction]

    st.subheader(f"Направление: {direction}")

    total_students = len(direction_df)
    budget_students = len(direction_df[direction_df["Тип оплаты"] == "Бюджет"])
    paid_students = len(direction_df[direction_df["Тип оплаты"] == "Платно"])
    with_scores = direction_df[direction_df["Баллы ЕГЭ"].notna()]
    bvi_students = direction_df[direction_df["Баллы ЕГЭ"].isna()]

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Всего мест", total_students)
    col2.metric("Бюджет", budget_students)
    col3.metric("Платно", paid_students)
    col4.metric("Сдававших ЕГЭ", len(with_scores))
    col5.metric("БВИ", len(bvi_students))

    if len(with_scores) > 0:
        col6.metric("Средний балл", f"{with_scores['Баллы ЕГЭ'].mean():.1f}")
    else:
        col6.metric("Средний балл", "—")

    dir_stats_list = []

    for category in sorted(direction_df["Категория места"].unique()):
        cat_df = direction_df[direction_df["Категория места"] == category]
        cat_with_scores = cat_df[cat_df["Баллы ЕГЭ"].notna()]
        cat_bvi = cat_df[cat_df["Баллы ЕГЭ"].isna()]
        typ = cat_df["Тип оплаты"].iloc[0]

        if len(cat_with_scores) > 0:
            dir_stats_list.append({
                "Категория": category,
                "Тип оплаты": typ,
                "Всего": len(cat_df),
                "Сдававших": len(cat_with_scores),
                "БВИ": len(cat_bvi),
                "Минимальный": int(cat_with_scores["Баллы ЕГЭ"].min()),
                "Средний": round(cat_with_scores["Баллы ЕГЭ"].mean(), 1),
                "Максимальный": int(cat_with_scores["Баллы ЕГЭ"].max())
            })
        else:
            dir_stats_list.append({
                "Категория": category,
                "Тип оплаты": typ,
                "Всего": len(cat_df),
                "Сдававших": 0,
                "БВИ": len(cat_bvi),
                "Минимальный": "—",
                "Средний": "—",
                "Максимальный": "—"
            })

    dir_stats_df = pd.DataFrame(dir_stats_list)

    st.dataframe(
        dir_stats_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Категория": "Категория",
            "Тип оплаты": "Тип оплаты",
            "Всего": st.column_config.NumberColumn("Всего", format="%d"),
            "Сдававших": st.column_config.NumberColumn("Сдававших", format="%d"),
            "БВИ": st.column_config.NumberColumn("БВИ", format="%d"),
            "Минимальный": "Минимальный",
            "Средний": "Средний",
            "Максимальный": "Максимальный"
        }
    )

st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")

# --- БЛОК 4: СРАВНЕНИЕ СРЕДНИХ БАЛЛОВ ---
st.header("Сравнение средних баллов")

chart_data = stats_df[stats_df["Средний"] != "—"].copy()
chart_data["Средний"] = chart_data["Средний"].astype(float)

if len(chart_data) > 0:
    chart_data["Направление и категория"] = chart_data["Направление"] + " - " + chart_data["Категория места"]

    fig = px.bar(
        chart_data,
        x="Направление и категория",
        y="Средний",
        color="Тип оплаты",
        text="Средний",
        color_discrete_sequence=["#1a237e", "#e65100"]
    )
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Средний балл",
        showlegend=True,
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Нет данных для построения графика")

st.caption(f"Данные обновлены: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}")
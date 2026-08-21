import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys


# --- Путь к ресурсам (работает и в .exe, и в обычном запуске) ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


st.set_page_config(page_title="Статистика поступлений", layout="wide")

PAID_LABEL = "Платные места"
MAIN_BUDGET_LABEL = "Основные места"


# --- Загрузка и нормализация данных ---
@st.cache_data
def load_bachelor():
    df = pd.read_excel(resource_path("Bak.xlsx"), sheet_name="Бакалавриат")
    df["Направление"] = df["Направление"].str.strip()
    df["Категория места"] = df["Категория места"].str.strip()
    df["Балл"] = pd.to_numeric(df["Баллы ЕГЭ"], errors="coerce")
    df["Тип"] = df["Категория места"].apply(
        lambda x: "Платно" if x == PAID_LABEL else "Бюджет"
    )
    return df[["Направление", "Категория места", "Балл", "Тип"]]


@st.cache_data
def load_master():
    df = pd.read_excel(resource_path("Mag.xlsx"), sheet_name="Лист1")
    df["Направление"] = df["Направление"].str.strip()
    df["Категория места"] = df["Категория места"].str.strip()
    df["Балл"] = pd.to_numeric(df["Балл_ВИ"], errors="coerce")
    df["Тип"] = df["Категория места"].apply(
        lambda x: "Платно" if x == PAID_LABEL else "Бюджет"
    )
    return df[["Направление", "Категория места", "Балл", "Тип"]]


LEVELS = {
    "Бакалавриат": load_bachelor,
    "Магистратура": load_master,
}

# --- Выбор уровня образования ---
st.sidebar.header("Уровень")
selected_level = st.sidebar.radio("Уровень образования", list(LEVELS.keys()))

try:
    df = LEVELS[selected_level]()
except FileNotFoundError as e:
    st.error(
        f"Не найден файл с данными для уровня «{selected_level}»: {e}\n\n"
        "Проверь, что файл лежит рядом со скриптом (или добавлен в датасеты сборки)."
    )
    st.stop()

if df.empty:
    st.info(f"Для уровня «{selected_level}» пока нет данных.")
    st.stop()

# --- Фильтры ---
st.sidebar.header("Фильтры")

directions = ["Все"] + sorted(df["Направление"].unique().tolist())
selected_direction = st.sidebar.selectbox("Направление", directions)

categories = ["Все"] + sorted(df["Категория места"].unique().tolist())
selected_category = st.sidebar.selectbox("Категория места", categories)

filtered_df = df.copy()
if selected_direction != "Все":
    filtered_df = filtered_df[filtered_df["Направление"] == selected_direction]
if selected_category != "Все":
    filtered_df = filtered_df[filtered_df["Категория места"] == selected_category]

st.title(f"Статистика поступлений — {selected_level}")

# --- Блок 1: Общая сводка ---
st.header("Общая сводка")

total_places = len(filtered_df)
budget_places = len(filtered_df[filtered_df["Тип"] == "Бюджет"])
paid_places = len(filtered_df[filtered_df["Тип"] == "Платно"])

col1, col2, col3 = st.columns(3)
col1.metric("Всего мест", total_places)
col2.metric("Бюджет", budget_places)
col3.metric("Платно", paid_places)

st.markdown("---")

# --- Блок 2: Проходные баллы по направлениям ---
st.subheader("Проходные баллы по направлениям")

passing_rows = []
for direction in sorted(filtered_df["Направление"].unique()):
    direction_df = filtered_df[filtered_df["Направление"] == direction]

    budget_scores = direction_df[
        (direction_df["Категория места"] == MAIN_BUDGET_LABEL) & direction_df["Балл"].notna()
    ]
    paid_scores = direction_df[
        (direction_df["Категория места"] == PAID_LABEL) & direction_df["Балл"].notna()
    ]

    passing_rows.append({
        "Направление": direction,
        "Бюджет (проходной)": int(budget_scores["Балл"].min()) if len(budget_scores) else None,
        "Бюджет (кол-во)": len(budget_scores),
        "Платно (проходной)": int(paid_scores["Балл"].min()) if len(paid_scores) else None,
        "Платно (кол-во)": len(paid_scores),
    })

passing_df = pd.DataFrame(passing_rows)

st.dataframe(
    passing_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Бюджет (проходной)": st.column_config.NumberColumn(format="%.0f"),
        "Бюджет (кол-во)": st.column_config.NumberColumn(format="%d"),
        "Платно (проходной)": st.column_config.NumberColumn(format="%.0f"),
        "Платно (кол-во)": st.column_config.NumberColumn(format="%d"),
    },
)

st.markdown("---")

# --- Блок 3: Баллы по категориям ---
st.header("Баллы по категориям")

stats_rows = []
for (direction, category), group in filtered_df.groupby(["Направление", "Категория места"]):
    with_scores = group[group["Балл"].notna()]
    without_scores = group[group["Балл"].isna()]
    typ = group["Тип"].iloc[0]

    if len(with_scores):
        stats_rows.append({
            "Направление": direction,
            "Категория места": category,
            "Тип": typ,
            "Минимальный": int(with_scores["Балл"].min()),
            "Средний": round(with_scores["Балл"].mean(), 1),
            "Максимальный": int(with_scores["Балл"].max()),
            "С баллом": len(with_scores),
            "Без ВИ": len(without_scores),
            "Всего": len(group),
        })
    else:
        stats_rows.append({
            "Направление": direction,
            "Категория места": category,
            "Тип": typ,
            "Минимальный": None,
            "Средний": None,
            "Максимальный": None,
            "С баллом": 0,
            "Без ВИ": len(without_scores),
            "Всего": len(group),
        })

stats_df = pd.DataFrame(stats_rows)

st.dataframe(
    stats_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Минимальный": st.column_config.NumberColumn(format="%.0f"),
        "Средний": st.column_config.NumberColumn(format="%.1f"),
        "Максимальный": st.column_config.NumberColumn(format="%.0f"),
        "С баллом": st.column_config.NumberColumn(format="%d"),
        "Без ВИ": st.column_config.NumberColumn(format="%d"),
        "Всего": st.column_config.NumberColumn(format="%d"),
    },
)

st.write("")
st.write("")

# --- Блок 4: По направлениям (детально) ---
st.header("По направлениям")

for direction in sorted(filtered_df["Направление"].unique()):
    direction_df = filtered_df[filtered_df["Направление"] == direction]

    st.subheader(f"Направление: {direction}")

    total_students = len(direction_df)
    budget_students = len(direction_df[direction_df["Тип"] == "Бюджет"])
    paid_students = len(direction_df[direction_df["Тип"] == "Платно"])
    with_scores = direction_df[direction_df["Балл"].notna()]
    without_scores = direction_df[direction_df["Балл"].isna()]

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Всего мест", total_students)
    col2.metric("Бюджет", budget_students)
    col3.metric("Платно", paid_students)
    col4.metric("С баллом", len(with_scores))
    col5.metric("Без ВИ", len(without_scores))
    col6.metric("Средний балл", f"{with_scores['Балл'].mean():.1f}" if len(with_scores) else "—")

    dir_rows = []
    for category in sorted(direction_df["Категория места"].unique()):
        cat_df = direction_df[direction_df["Категория места"] == category]
        cat_with_scores = cat_df[cat_df["Балл"].notna()]
        cat_without = cat_df[cat_df["Балл"].isna()]
        typ = cat_df["Тип"].iloc[0]

        if len(cat_with_scores):
            dir_rows.append({
                "Категория места": category,
                "Тип": typ,
                "Всего": len(cat_df),
                "С баллом": len(cat_with_scores),
                "Без ВИ": len(cat_without),
                "Минимальный": int(cat_with_scores["Балл"].min()),
                "Средний": round(cat_with_scores["Балл"].mean(), 1),
                "Максимальный": int(cat_with_scores["Балл"].max()),
            })
        else:
            dir_rows.append({
                "Категория места": category,
                "Тип": typ,
                "Всего": len(cat_df),
                "С баллом": 0,
                "Без ВИ": len(cat_without),
                "Минимальный": None,
                "Средний": None,
                "Максимальный": None,
            })

    dir_stats_df = pd.DataFrame(dir_rows)

    st.dataframe(
        dir_stats_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Всего": st.column_config.NumberColumn(format="%d"),
            "С баллом": st.column_config.NumberColumn(format="%d"),
            "Без ВИ": st.column_config.NumberColumn(format="%d"),
            "Минимальный": st.column_config.NumberColumn(format="%.0f"),
            "Средний": st.column_config.NumberColumn(format="%.1f"),
            "Максимальный": st.column_config.NumberColumn(format="%.0f"),
        },
    )

st.write("")
st.write("")

# --- Блок 5: Сравнение среднего балла ---
st.header("Сравнение среднего балла")

chart_data = stats_df[stats_df["Средний"].notna()].copy()
chart_data["Средний"] = chart_data["Средний"].astype(float)

if len(chart_data):
    chart_data["Направление + категория"] = (
        chart_data["Направление"] + " — " + chart_data["Категория места"]
    )

    fig = px.bar(
        chart_data,
        x="Направление + категория",
        y="Средний",
        color="Тип",
        text="Средний",
        color_discrete_sequence=["#1a237e", "#e65100"],
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(xaxis_title="", yaxis_title="Средний балл", showlegend=True, height=500)
    st.plotly_chart(fig, width="stretch")
else:
    st.info("Нет данных для построения графика.")

st.caption(f"Данные обновлены: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}")
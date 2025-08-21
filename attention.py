import streamlit as st
import pandas as pd

# -------------------
# Налаштування сторінки
# -------------------
st.set_page_config(page_title="Attention Split Calculator", layout="wide")

st.title("🎯 Attention Split Calculator")
st.markdown("Інтерактивний калькулятор для оцінки **ефективності інструментів** та побудови оптимального 📊 **спліту бюджету**.")

# -------------------
# Вхідні дані
# -------------------
num_tools = st.slider("🔢 Кількість інструментів", 1, 4, 2)

tools = {
    "ТБ": "📺",
    "Мобайл": "📱",
    "ПК": "💻",
    "Аудіо": "🎧"
}

screen_coef = {"ТБ": 1.0, "ПК": 0.71, "Мобайл": 0.42, "Аудіо": 0.2}

data = []

st.markdown("---")

for i, (tool, emoji) in enumerate(list(tools.items())[:num_tools]):
    with st.container():
        st.subheader(f"{emoji} {tool}")

        col1, col2, col3 = st.columns(3)
        with col1:
            budget = st.number_input(f"Бюджет {tool} ($)", min_value=0.0, step=100.0, key=f"budget_{tool}")
            cpm = st.number_input(f"CPM {tool} ($)", min_value=0.0, step=0.1, key=f"cpm_{tool}")
        with col2:
            reach_share = st.slider(f"Доля потрапляння в ЦА {tool}", 0.0, 1.0, 0.5, step=0.01, key=f"reach_{tool}")
            viewability = st.slider(f"Viewability {tool}", 0.0, 1.0, 0.7, step=0.01, key=f"view_{tool}")
        with col3:
            creative_time = st.number_input(f"Хронометраж креативів (сек) {tool}", min_value=0, step=5, key=f"time_{tool}")

        st.markdown("**🎥 VTR (Video Through Rate)**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            vtr25 = st.slider(f"VTR 25% {tool}", 0.0, 1.0, 0.25, step=0.01, key=f"vtr25_{tool}")
        with c2:
            vtr50 = st.slider(f"VTR 50% {tool}", 0.0, 1.0, 0.15, step=0.01, key=f"vtr50_{tool}")
        with c3:
            vtr75 = st.slider(f"VTR 75% {tool}", 0.0, 1.0, 0.10, step=0.01, key=f"vtr75_{tool}")
        with c4:
            vtr100 = st.slider(f"VTR 100% {tool}", 0.0, 1.0, 0.05, step=0.01, key=f"vtr100_{tool}")

        # -------------------
        # Розрахунки
        # -------------------
        impressions = (budget / cpm * 1000) if cpm > 0 else 0
        viewed_impressions = impressions * viewability

        avg_time_viewed = (vtr25*0.25 + vtr50*0.5 + vtr75*0.75 + vtr100*1.0) * creative_time
        ARM = viewed_impressions * avg_time_viewed / 1000 if creative_time > 0 else 0
        ACPM = budget / ARM if ARM > 0 else 0

        data.append([f"{emoji} {tool}", budget, cpm, impressions, viewed_impressions, ARM, ACPM])

st.markdown("---")

# -------------------
# Таблиця результатів
# -------------------
df = pd.DataFrame(data, columns=["Інструмент", "Бюджет", "CPM", "Impressions", "Viewed Impressions", "ARM", "ACPM"])

st.subheader("📋 Результати розрахунків")
st.dataframe(df.style.format({
    "Бюджет": "{:,.0f} $",
    "CPM": "{:,.2f} $",
    "Impressions": "{:,.0f}",
    "Viewed Impressions": "{:,.0f}",
    "ARM": "{:,.2f}",
    "ACPM": "{:,.2f} $"
}))

# -------------------
# Спліт бюджету
# -------------------
if not df.empty:
    df_sorted = df.sort_values("ACPM")
    total_budget = df["Бюджет"].sum()
    split = []

    for _, row in df_sorted.iterrows():
        share = max(0.02, min(0.35, row["Бюджет"] / total_budget)) if total_budget > 0 else 0
        split.append(share)

    split_df = pd.DataFrame({
        "Інструмент": df_sorted["Інструмент"],
        "Частка бюджету (%)": [round(s*100,2) for s in split]
    })

    st.subheader("📊 Оптимальний спліт бюджету")
    st.dataframe(split_df.style.format({"Частка бюджету (%)": "{:.2f} %"}))

    # -------------------
    # Графік
    # -------------------
    st.bar_chart(split_df.set_index("Інструмент")["Частка бюджету (%)"])



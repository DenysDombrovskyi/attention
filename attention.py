import streamlit as st
import pandas as pd
import io

# -------------------
# Налаштування сторінки
# -------------------
st.set_page_config(page_title="Attention Split Calculator", layout="wide")

st.title("🎯 Attention Split Calculator")
st.markdown("Інтерактивний калькулятор для оцінки **ефективності інструментів** та побудови оптимального 📊 **спліту бюджету**.")

# -------------------
# Вхідні дані
# -------------------
num_tools = st.slider("🔢 Кількість інструментів", 1, 20, 2)

# Словник з загальними назвами інструментів
tools = {f"Інструмент {i}": "" for i in range(1, 21)}

# Коефіцієнти для кожного типу медіа
screen_coef = {"ТБ": 1.0, "ПК": 0.71, "Мобайл": 0.42, "Аудіо": 0.2}

data = []

st.markdown("---")

for i, (tool, emoji) in enumerate(list(tools.items())[:num_tools]):
    with st.container():
        st.subheader(f"{tool}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            budget = st.number_input(f"Бюджет {tool} ($)", min_value=0.0, step=100.0, key=f"budget_{tool}")
            cpm = st.number_input(f"CPM {tool} ($)", min_value=0.0, step=0.1, key=f"cpm_{tool}")
        
        st.markdown("**Частки розподілу за пристроями**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            share_tv = st.slider(f"Частка ТВ {tool}", 0.0, 1.0, 0.25, step=0.01, key=f"share_tv_{tool}")
        with c2:
            share_mobile = st.slider(f"Частка мобайлу {tool}", 0.0, 1.0, 0.25, step=0.01, key=f"share_mobile_{tool}")
        with c3:
            share_pc = st.slider(f"Частка ПК {tool}", 0.0, 1.0, 0.25, step=0.01, key=f"share_pc_{tool}")
        with c4:
            share_audio = st.slider(f"Частка аудіо {tool}", 0.0, 1.0, 0.25, step=0.01, key=f"share_audio_{tool}")

        viewability = st.slider(f"Viewability {tool}", 0.0, 1.0, 0.7, step=0.01, key=f"view_{tool}")
        creative_time = st.number_input(f"Хронометраж креативів (сек) {tool}", min_value=0, step=5, key=f"time_{tool}")

        st.markdown("**🎥 VTR (Video Through Rate)**")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            vtr25 = st.slider(f"VTR 25% {tool}", 0.0, 1.0, 0.25, step=0.01, key=f"vtr25_{tool}")
        with d2:
            vtr50 = st.slider(f"VTR 50% {tool}", 0.0, 1.0, 0.15, step=0.01, key=f"vtr50_{tool}")
        with d3:
            vtr75 = st.slider(f"VTR 75% {tool}", 0.0, 1.0, 0.10, step=0.01, key=f"vtr75_{tool}")
        with d4:
            vtr100 = st.slider(f"VTR 100% {tool}", 0.0, 1.0, 0.05, step=0.01, key=f"vtr100_{tool}")

        # -------------------
        # Розрахунки
        # -------------------
        impressions = (budget / cpm * 1000) if cpm > 0 else 0
        viewed_impressions = impressions * viewability

        # Розрахунок загального коефіцієнта розміру екрана
        total_screen_coeff = (share_tv * screen_coef["ТБ"] +
                             share_mobile * screen_coef["Мобайл"] +
                             share_pc * screen_coef["ПК"] +
                             share_audio * screen_coef["Аудіо"])
        
        target_impressions = viewed_impressions * total_screen_coeff

        avg_time_viewed = (vtr25*0.25 + vtr50*0.5 + vtr75*0.75 + vtr100*1.0) * creative_time
        APM = target_impressions * avg_time_viewed / 1000 if creative_time > 0 else 0
        ACPM = budget / APM if APM > 0 else 0

        data.append([
            tool, budget, cpm, impressions, viewed_impressions,
            share_tv, share_mobile, share_pc, share_audio,
            APM, ACPM
        ])

st.markdown("---")

# -------------------
# Таблиця результатів
# -------------------
df = pd.DataFrame(data, columns=[
    "Інструмент", "Бюджет", "CPM", "Impressions", "Viewed Impressions",
    "Частка ТВ", "Частка Мобайлу", "Частка ПК", "Частка Аудіо",
    "APM", "ACPM"
])

st.subheader("📋 Результати розрахунків")
st.dataframe(df.style.format({
    "Бюджет": "{:,.0f} $",
    "CPM": "{:,.2f} $",
    "Impressions": "{:,.0f}",
    "Viewed Impressions": "{:,.0f}",
    "Частка ТВ": "{:.2f}",
    "Частка Мобайлу": "{:.2f}",
    "Частка ПК": "{:.2f}",
    "Частка Аудіо": "{:.2f}",
    "APM": "{:,.2f}",
    "ACPM": "{:,.2f} $"
}))

# -------------------
# Оновлений спліт бюджету на основі ACPM
# -------------------
split_df = None
if not df.empty and df["Бюджет"].sum() > 0:
    # Замість початкового бюджету, розподіляємо на основі ACPM
    df_temp = df.copy()
    
    # Обробка випадку, коли ACPM = 0, щоб уникнути ділення на нуль
    df_temp['ACPM_safe'] = df_temp['ACPM'].replace(0, float('inf'))
    
    # Розрахунок показника ефективності (зворотна величина ACPM)
    df_temp['efficiency_score'] = 1 / df_temp['ACPM_safe']
    
    total_efficiency_score = df_temp['efficiency_score'].sum()
    
    if total_efficiency_score > 0:
        df_temp['Частка бюджету (%)'] = (df_temp['efficiency_score'] / total_efficiency_score) * 100
    else:
        df_temp['Частка бюджету (%)'] = 0

    df_sorted = df_temp.sort_values("Частка бюджету (%)", ascending=False)

    split_df = pd.DataFrame({
        "Інструмент": df_sorted["Інструмент"],
        "Частка бюджету (%)": df_sorted["Частка бюджету (%)"]
    })

    st.subheader("📊 Оптимальний спліт бюджету")
    st.dataframe(split_df.style.format({"Частка бюджету (%)": "{:.2f} %"}))

    # -------------------
    # Графік
    # -------------------
    st.bar_chart(split_df.set_index("Інструмент")["Частка бюджету (%)"])

# -------------------
# Кнопка для завантаження в Excel
# -------------------
st.markdown("---")

def to_excel(df_results, df_split):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_results.to_excel(writer, sheet_name='Результати', index=False)
        if df_split is not None:
            df_split.to_excel(writer, sheet_name='Спліт', index=False)
    processed_data = output.getvalue()
    return processed_data

if not df.empty and df["Бюджет"].sum() > 0:
    excel_data = to_excel(df, split_df)
    st.download_button(
        label="Завантажити в Excel ⬇️",
        data=excel_data,
        file_name='attention_split_results.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


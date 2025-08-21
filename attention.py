import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="ARM & ACPM Calculator", page_icon="📊", layout="centered")

st.title("📊 Калькулятор ARM та ACPM")
st.markdown("Введіть параметри кампанії та отримайте розрахунок ефективності і бюджетний спліт по інструментах.")

# --- Вхідні параметри ---
st.sidebar.header("🔧 Параметри кампанії")

budget = st.sidebar.number_input("Бюджет (грн)", min_value=1000.0, value=100000.0, step=1000.0)
cpm = st.sidebar.number_input("CPM (грн)", min_value=1.0, value=100.0)
reach_share = st.sidebar.slider("Доля попадання в ЦА", 0.0, 1.0, 0.8, 0.01)
creative_duration = st.sidebar.number_input("Хронометраж креативу (сек)", min_value=1.0, value=30.0)
viewability = st.sidebar.slider("Viewability", 0.0, 1.0, 0.7, 0.01)

# Вибір інструментів
available_channels = ["TV", "Mobile", "PC", "Audio"]
chosen_channels = st.sidebar.multiselect("Оберіть інструменти", available_channels, default=["TV", "Mobile", "PC"])

# VTR %
st.sidebar.subheader("📺 VTR")
vtr25 = st.sidebar.slider("VTR 25%", 0.0, 1.0, 0.6, 0.01)
vtr50 = st.sidebar.slider("VTR 50%", 0.0, 1.0, 0.4, 0.01)
vtr75 = st.sidebar.slider("VTR 75%", 0.0, 1.0, 0.2, 0.01)
vtr100 = st.sidebar.slider("VTR 100%", 0.0, 1.0, 0.1, 0.01)

# Коефіцієнти
coef = {"TV": 1.0, "PC": 0.71, "Mobile": 0.42, "Audio": 0.2}

st.sidebar.subheader("🎯 TVC коефіцієнти")
tvc_coef = {}
shares = {}
for ch in chosen_channels:
    shares[ch] = st.sidebar.slider(f"Доля {ch}", 0.0, 1.0, 0.25, 0.01)
    tvc_coef[ch] = st.sidebar.number_input(f"TVC coef {ch}", min_value=0.1, value=1.0, step=0.1)

# --- Розрахунки ---
impressions = (budget / cpm) * 1000 * reach_share
avg_time_viewed = (vtr25*0.25 + vtr50*0.50 + vtr75*0.75 + vtr100*1.0) * creative_duration
viewed_impressions = impressions * viewability
arm = viewed_impressions * avg_time_viewed / 1000
acpm = budget / arm if arm > 0 else float("inf")

apm_weighted = 0
for ch in shares:
    apm_weighted += impressions * shares[ch] * coef[ch] * tvc_coef[ch]

acpm_weighted = budget / apm_weighted if apm_weighted > 0 else float("inf")

# --- Вивід ---
st.subheader("📈 Результати розрахунків")
results_df = pd.DataFrame({
    "Показник": ["Impressions", "Average Time Viewed (сек)", "Viewed Impressions", "ARM", "ACPM (грн)", "ACPM Weighted by Quality (грн)"],
    "Значення": [round(impressions, 0), round(avg_time_viewed, 2), round(viewed_impressions, 0), round(arm, 2), round(acpm, 2), round(acpm_weighted, 2)]
})
st.table(results_df)

# --- Розрахунок спліту ---
st.subheader("💰 Оптимальний спліт бюджету")

acpm_channels = {}
for ch in shares:
    channel_apm = impressions * shares[ch] * coef[ch] * tvc_coef[ch]
    if channel_apm > 0:
        acpm_channels[ch] = budget / channel_apm
    else:
        acpm_channels[ch] = float("inf")

sorted_channels = sorted(acpm_channels.items(), key=lambda x: x[1])

split = {}
remaining = 1.0
for ch, _ in sorted_channels:
    share = min(0.35, remaining)
    share = max(0.02, share)
    split[ch] = share
    remaining -= share
    if remaining <= 0:
        break

total = sum(split.values())
for ch in split:
    split[ch] /= total

split_df = pd.DataFrame({
    "Інструмент": list(split.keys()),
    "Частка бюджету (%)": [f"{split[ch]*100:.2f}%" for ch in split]
})
st.table(split_df)

# --- Візуалізація ---
fig, ax = plt.subplots()
ax.pie([split[ch]*100 for ch in split], labels=list(split.keys()), autopct='%1.1f%%', startangle=90)
ax.set_title("Бюджетний спліт по інструментах")
st.pyplot(fig)

# --- Експорт ---
st.subheader("📤 Експорт результатів")
csv = results_df.to_csv(index=False).encode("utf-8-sig")
csv_split = split_df.to_csv(index=False).encode("utf-8-sig")
excel_writer = pd.ExcelWriter("results.xlsx", engine="xlsxwriter")
results_df.to_excel(excel_writer, sheet_name="Розрахунки", index=False)
split_df.to_excel(excel_writer, sheet_name="Спліт", index=False)
excel_writer.close()

st.download_button("⬇️ Завантажити результати (CSV)", csv, "results.csv", "text/csv")
st.download_button("⬇️ Завантажити спліт (CSV)", csv_split, "split.csv", "text/csv")
st.download_button("⬇️ Завантажити всі дані (Excel)", open("results.xlsx", "rb"), "results.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

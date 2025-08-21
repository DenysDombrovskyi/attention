import streamlit as st
import pandas as pd
import io
from scipy.optimize import linprog

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

# Вибір мети оптимізації
optimization_target = st.radio(
    "Виберіть мету оптимізації:",
    ("Мінімізувати ACPM", "Мінімізувати ACPM (з якістю)")
)

# Коефіцієнти для кожного типу медіа
screen_coef = {"ТБ": 1.0, "ПК": 0.71, "Мобайл": 0.42, "Аудіо": 0.2}

data = []
input_budgets = []

st.markdown("---")

for i in range(num_tools):
    with st.container():
        tool_name = st.text_input(f"Назва Інструменту {i+1}", f"Інструмент {i+1}", key=f"tool_name_{i}")
        st.subheader(f"{tool_name}")

        col1, col2 = st.columns(2)
        with col1:
            budget = st.number_input(f"Бюджет {tool_name} ($)", min_value=0.0, step=100.0, key=f"budget_{tool_name}")
            cpm = st.number_input(f"CPM {tool_name} ($)", min_value=0.0, step=0.1, key=f"cpm_{tool_name}")
            input_budgets.append(budget)
            
        with col2:
            quality_tool_coeff = st.slider(f"Коефіцієнт якості {tool_name}", 0.0, 1.0, 1.0, step=0.01, key=f"quality_tool_{tool_name}")
        
        st.markdown("**Частки розподілу за пристроями**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            share_tv = st.slider(f"Частка ТВ {tool_name}", 0.0, 1.0, 0.25, step=0.01, key=f"share_tv_{tool_name}")
        with c2:
            share_mobile = st.slider(f"Частка мобайлу {tool_name}", 0.0, 1.0, 0.25, step=0.01, key=f"share_mobile_{tool_name}")
        with c3:
            share_pc = st.slider(f"Частка ПК {tool_name}", 0.0, 1.0, 0.25, step=0.01, key=f"share_pc_{tool_name}")
        with c4:
            share_audio = st.slider(f"Частка аудіо {tool_name}", 0.0, 1.0, 0.25, step=0.01, key=f"share_audio_{tool_name}")

        col_new1, col_new2 = st.columns(2)
        with col_new1:
            viewability = st.slider(f"Viewability {tool_name}", 0.0, 1.0, 0.7, step=0.01, key=f"view_{tool_name}")
        with col_new2:
            ta_reach = st.slider(f"Потрапляння в ЦА {tool_name}", 0.0, 1.0, 1.0, step=0.01, key=f"ta_reach_{tool_name}")
            
        creative_time = st.number_input(f"Хронометраж креативів (сек) {tool_name}", min_value=0, step=5, key=f"time_{tool_name}")

        st.markdown("**🎥 VTR (Video Through Rate)**")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            vtr25 = st.slider(f"VTR 25% {tool_name}", 0.0, 1.0, 0.25, step=0.01, key=f"vtr25_{tool_name}")
        with d2:
            vtr50 = st.slider(f"VTR 50% {tool_name}", 0.0, 1.0, 0.15, step=0.01, key=f"vtr50_{tool_name}")
        with d3:
            vtr75 = st.slider(f"VTR 75% {tool_name}", 0.0, 1.0, 0.10, step=0.01, key=f"vtr75_{tool_name}")
        with d4:
            vtr100 = st.slider(f"VTR 100% {tool_name}", 0.0, 1.0, 0.05, step=0.01, key=f"vtr100_{tool_name}")

        # -------------------
        # Розрахунки для введених даних
        # -------------------
        impressions = (budget / cpm * 1000) if cpm > 0 else 0
        viewed_impressions = impressions * viewability
        targeted_impressions = viewed_impressions * ta_reach

        total_screen_coeff = (share_tv * screen_coef["ТБ"] +
                             share_mobile * screen_coef["Мобайл"] +
                             share_pc * screen_coef["ПК"] +
                             share_audio * screen_coef["Аудіо"])
        
        target_impressions = targeted_impressions * total_screen_coeff

        avg_time_viewed = (vtr25*0.25 + vtr50*0.5 + vtr75*0.75 + vtr100*1.0) * creative_time
        
        APM = target_impressions * avg_time_viewed / 1000 if creative_time > 0 else 0
        ACPM = budget / APM if APM > 0 else 0
        
        APM_wq = APM * quality_tool_coeff
        ACPM_wq = budget / APM_wq if APM_wq > 0 else 0

        data.append([
            tool_name, budget, cpm, impressions, viewed_impressions, targeted_impressions,
            share_tv, share_mobile, share_pc, share_audio,
            APM, ACPM, APM_wq, ACPM_wq, quality_tool_coeff, avg_time_viewed
        ])

st.markdown("---")

# -------------------
# Таблиця результатів для введеного спліту
# -------------------
df = pd.DataFrame(data, columns=[
    "Інструмент", "Бюджет", "CPM", "Impressions", "Viewed Impressions", "Targeted Impressions",
    "Частка ТВ", "Частка Мобайлу", "Частка ПК", "Частка Аудіо",
    "APM", "ACPM", "APM (з якістю)", "ACPM (з якістю)", "Коефіцієнт якості", "Середній час перегляду (сек)"
])

st.subheader("📋 Результати розрахунків для вашого спліту")
st.dataframe(df.style.format({
    "Бюджет": "{:,.0f} $",
    "CPM": "{:,.2f} $",
    "Impressions": "{:,.0f}",
    "Viewed Impressions": "{:,.0f}",
    "Targeted Impressions": "{:,.0f}",
    "Частка ТВ": "{:.2f}",
    "Частка Мобайлу": "{:.2f}",
    "Частка ПК": "{:.2f}",
    "Частка Аудіо": "{:.2f}",
    "APM": "{:,.2f}",
    "ACPM": "{:,.2f} $",
    "APM (з якістю)": "{:,.2f}",
    "ACPM (з якістю)": "{:,.2f} $",
    "Середній час перегляду (сек)": "{:,.2f}"
}))

total_input_budget = sum(input_budgets)

# -------------------
# Розрахунок тотальних показників
# -------------------
st.markdown("---")
st.subheader("📈 Тотальні показники кампанії")

if total_input_budget > 0:
    total_apm = df['APM'].sum()
    total_acpm = total_input_budget / total_apm if total_apm > 0 else 0

    total_apm_wq = df['APM (з якістю)'].sum()
    total_acpm_wq = total_input_budget / total_apm_wq if total_apm_wq > 0 else 0
    
    # Середньозважений час перегляду
    weighted_avg_time = (df['Середній час перегляду (сек)'] * df['Бюджет']).sum() / total_input_budget
    
    total_metrics_data = {
        "Показник": ["Загальний бюджет", "Загальний APM", "Загальний ACPM", "Загальний APM (з якістю)", "Загальний ACPM (з якістю)", "Середній час перегляду (сек)"],
        "Значення": [total_input_budget, total_apm, total_acpm, total_apm_wq, total_acpm_wq, weighted_avg_time]
    }
    total_metrics_df = pd.DataFrame(total_metrics_data)

    st.dataframe(total_metrics_df.style.format({
        "Значення": "{:,.2f}"  # Універсальний формат для всіх значень
    }))

# -------------------
# Оптимізований спліт за допомогою лінійного програмування
# -------------------
st.markdown("---")
st.subheader("📊 Оптимізований спліт бюджету")

if total_input_budget > 0:
    # Розрахунок коефіцієнтів ефективності для LP
    df['APM_rate'] = df['APM'] / df['Бюджет']
    df['APM_wq_rate'] = df['APM (з якістю)'] / df['Бюджет']

    if optimization_target == "Мінімізувати ACPM":
        c = -df['APM_rate'].fillna(0).values
    else:
        c = -df['APM_wq_rate'].fillna(0).values

    # Обмеження: сума бюджетів має дорівнювати загальному бюджету
    A_eq = [[1.0] * num_tools]
    b_eq = [total_input_budget]
    
    # Обмеження: бюджети не можуть бути від'ємними та мають бути в діапазоні 2%-40%
    min_budget = total_input_budget * 0.02
    max_budget = total_input_budget * 0.40
    bounds = [(min_budget, max_budget)] * num_tools
    
    # Якщо загальний бюджет недостатній для мінімальних лімітів
    if min_budget * num_tools > total_input_budget:
        st.error(f"Сума мінімальних бюджетів ({min_budget * num_tools:,.0f} $) перевищує загальний бюджет ({total_input_budget:,.0f} $). Збільште загальний бюджет або зменште кількість інструментів.")
        bounds = [(0, total_input_budget)] * num_tools

    result = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

    if result.success:
        optimized_budgets = result.x
        
        optimized_split_df = pd.DataFrame({
            "Інструмент": df["Інструмент"],
            "Оптимізований Бюджет ($)": optimized_budgets,
            "Частка бюджету (%)": (optimized_budgets / total_input_budget) * 100
        })

        st.dataframe(optimized_split_df.style.format({
            "Оптимізований Бюджет ($)": "{:,.0f} $",
            "Частка бюджету (%)": "{:.2f} %"
        }))
        
        st.bar_chart(optimized_split_df.set_index("Інструмент")["Частка бюджету (%)"])

        # -------------------
        # Порівняння сплітів
        # -------------------
        st.markdown("---")
        st.subheader("📈 Порівняння сплітів")
        
        total_apm_input = df['APM'].sum()
        total_acpm_input = total_input_budget / total_apm_input if total_apm_input > 0 else 0

        total_apm_wq_input = df['APM (з якістю)'].sum()
        total_acpm_wq_input = total_input_budget / total_apm_wq_input if total_apm_wq_input > 0 else 0
        
        df_optimized = df.copy()
        df_optimized['Оптимізований Бюджет'] = optimized_budgets
        
        total_apm_optimized = (df_optimized['APM_rate'] * df_optimized['Оптимізований Бюджет']).sum()
        total_acpm_optimized = total_input_budget / total_apm_optimized if total_apm_optimized > 0 else 0
        
        total_apm_wq_optimized = (df_optimized['APM_wq_rate'] * df_optimized['Оптимізований Бюджет']).sum()
        total_acpm_wq_optimized = total_input_budget / total_apm_wq_optimized if total_apm_wq_optimized > 0 else 0

        comparison_data = {
            "Показник": ["Загальний бюджет ($)", "Загальний APM", "Загальний ACPM ($)", "Загальний APM (з якістю)", "Загальний ACPM (з якістю)"],
            "Ваш спліт": [total_input_budget, total_apm_input, total_acpm_input, total_apm_wq_input, total_acpm_wq_input],
            "Оптимізований спліт": [total_input_budget, total_apm_optimized, total_acpm_optimized, total_apm_wq_optimized, total_acpm_wq_optimized]
        }
        comparison_df = pd.DataFrame(comparison_data)

        st.dataframe(comparison_df.style.format(
            formatter={
                "Ваш спліт": lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and x >= 1000 else f"{x:,.2f}",
                "Оптимізований спліт": lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and x >= 1000 else f"{x:,.2f}"
            }
        ))
        
        # -------------------
        # Завантаження в Excel
        # -------------------
        st.markdown("---")
        
        def to_excel(df_results, df_split_opt, df_comp, df_total_metrics):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_results.to_excel(writer, sheet_name='Результати', index=False)
                df_split_opt.to_excel(writer, sheet_name='Оптимізований спліт', index=False)
                df_comp.to_excel(writer, sheet_name='Порівняння', index=False)
                df_total_metrics.to_excel(writer, sheet_name='Тотальні показники', index=False)
            processed_data = output.getvalue()
            return processed_data

        excel_data = to_excel(df, optimized_split_df, comparison_df, total_metrics_df)
        st.download_button(
            label="Завантажити в Excel ⬇️",
            data=excel_data,
            file_name='attention_split_results.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    else:
        st.error("Не вдалося знайти оптимальне рішення. Перевірте, чи сума мінімальних бюджетів не перевищує загальний бюджет. ")
else:
    st.warning("Введіть загальний бюджет, щоб розрахувати оптимальний спліт.")

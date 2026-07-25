import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="لوحة تحكم مراقبة جودة الزبادي", layout="wide", page_icon="🥛")

# تنسيق عام للشاشة والاتجاه
st.markdown("""
<style>
    .stApp {
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {
        text-align: right !important;
    }
    table {
        direction: rtl;
        text-align: right;
    }
    [data-testid="stMetricValue"] {
        direction: ltr !important;
        unicode-bidi: embed;
        text-align: right !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🥛 منظومة إنتاج ومراقبة جودة الزبادي والهاسب (HACCP)")
st.markdown("لوحة التحكم الشاملة لمتابعة مراحل الإنتاج، قياسات اللزوجة والـ pH بدقة، التحاليل المايكروبيولوجية، سلسلة التبريد، وتحليل العيوب والهدر")

@st.cache_data
def get_dashboard_data():
    np.random.seed(42)
    
    shifts_list = ["وردية الصباح"] * 15 + ["وردية المساء"] * 15
    batch_nums = list(range(1, 16)) * 2
    batch_ids = [f"B{i}" for i in range(1, 16)] * 2
    
    cultures = np.random.choice([
        "Streptococcus thermophilus", 
        "Lactobacillus bulgaricus", 
        "Mix Blend (S.t + L.b)"
    ], size=30)
    
    df = pd.DataFrame({
        "Batch_Num": batch_nums,
        "Batch_ID": batch_ids,
        "Shift": shifts_list,
        "Starter_Culture": cultures,
        "Sensory": np.random.choice(["ممتاز", "جيد"], size=30),
        "Chemical_Analysis": np.random.choice(["خالي من المضادات", "مطابق للمواصفات"], size=30),
        "Microbiological": np.random.choice(["مطابق وبادئ نشط", "قبول آمن"], size=30),
        "pH": np.random.uniform(4.25, 4.45, 30).round(2),
        "Viscosity": np.random.uniform(1900, 2300, 30).astype(int),
        "Temp": np.random.uniform(85.0, 90.0, 30).round(1),
        "Cold_Storage_Temp": np.random.uniform(3.8, 6.5, 30).round(1),
        "Waste": np.random.uniform(0.5, 1.2, 30).round(2)
    })
    
    df['Unique_Batch'] = df['Shift'] + " - " + df['Batch_ID']
    
    # محاكاة انحرافات
    df.loc[(df['Shift'] == 'وردية الصباح') & (df['Batch_ID'].isin(['B4', 'B11'])), 'pH'] = 4.10
    df.loc[(df['Shift'] == 'وردية الصباح') & (df['Batch_ID'].isin(['B4', 'B11'])), 'Viscosity'] = 1650
    df.loc[(df['Shift'] == 'وردية الصباح') & (df['Batch_ID'].isin(['B4', 'B11'])), 'Temp'] = 82.0
    df.loc[(df['Shift'] == 'وردية الصباح') & (df['Batch_ID'].isin(['B4', 'B11'])), 'Cold_Storage_Temp'] = 8.2 
    df.loc[(df['Shift'] == 'وردية الصباح') & (df['Batch_ID'].isin(['B4', 'B11'])), 'Waste'] = 2.45
    df.loc[(df['Shift'] == 'وردية الصباح') & (df['Batch_ID'].isin(['B4', 'B11'])), 'Microbiological'] = '⚠️ ضعيف/تلوث'
    
    df.loc[(df['Shift'] == 'وردية المساء') & (df['Batch_ID'].isin(['B6', 'B15'])), 'pH'] = 4.08
    df.loc[(df['Shift'] == 'وردية المساء') & (df['Batch_ID'].isin(['B6', 'B15'])), 'Viscosity'] = 1600
    df.loc[(df['Shift'] == 'وردية المساء') & (df['Batch_ID'].isin(['B6', 'B15'])), 'Temp'] = 81.5
    df.loc[(df['Shift'] == 'وردية المساء') & (df['Batch_ID'].isin(['B6', 'B15'])), 'Cold_Storage_Temp'] = 7.9 
    df.loc[(df['Shift'] == 'وردية المساء') & (df['Batch_ID'].isin(['B6', 'B15'])), 'Waste'] = 2.80
    df.loc[(df['Shift'] == 'وردية المساء') & (df['Batch_ID'].isin(['B6', 'B15'])), 'Microbiological'] = '⚠️ ضعيف/تلوث'

    df['Status'] = np.where(
        (df['pH'] >= 4.20) & (df['pH'] <= 4.50) & 
        (df['Viscosity'] >= 1800) & 
        (df['Temp'] >= 84.0) &
        (df['Cold_Storage_Temp'] <= 7.0) &
        (df['Microbiological'] != '⚠️ ضعيف/تلوث'), 
        'إنتاج مطابـق', 
        '⚠️ مستبعد (انحراف CCP/تبريد/ميكروبيولوجي)'
    )
    
    def get_simplified_waste_type(row):
        if row['Status'] == 'إنتاج مطابـق':
            return 'هدر طبيعي (مسموح)'
        else:
            return 'هدر حرج (مستبعد)'

    df['Simplified_Waste_Type'] = df.apply(get_simplified_waste_type, axis=1)
    
    def get_rejection_reason(row):
        if row['Status'] == 'إنتاج مطابـق':
            return 'لا يوجد (مطابق للمواصفات)'
        reasons = []
        if row['pH'] < 4.20 or row['pH'] > 4.50:
            reasons.append(f"انحراف الحموضة pH ({row['pH']})")
        if row['Viscosity'] < 1800:
            reasons.append(f"إنفصال مصل / انخفاض لزوجة ({row['Viscosity']} cP)")
        if row['Temp'] < 84.0:
            reasons.append(f"انخفاض البسترة ({row['Temp']}°C)")
        if row['Cold_Storage_Temp'] > 7.0:
            reasons.append(f"ارتفاع حرارة التخزين ({row['Cold_Storage_Temp']}°C)")
        if row['Microbiological'] == '⚠️ ضعيف/تلوث':
            reasons.append("انحراف ميكروبيولوجي")
        return " + ".join(reasons) if reasons else 'انحراف حرج'

    df['Exclusion_Reason'] = df.apply(get_rejection_reason, axis=1)
    df['Trip_Action_Status'] = np.where(df['Status'] == 'إنتاج مطابـق', 'تشغيل طبيعي (Normal Flow)', 'تفعيل Trip Action (تحويل لخط الهدر)')
    
    return df

df_full = get_dashboard_data()

# الشريط الجانبي الفلاتر المتقدمة
st.sidebar.header("⚙️ خيارات الفلترة المتقدمة")

selected_shift = st.sidebar.selectbox("اختر الوردية:", ["الكل", "وردية الصباح", "وردية المساء"])

if selected_shift != "الكل":
    df_filtered_shift = df_full[df_full['Shift'] == selected_shift]
else:
    df_filtered_shift = df_full

st.sidebar.markdown("---")

available_batches = ["الكل"] + list(df_filtered_shift['Batch_ID'].unique())
selected_batch = st.sidebar.selectbox("🎯 اختر الباتش المطلوب فحصه:", available_batches)

if selected_batch != "الكل":
    df_filtered_shift = df_filtered_shift[df_filtered_shift['Batch_ID'] == selected_batch]

st.sidebar.markdown("---")

culture_options = ["الكل"] + list(df_full['Starter_Culture'].unique())
selected_culture = st.sidebar.selectbox("🦠 فلتر نوع بكتيريا البادئ (Starter Culture):", culture_options)

if selected_culture != "الكل":
    df_filtered_shift = df_filtered_shift[df_filtered_shift['Starter_Culture'] == selected_culture]

st.sidebar.markdown("---")

status_options = ["الكل"] + list(df_full['Status'].unique())
selected_status = st.sidebar.selectbox("📋 فلتر حالة الإنتاج:", status_options)

if selected_status != "الكل":
    df_filtered_shift = df_filtered_shift[df_filtered_shift['Status'] == selected_status]

st.sidebar.markdown("---")

waste_options = ["الكل"] + list(df_full['Simplified_Waste_Type'].unique())
selected_waste_type = st.sidebar.selectbox("📉 فلتر نوع الهدر:", waste_options)

if selected_waste_type != "الكل":
    df_filtered_shift = df_filtered_shift[df_filtered_shift['Simplified_Waste_Type'] == selected_waste_type]

st.sidebar.markdown("---")

min_pH_val = float(df_full['pH'].min())
max_pH_val = float(df_full['pH'].max())
ph_range = st.sidebar.slider("🧪 نطاق حموضة الـ pH:", min_value=min_pH_val, max_value=max_pH_val, value=(min_pH_val, max_pH_val))

st.sidebar.markdown("---")

min_cold_val = float(df_full['Cold_Storage_Temp'].min())
max_cold_val = float(df_full['Cold_Storage_Temp'].max())
cold_range = st.sidebar.slider("🧊 نطاق حرارة ثلاجات التخزين (°C):", min_value=min_cold_val, max_value=max_cold_val, value=(min_cold_val, max_cold_val))

# تطبيق كل الفلاتر
df = df_filtered_shift[
    (df_filtered_shift['pH'] >= ph_range[0]) & 
    (df_filtered_shift['pH'] <= ph_range[1]) &
    (df_filtered_shift['Cold_Storage_Temp'] >= cold_range[0]) &
    (df_filtered_shift['Cold_Storage_Temp'] <= cold_range[1])
]

st.sidebar.markdown("---")
st.sidebar.info(f"💡 عدد الباتشات المعروضة بعد التصفية: **{len(df)}** باتش.")

# تنبيه ديناميكي فوري لو فيه باتشات مستبعدة في النطاق الحالي
critical_count = len(df[df['Status'].str.contains('مستبعد', na=False)])
if critical_count > 0:
    st.error(f"🚨 **تنبيه عاجل من نظام HACCP:** تم رصد عدد **{critical_count}** باتش غير مطابق للمواصفات وتحويلهم لصمامات الهدر (Trip Action).")
else:
    st.success("✅ **حالة النظام مستقرة:** جميع الباتشات المعروضة مطابقة للمواصفات القياسية وسلسلة التبريد آمنة.")

# المؤشرات
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("متوسط حموضة pH", f"{df['pH'].mean():.2f}" if not df.empty else "0.00")
c2.metric("متوسط اللزوجة", f"{df['Viscosity'].mean():.0f} cP" if not df.empty else "0 cP")
c3.metric("حرارة البسترة", f"{df['Temp'].mean():.1f} °C" if not df.empty else "0.0 °C")
c4.metric("حرارة التخزين", f"{df['Cold_Storage_Temp'].mean():.1f} °C" if not df.empty else "0.0 °C")
c5.metric("متوسط نسبة الهدر", f"{df['Waste'].mean():.2f}%" if not df.empty else "0.00%")

st.markdown("---")

# 1️⃣ الفحوصات الأولية
st.subheader("📥 1. الفحوصات الأولية (حسي، كيميائي، ومايكروبيولوجي)")
col_sensory, col_chem, col_micro = st.columns(3)

with col_sensory:
    st.markdown("##### الفحص الحسي")
    if not df.empty:
        sensory_df = df["Sensory"].value_counts().reset_index()
        sensory_df.columns = ['الحالة', 'العدد']
        fig_sensory = px.bar(
            sensory_df, x='الحالة', y='العدد', color='الحالة',
            color_discrete_map={'ممتاز': '#154360', 'جيد': '#2980b9'}
        )
        fig_sensory.update_traces(width=0.42)
        fig_sensory.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=260, xaxis_title="", yaxis_title="العدد",
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_sensory, use_container_width=True)

with col_chem:
    st.markdown("##### التحاليل الكيميائية")
    if not df.empty:
        chem_df = df["Chemical_Analysis"].value_counts().reset_index()
        chem_df.columns = ['الحالة', 'العدد']
        fig_chem = px.bar(
            chem_df, x='الحالة', y='العدد', color='الحالة',
            color_discrete_map={'خالي من المضادات': '#1b4f72', 'مطابق للمواصفات': '#5499c7'}
        )
        fig_chem.update_traces(width=0.42)
        fig_chem.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=260, xaxis_title="", yaxis_title="العدد",
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_chem, use_container_width=True)

with col_micro:
    st.markdown("##### الفحص المايكروبيولوجي")
    if not df.empty:
        micro_df = df["Microbiological"].value_counts().reset_index()
        micro_df.columns = ['الحالة', 'العدد']
        fig_micro = px.bar(
            micro_df, x='الحالة', y='العدد', color='الحالة',
            color_discrete_map={'مطابق وبادئ نشط': '#2471a3', 'قبول آمن': '#85c1e9', '⚠️ ضعيف/تلوث': '#c0392b'}
        )
        fig_micro.update_traces(width=0.42)
        fig_micro.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=260, xaxis_title="", yaxis_title="العدد",
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_micro, use_container_width=True)

st.markdown("---")

target_shift_for_plots = selected_shift if selected_shift != "الكل" else "وردية الصباح"
base_shift_df = df_full[df_full['Shift'] == target_shift_for_plots].copy()
base_shift_df['Batch_Num_Int'] = base_shift_df['Batch_ID'].str.replace('B', '').astype(int)
df_sorted = base_shift_df.sort_values('Batch_Num_Int')

# 2️⃣ اللزوجة و الـ pH
st.subheader("🧪 2. قياسات الحموضة pH واللزوجة (منع انفصال مصل اللبن Syneresis)")
col_ph, col_visc = st.columns(2)

with col_ph:
    st.markdown("##### قياسات الحموضة pH (CCP2)")
    if not df_sorted.empty:
        df_sorted['pH_Color'] = ['مخالف' if (pd.notnull(p) and (p < 4.20 or p > 4.50)) else 'مطابق' for p in df_sorted['pH']]
        fig_ph = px.bar(
            df_sorted, x='Batch_ID', y='pH', color='pH_Color',
            color_discrete_map={'مطابق': '#5dade2', 'مخالف': '#c0392b'},
            category_orders={'Batch_ID': [f"B{i}" for i in range(1, 16)]}
        )
        fig_ph.add_hline(y=4.20, line_dash="dash", line_color="green")
        fig_ph.add_hline(y=4.50, line_dash="dash", line_color="green")
        fig_ph.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=300, yaxis_range=[3.8, 4.8],
            xaxis_title="", yaxis_title="pH", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_ph, use_container_width=True)

with col_visc:
    st.markdown("##### قياسات اللزوجة (cP) - كشف عيوب القوام")
    if not df_sorted.empty:
        df_sorted['Visc_Color'] = ['مخالف (إنفصال مصل)' if (pd.notnull(v) and v < 1800) else 'مطابق' for v in df_sorted['Viscosity']]
        fig_visc = px.bar(
            df_sorted, x='Batch_ID', y='Viscosity', color='Visc_Color',
            color_discrete_map={'مطابق': '#2980b9', 'مخالف (إنفصال مصل)': '#c0392b'},
            category_orders={'Batch_ID': [f"B{i}" for i in range(1, 16)]}
        )
        fig_visc.add_hline(y=1800, line_dash="dash", line_color="green")
        fig_visc.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=300, yaxis_range=[1400, 2500],
            xaxis_title="", yaxis_title="Viscosity (cP)", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_visc, use_container_width=True)

st.markdown("---")

# 3️⃣ حرارة البسترة وثلاجات التخزين
st.subheader("🔥 🧊 3. مراقبة المعاملة الحرارية وسلسلة التبريد (CCP1 & Cold Chain)")
col_pasteur, col_cold = st.columns(2)

with col_pasteur:
    st.markdown("##### حرارة البسترة (CCP1)")
    if not df_sorted.empty:
        fig_temp = px.line(df_sorted, x='Batch_ID', y='Temp', markers=True, category_orders={'Batch_ID': [f"B{i}" for i in range(1, 16)]})
        fig_temp.add_hline(y=84.0, line_dash="dash", line_color="#c0392b")
        fig_temp.update_traces(line_color='#2980b9', marker=dict(size=8))
        fig_temp.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=280, yaxis_range=[78, 92],
            xaxis_title="", yaxis_title="Temp (°C)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_temp, use_container_width=True)

with col_cold:
    st.markdown("##### درجات حرارة ثلاجات التخزين (Cold Chain Storage)")
    if not df_sorted.empty:
        fig_cold = px.line(df_sorted, x='Batch_ID', y='Cold_Storage_Temp', markers=True, category_orders={'Batch_ID': [f"B{i}" for i in range(1, 16)]})
        fig_cold.add_hline(y=7.0, line_dash="dash", line_color="#c0392b")
        fig_cold.update_traces(line_color='#16a085', marker=dict(size=8))
        fig_cold.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=280, yaxis_range=[2, 10],
            xaxis_title="", yaxis_title="Storage Temp (°C)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_cold, use_container_width=True)

st.markdown("---")

# 4️⃣ جدول المتابعة والقرار النهائي مع زر التصدير (Export CSV)
st.subheader("📊 4. جدول المتابعة والقرار النهائي وتحليل العيوب")

if not df.empty:
    df_display_temp = df.copy()
    df_display_temp['Batch_Num_Int'] = df_display_temp['Batch_ID'].str.replace('B', '').astype(int)
    df_display_temp = df_display_temp.sort_values(['Shift', 'Batch_Num_Int'])
    
    df_display_temp['Viscosity_cP'] = df_display_temp['Viscosity'].astype(str) + " cP"
    df_display_temp['Temp_C'] = df_display_temp['Temp'].astype(str) + " °C"
    df_display_temp['Cold_Temp_C'] = df_display_temp['Cold_Storage_Temp'].astype(str) + " °C"
    
    display_df = df_display_temp[['Shift', 'Batch_ID', 'Starter_Culture', 'pH', 'Viscosity_cP', 'Temp_C', 'Cold_Temp_C', 'Microbiological', 'Waste', 'Trip_Action_Status', 'Exclusion_Reason', 'Status']].rename(columns={
        'Shift': 'الوردية',
        'Batch_ID': 'رقم الباتش',
        'Starter_Culture': 'نوع البادئ',
        'pH': 'الحموضة (pH)',
        'Viscosity_cP': 'اللزوجة والقوام',
        'Temp_C': 'الحرارة',
        'Cold_Temp_C': 'حرارة التخزين',
        'Microbiological': 'الفحص المايكرو',
        'Waste': 'الهدر (%)',
        'Trip_Action_Status': 'حالة الـ Trip Action',
        'Exclusion_Reason': 'تحليل السبب / عيوب القوام',
        'Status': 'القرار النهائي'
    })
    
    def highlight_status(row):
        if 'مستبعد' in str(row['القرار النهائي']) or '⚠️' in str(row['القرار النهائي']):
            return ['background-color: #fdf2f2; color: #c0392b; font-weight: bold'] * len(row)
        return [''] * len(row)

    styled_table = display_df.style.apply(highlight_status, axis=1)
    st.dataframe(styled_table, use_container_width=True, hide_index=True)
    
    # زر تصدير التقرير الرسمي CSV
    csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 تحميل تقرير فحص الجودة الرسمي (CSV Report)",
        data=csv_data,
        file_name="HACCP_Yogurt_Quality_Report.csv",
        mime="text/csv",
    )

st.markdown("---")

# 5️⃣ أسباب الهدر والتحليل التشغيلي
st.subheader("📉 5. أسباب الهدر وتحليل عيوب القوام (Syneresis & Defects Analysis)")
st.markdown("""
* **1. هدر طبيعي (مسموح):** النسبة المسموح بها ضمن التشغيل الطبيعي لضمان استمرارية وكفاءة خط الإنتاج.
* **2. هدر حرج (مستبعد):** الباتشات التي يتم استبعادها نتيجة انحراف حرارة البسترة (CCP1)، حموضة التخمير (CCP2)، ارتفاع حرارة ثلاجات التخزين، أو عيوب قوام مثل **إنفصال مصل اللبن (Whey Syneresis)** الناتج عن انخفاض اللزوجة دون 1800 cP.
* **الإجراء الوقائي:** تفعيل صمامات التحويل التلقائي (Trip Action) لعزل الباتشات الحرجة وتعديل معلمات التبريد والتحضن فوراً.
""")

st.markdown("<br>", unsafe_allow_html=True)

# 6️⃣ الرسم البياني لنوع الهدر
st.subheader("📉 الرسم البياني لنوع الهدر (طبيعي / حرج)")
if not df.empty:
    waste_type_df = df['Simplified_Waste_Type'].value_counts().reset_index()
    waste_type_df.columns = ['نوع الهدر', 'عدد الباتشات']
    
    fig_waste = px.bar(
        waste_type_df, x='نوع الهدر', y='عدد الباتشات', color='نوع الهدر',
        color_discrete_map={'هدر طبيعي (مسموح)': '#2980b9', 'هدر حرج (مستبعد)': '#c0392b'}
    )
    fig_waste.update_traces(width=0.4)
    fig_waste.update_layout(
        margin=dict(l=10, r=10, t=10, b=10), height=320, xaxis_title="", yaxis_title="عدد الباتشات",
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_waste, use_container_width=True)

st.markdown("---")

# 7️⃣ التدابير التصحيحية والهاسب
st.subheader("🛠️ 7. التدابير التصحيحية وإجراءات الهاسب وأنواع البكتيريا (Corrective Actions & Cultures)")
st.markdown("##### 🦠 أنواع بكتيريا بادئ الزبادي الأساسية المستخدمة:")
st.markdown("""
* **Streptococcus thermophilus:** مسؤولة عن إنتاج الحموضة السريعة والنكهة المميزة في بداية مرحلة التخمير.
* **Lactobacillus delbrueckii subsp. bulgaricus:** مسؤولة عن تكوين المركبات المسؤولة عن القوام والنكهة (تفرز مادة Exopolysaccharides تعزز القوام وتمنع انفصال المصل).
* **Mix Blend (S.t + L.b):** التكافؤ التبادلي بين النوعين لضمان الوصول للـ pH المثالي (4.20 - 4.50).
""")

st.markdown("##### 1️⃣ CCP1 & Cold Chain (البسترة وسلسلة التبريد)")
st.markdown("""
* **الانحراف المحتمل:** انخفاض حرارة البسترة أو ارتفاع حرارة ثلاجة التخزين عن 7°C مما يؤدي لزيادة نشاط البكتيريا وحموضة زائدة.
* **الإجراء التصحيحي:** مراجعة وحدات التبريد فوراً، تحويل الباتشات المخالفة، وضبط درجات التبريد السريع (Blast Chilling).
""")

st.markdown("##### 2️⃣ CCP2 (مراقبة الحموضة pH واللزوجة وقوام الزبادي)")
st.markdown("""
* **الانحراف المحتمل:** خروج الـ pH عن (4.20 - 4.50) أو حدوث **إنفصال مصل اللبن (Syneresis)** وانخفاض اللزوجة عن 1800 cP.
* **الإجراء التصحيحي:** إيقاف التخمير فوراً، تعقيم الخطوط، تعديل نسب بادئات التخمير، وإعدام الباتش المتأثر لحماية المستهلك.
""")
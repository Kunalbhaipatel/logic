
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🛠️ Drilling Operations Dashboard (Filtered + Decision Logic)")

st.sidebar.header("Upload Sensor CSV")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    with st.spinner("Loading data..."):
        usecols = [
            'YYYY/MM/DD', 'HH:MM:SS',
            'Rate Of Penetration (ft_per_hr)', 'PLC ROP (ft_per_hr)',
            'Hook Load (klbs)', 'Standpipe Pressure (psi)',
            'Pump 1 strokes/min (SPM)', 'Pump 2 strokes/min (SPM)',
            'DAS Vibe Lateral Max (g_force)', 'DAS Vibe Axial Max (g_force)',
            'AutoDriller Limiting (unitless)',
            'DAS Vibe WOB Reduce (percent)', 'DAS Vibe RPM Reduce (percent)'
        ]

        df = pd.read_csv(uploaded_file, usecols=usecols)
        df['Timestamp'] = pd.to_datetime(df['YYYY/MM/DD'] + ' ' + df['HH:MM:SS'], format='%m/%d/%Y %H:%M:%S')
        df.set_index('Timestamp', inplace=True)
        df.drop(columns=['YYYY/MM/DD', 'HH:MM:SS'], inplace=True)

        st.success("File successfully loaded.")
        st.subheader("🔍 Preview")
        st.dataframe(df.head())

        st.sidebar.markdown("---")
        st.sidebar.header("📊 Filters")

        # Filters (using synthetic logic)
        min_rop = st.sidebar.slider("Min ROP (ft/hr)", 0, 100, 5)
        max_vibration = st.sidebar.slider("Max Vibe Lateral (g)", 0, 50, 25)
        min_hook_load = st.sidebar.slider("Min Hook Load (klbs)", 0, 150, 30)

        df_filtered = df[
            (df['Rate Of Penetration (ft_per_hr)'] >= min_rop) &
            (df['DAS Vibe Lateral Max (g_force)'] <= max_vibration) &
            (df['Hook Load (klbs)'] >= min_hook_load)
        ]

        st.markdown(f"### Filtered Data ({len(df_filtered)} rows)")
        st.dataframe(df_filtered.head(20))

        st.markdown("### 🔬 Decision Scoring Engine")

        def compute_status(row):
            score = 0
            if abs(row['Rate Of Penetration (ft_per_hr)'] - row['PLC ROP (ft_per_hr)']) > 15:
                score += 1
            if row['DAS Vibe Lateral Max (g_force)'] > 25:
                score += 1
            if row['AutoDriller Limiting (unitless)'] > 0:
                score += 1
            if row['DAS Vibe WOB Reduce (percent)'] > 0 or row['DAS Vibe RPM Reduce (percent)'] > 0:
                score += 1

            if score >= 3:
                return 'Overload Risk'
            elif score == 2:
                return 'Monitor'
            else:
                return 'Stable'

        df_filtered['Status'] = df_filtered.apply(compute_status, axis=1)
        st.dataframe(df_filtered[['Rate Of Penetration (ft_per_hr)', 'PLC ROP (ft_per_hr)',
                                  'DAS Vibe Lateral Max (g_force)', 'AutoDriller Limiting (unitless)',
                                  'Status']].tail(20))

        st.markdown("### 📈 Status Over Time")
        fig = px.scatter(df_filtered.reset_index(), x='Timestamp', y='Status', color='Status')
        st.plotly_chart(fig)

        st.sidebar.download_button("Download Filtered CSV", df_filtered.to_csv().encode(), "filtered_output.csv")


import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🛠️ Operational Diagnostics Dashboard (Real Metrics)")

st.sidebar.header("Upload Drilling Sensor CSV")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    with st.spinner("Loading data..."):
        usecols = [
            'YYYY/MM/DD', 'HH:MM:SS',
            'Rate Of Penetration (ft_per_hr)',
            'Hook Load (klbs)', 'Standpipe Pressure (psi)',
            'DAS Vibe Lateral Max (g_force)', 'SHAKER #3 (PERCENT)',
            'Flow (flow_percent)', 'Total Pump Output (gal_per_min)'
        ]

        df = pd.read_csv(uploaded_file, usecols=usecols)
        df['Timestamp'] = pd.to_datetime(df['YYYY/MM/DD'] + ' ' + df['HH:MM:SS'], format='%m/%d/%Y %H:%M:%S')
        df.set_index('Timestamp', inplace=True)
        df.drop(columns=['YYYY/MM/DD', 'HH:MM:SS'], inplace=True)

        st.success("Data loaded successfully.")

        tab1, tab2 = st.tabs(["📈 Data Preview", "🔬 Operational Diagnostics"])

        with tab1:
            st.markdown("### Head of File")
            st.dataframe(df.head(10))
            st.line_chart(df[['Rate Of Penetration (ft_per_hr)', 'SHAKER #3 (PERCENT)']])

        with tab2:
            mode = st.selectbox("Choose Diagnostic View", [
                "Screen Optimization",
                "Shaker Performance %",
                "Screen Utilization",
                "Washout Risk",
                "Downhole Issue",
                "Sidetrack Risk"
            ])

            if mode == "Screen Optimization":
                df['Screen Load Index (%)'] = (df['Flow (flow_percent)'] + df['SHAKER #3 (PERCENT)']) / 2
                st.line_chart(df['Screen Load Index (%)'])

            elif mode == "Shaker Performance %":
                df['Shaker Effectiveness'] = (100 - df['DAS Vibe Lateral Max (g_force)'] * 3).clip(0, 100)
                st.line_chart(df['Shaker Effectiveness'])

            elif mode == "Screen Utilization":
                df['Screen Utilization (%)'] = (df['SHAKER #3 (PERCENT)'] / df['Flow (flow_percent)']) * 100
                df['Screen Utilization (%)'] = df['Screen Utilization (%)'].clip(0, 150)
                st.line_chart(df['Screen Utilization (%)'])

            elif mode == "Washout Risk":
                df['Washout Risk'] = ((df['Rate Of Penetration (ft_per_hr)'] > 60) & (df['Standpipe Pressure (psi)'] < 500)).astype(int)
                st.area_chart(df['Washout Risk'])

            elif mode == "Downhole Issue":
                df['Downhole Flag'] = ((df['Hook Load (klbs)'] > 100) & (df['Rate Of Penetration (ft_per_hr)'] < 5)).astype(int)
                st.bar_chart(df['Downhole Flag'])

            elif mode == "Sidetrack Risk":
                df['ROP Δ'] = df['Rate Of Penetration (ft_per_hr)'].diff().abs()
                df['Sidetrack Alert'] = (df['ROP Δ'] > 30).astype(int)
                st.line_chart(df['Sidetrack Alert'])

        st.sidebar.download_button("Download Diagnostics CSV", df.to_csv().encode(), "diagnostic_output.csv")

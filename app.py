
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🛠️ Drilling Dashboard with Operational Diagnostics")

st.sidebar.header("Upload Drilling Data")
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

        st.success("Data loaded.")
        tab1, tab2 = st.tabs(["📈 Data Overview", "🔎 Operational Diagnostics"])

        with tab1:
            st.markdown("### Full Dataset Preview")
            st.dataframe(df.head(20))

            st.markdown("### Basic ROP & Vibration Trends")
            fig = px.line(df.reset_index(), x='Timestamp', y=['Rate Of Penetration (ft_per_hr)', 'DAS Vibe Lateral Max (g_force)'])
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.markdown("### 🔧 Diagnostics & Optimization")

            mode = st.selectbox("Optimization Target", [
                "Screen Optimization",
                "Shaker Performance",
                "Utilization",
                "Generic Issue Prediction"
            ])

            if mode == "Screen Optimization":
                st.info("Calculating screen optimization based on ROP vs. vibration...")
                df['Screen Load Estimate (%)'] = (df['Rate Of Penetration (ft_per_hr)'] * 2).clip(0, 100)
                st.line_chart(df['Screen Load Estimate (%)'])

            elif mode == "Shaker Performance":
                st.info("Estimating shaker performance as inverse of vibration intensity...")
                df['Shaker Performance (%)'] = (100 - df['DAS Vibe Lateral Max (g_force)'] * 3).clip(0, 100)
                st.line_chart(df['Shaker Performance (%)'])

            elif mode == "Utilization":
                st.info("Utilization defined from Hook Load & Pump Status...")
                df['Utilization (%)'] = (
                    (df['Hook Load (klbs)'] / df['Hook Load (klbs)'].max()) * 
                    ((df['Pump 1 strokes/min (SPM)'] + df['Pump 2 strokes/min (SPM)']) / 100)
                ).clip(0, 1) * 100
                st.line_chart(df['Utilization (%)'])

            elif mode == "Generic Issue Prediction":
                issue_type = st.selectbox("Select Issue Type", [
                    "Washout %",
                    "Downhole Issue",
                    "Sidetrack Issue"
                ])

                if issue_type == "Washout %":
                    st.warning("Washout risk flagged where ROP > 60 and Vibration < 10")
                    df['Washout Risk (%)'] = ((df['Rate Of Penetration (ft_per_hr)'] > 60) & (df['DAS Vibe Lateral Max (g_force)'] < 10)).astype(int) * 100
                    st.line_chart(df['Washout Risk (%)'])

                elif issue_type == "Downhole Issue":
                    st.warning("Flagged if Hook Load > 100 and ROP < 5")
                    df['Downhole Risk'] = ((df['Hook Load (klbs)'] > 100) & (df['Rate Of Penetration (ft_per_hr)'] < 5)).astype(int)
                    st.line_chart(df['Downhole Risk'])

                elif issue_type == "Sidetrack Issue":
                    st.warning("Flagged if ROP erratic with spikes over time")
                    df['ROP Change'] = df['Rate Of Penetration (ft_per_hr)'].diff().abs()
                    df['Sidetrack Risk'] = (df['ROP Change'] > 30).astype(int)
                    st.line_chart(df['Sidetrack Risk'])

        st.sidebar.download_button("Download Processed CSV", df.to_csv().encode(), "processed_with_diagnostics.csv")

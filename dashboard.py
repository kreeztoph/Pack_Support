import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide')

with st.expander('Expand to upload the excel file'):
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
sheet_named = {
                'FED_Sun': 'Front End Days - Sunday',
                'FED_Mon': 'Front End Days - Monday',
                'FED_Tue': 'Front End Days - Tuesday',
                'FED_Wed': 'Front End Days - Wednesday',
                'FEN_Sun': 'Front End Nights - Sunday',
                'FEN_Mon': 'Front End Nights - Monday',
                'FEN_Tue': 'Front End Nights - Tuesday',
                'FEN_Wed': 'Front End Nights - Wednesday',
                'BED_Wed': 'Back End Days - Wednesday',
                'BED_Thu': 'Back End Days - Thursday',
                'BED_Fri': 'Back End Days - Friday',
                'BED_Sat': 'Back End Days - Saturday',
                'BEN_Wed': 'Back End Nights - Wednesday',
                'BEN_Thu': 'Back End Nights - Thursday',
                'BEN_Fri': 'Back End Nights - Friday',
                'BEN_Sat': 'Back End Nights - Saturday',            
            }

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    tab_names = xls.sheet_names
    tabs = st.tabs(tab_names)

    for i, sheet in enumerate(tab_names):
        with tabs[i]:
            df = pd.read_excel(xls, sheet_name=sheet)
            df.rename(columns=lambda x: x.strip(), inplace=True)
            df = df.fillna(0)
            shift = sheet_named.get(sheet, 'Summary sheet')
            st.write(f"### {shift}")

            if "Function" in df.columns and "Total Paid Hours" in df.columns:
                df["Function"] = df["Function"].astype(str).str.strip()

                # Combine SLAM roles
                slam_mask = df["Function"].isin(["SLAM Kickout", "SLAM Operator"])
                slam_total = df.loc[slam_mask, "Total Paid Hours"].sum()
                df = df[~slam_mask]

                if slam_total > 0:
                    df = pd.concat([
                        df,
                        pd.DataFrame([{
                            "Function": "SLAM / KO Ops",
                            "Total Paid Hours": round(slam_total, 2)
                        }])
                    ], ignore_index=True)

                # Define threshold (Planned) hours
                thresholds = {
                    "afe water spider": 15,
                    "p2r water spider": 15,
                    "pack singles water spider": 0,
                    "process guide pack singles": 40,
                    "process guide pack multis": 40,
                    "pack ambassador": 0,
                    "slam / ko ops": 49
                }

                df["Function Lower"] = df["Function"].str.lower()
                df["Planned Hours"] = df["Function Lower"].map(thresholds).fillna(0)
           
                # Define color based on logic
                def get_tile_color(row):
                    if row["Planned Hours"] == 0:
                        return "orange"
                    elif row["Total Paid Hours"] > row["Planned Hours"]:
                        return "red"
                    elif row["Total Paid Hours"] < row["Planned Hours"]:
                        return "green"
                    else:
                        return "black"

                # Display individual colored tiles
                rows = df.to_dict("records")
                for i in range(0, len(rows), 6):
                    chunk = rows[i:i + 6]
                    cols = st.columns(6,border=True)
                    for j, row in enumerate(chunk):
                        with cols[j]:
                            color = get_tile_color(row)
                            st.markdown(
                                f"<div style='color:{color}; font-size: 18px; font-weight: bold;'>"
                                f"{row['Function']}<br>{row['Total Paid Hours']} hours used of {row['Planned Hours']} planned</div>",
                                unsafe_allow_html=True
                            )

                # --- Total summary ---
                total_used = df["Total Paid Hours"].sum()
                total_planned = df["Planned Hours"].sum()

                shift_summary_1, shift_summary_2 = st.columns([0.3, 0.7])
                with shift_summary_1:
                    st.markdown("## 🧾 Totals")
                    totals_1,totals_2 = st.columns(2, border=True)
                    with totals_1:
                        st.metric(label="Total Hours Used", value=round(total_used, 2))
                    with totals_2:
                        st.metric(label="Total Hours Planned", value=round(total_planned, 2))

                
                with shift_summary_2:
                    with st.container(height=600):
                        st.markdown("### 📊 Detailed Function Table")

                        def color_row(row):
                            if row["Planned Hours"] == 0:
                                return ['background-color: orange; color: black'] * len(row)
                            elif row["Total Paid Hours"] > row["Planned Hours"]:
                                return ['background-color: red; color: white'] * len(row)
                            elif row["Total Paid Hours"] < row["Planned Hours"]:
                                return ['background-color: green; color: white'] * len(row)
                            else:
                                return [''] * len(row)
                        # Create the DataFrame for display
                        display_df = df[["Function", "Total Paid Hours", "Planned Hours"]].copy()

                        # Apply styling + formatting
                        styled_df = (
                            display_df.style
                            .apply(color_row, axis=1)
                            .format({"Total Paid Hours": "{:.2f}", "Planned Hours": "{:.2f}"})
                        )
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)


            elif "Shift" in df.columns and "Total Paid Hours" in df.columns:
                df["Shift"] = df["Shift"].astype(str).str.strip()
                st.write('This is for the summary')
                # Creating columns
                cols = st.columns(4,border=True)

                # Displaying metrics
                for i, row in df.iterrows():
                    cols[i].metric(label=f"Shift: {row['Shift']}", value=row["Total Paid Hours"])
                vis_1,vis_2 = st.columns(2)
                with vis_1:  
                    st.markdown("**Average Unit Distribution %**")
        
                    fig2 = px.pie(
                        df,
                        values='Total Paid Hours',
                        names='Shift',
                        color_discrete_sequence=['#EF553B', '#00CC96', '#AB63FA', '#3B63FA'],
                        title='Dist',
                        hole= 0.6
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                with vis_2:
                    # Barplot: Total UPH per employee
                    fig_uph = px.bar(df.sort_values("Total Paid Hours", ascending=False),
                                    x="Shift", y="Total Paid Hours",
                                    color="Shift", title="Total Pack Support hours By Shift",
                                    labels={"Total Paid Hours": "Total Paid Hours"})
                    fig_uph.update_layout(xaxis_tickangle=-45, height=500)
                    st.plotly_chart(fig_uph, use_container_width=True)
            else:
                st.warning("This sheet does not contain 'Function' and 'Total Paid Hours' columns.")

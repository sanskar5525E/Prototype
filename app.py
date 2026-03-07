import streamlit as st
import pandas as pd

st.title("Simple Sales Dashboard")

# upload excel
file = st.file_uploader("Upload Excel file", type=["xlsx","csv"])

if file:
    df = pd.read_csv(file)

    st.subheader("Data Preview")
    st.dataframe(df)

    total_sales = df["Amount"].sum()

    st.metric("Total Sales", total_sales)

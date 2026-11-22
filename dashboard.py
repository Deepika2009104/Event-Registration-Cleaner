import streamlit as st
import pandas as pd

st.set_page_config(page_title="Registration Dashboard", layout="wide")

st.title("🎓 Event Registration Cleaner")
st.write("AI-Powered Registration Data Dashboard")

# Read files
try:
    clean_data = pd.read_csv("clean_list.csv")
    problem_data = pd.read_csv("problems.csv")

    # Dashboard metrics
    total_valid = len(clean_data)
    total_problems = len(problem_data)
    total_records = total_valid + total_problems

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Registrations", total_records)
    col2.metric("Valid Registrations", total_valid)
    col3.metric("Needs Fixing / Duplicates", total_problems)

    # Valid registrations
    st.header("✅ Valid Registrations")
    st.dataframe(clean_data, use_container_width=True)

    # Problem registrations
    st.header("⚠️ Registrations Needing Attention")
    st.dataframe(problem_data, use_container_width=True)

    # Branch chart
    if "branch" in clean_data.columns:
        st.header("📊 Registrations by Branch")
        st.bar_chart(clean_data["branch"].value_counts())

    # Year chart
    if "year" in clean_data.columns:
        st.header("📈 Registrations by Year")
        st.bar_chart(clean_data["year"].value_counts().sort_index())

    st.success("Dashboard loaded successfully!")

except FileNotFoundError:
    st.error("Output files not found. Please run main.py first.")
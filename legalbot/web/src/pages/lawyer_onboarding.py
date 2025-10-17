# legalbot/web/src/pages/lawyer_onboarding.py

import streamlit as st
import requests

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8705/api/v1";

st.set_page_config(page_title="⚖️ Lawyer Onboarding", layout="wide")

st.title("⚖️ LegalBOT Lawyer Onboarding Portal")
st.caption("Join our LegalBOT network to receive verified client cases automatically routed to your expertise area.")

st.markdown("---")

# --------------------- FORM ---------------------
with st.form("lawyer_onboard_form", clear_on_submit=False):
    st.subheader("👤 Lawyer Information")

    name = st.text_input("Full Name *", "")
    email = st.text_input("Email *", "")
    phone = st.text_input("Phone Number", "")
    firm_name = st.text_input("Law Firm / Organization", "")

    st.subheader("📚 Professional Details")

    category = st.selectbox(
        "Primary Practice Area *",
        ["tax", "contract", "property", "criminal", "family", "other"],
        index=0,
    )

    total_cases = st.number_input("Total Cases Handled", min_value=0, max_value=10000, value=0, step=1)
    win_percent = st.number_input("Win Percentage", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    consultation_fee = st.number_input("Consultation Fee (₹)", min_value=0.0, value=0.0, step=100.0)
    location = st.text_input("Practice Location (City / State)", "")

    submitted = st.form_submit_button("🚀 Submit & Register")

# --------------------- SUBMIT ---------------------
if submitted:
    if not name or not email:
        st.error("⚠️ Name and Email are required.")
    else:
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "category": category,
            "firm_name": firm_name,
            "total_cases": total_cases,
            "win_percent": win_percent,
            "consultation_fee": consultation_fee,
            "location": location,
        }

        try:
            resp = requests.post(f"{API_BASE}/lawyers", json=data)
            if resp.status_code == 200:
                result = resp.json()
                st.success(f"✅ Lawyer '{name}' successfully registered! ID: {result.get('lawyer_id')}")
            else:
                st.error(f"❌ Registration failed: {resp.text}")
        except Exception as e:
            st.error(f"🚨 Connection error: {e}")

# --------------------- LAWYER LISTING ---------------------
st.markdown("---")
st.subheader("📋 Registered Lawyers")

try:
    resp = requests.get(f"{API_BASE}/lawyers")
    if resp.status_code == 200:
        lawyers = resp.json().get("lawyers", [])
        if lawyers:
            import pandas as pd

            df = pd.DataFrame(lawyers)
            display_cols = [
                "id", "name", "email", "phone", "category",
                "firm_name", "win_percent", "consultation_fee", "location", "available"
            ]
            df = df[[c for c in display_cols if c in df.columns]]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No lawyers registered yet.")
    else:
        st.error(f"Failed to fetch lawyers: {resp.text}")
except Exception as e:
    st.error(f"Error fetching lawyers: {e}")

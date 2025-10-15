import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px

# -------------------- CONFIG --------------------
API_BASE = "http://localhost:8705/api/v1"  # ✅ FastAPI backend (Postgres)
st.set_page_config(page_title="🎫 LegalBOT Ticket Dashboard", layout="wide")

st.title("🎫 LegalBOT Ticket Management Dashboard")
st.caption("Monitor, filter, and manage routed legal support tickets in real time.")

# -------------------- SIDEBAR FILTERS --------------------
st.sidebar.header("🔍 Filters")

category = st.sidebar.selectbox(
    "Category",
    ["All", "tax", "contract", "property", "criminal", "family", "other", "unknown"],
    index=0,
)

status = st.sidebar.selectbox(
    "Status",
    ["All", "open", "in_review", "closed"],
    index=0,
)

auto_refresh = st.sidebar.checkbox("🔁 Auto-refresh every 30s", value=False)

# -------------------- FETCH TICKETS --------------------
def get_tickets(category=None, status=None):
    params = {}
    if category and category != "All":
        params["category"] = category
    if status and status != "All":
        params["status"] = status

    try:
        resp = requests.get(f"{API_BASE}/tickets", params=params)
        if resp.status_code == 200:
            return resp.json().get("tickets", [])
        else:
            st.error(f"⚠️ Failed to fetch tickets: {resp.text}")
            return []
    except Exception as e:
        st.error(f"❌ Connection error: {e}")
        return []


# -------------------- MAIN FETCH --------------------
tickets = get_tickets(category, status)

if not tickets:
    st.warning("No tickets found for the current filter.")
    st.stop()

df = pd.DataFrame(tickets)
df = df.sort_values(by="timestamp", ascending=False)

# -------------------- DASHBOARD METRICS --------------------
st.markdown("### 📊 Ticket Summary")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Tickets", len(df))
with col2:
    st.metric("Open Tickets", len(df[df["ticket_status"] == "open"]))
with col3:
    st.metric("In Review", len(df[df["ticket_status"] == "in_review"]))
with col4:
    st.metric("Closed Tickets", len(df[df["ticket_status"] == "closed"]))

# -------------------- ANALYTICS VISUALS --------------------
with st.expander("📈 Ticket Analytics Dashboard", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        cat_count = df["query_category"].value_counts().reset_index()
        cat_count.columns = ["Category", "Count"]
        fig = px.bar(cat_count, x="Category", y="Count", title="Tickets by Category", text="Count")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        status_count = df["ticket_status"].value_counts().reset_index()
        status_count.columns = ["Status", "Count"]
        fig2 = px.pie(status_count, names="Status", values="Count", title="Tickets by Status", hole=0.3)
        st.plotly_chart(fig2, use_container_width=True)

# -------------------- DATA TABLE --------------------
st.markdown("### 📋 Ticket Overview")

st.dataframe(
    df[
        [
            "ticket_id",
            "timestamp",
            "query_category",
            "ticket_tag",
            "ticket_status",
            "question",
            "user_name",
            "model_used",
            "confidence",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

# -------------------- TICKET DETAIL MODAL --------------------
st.markdown("### 🕵️ View or Update Ticket")

ticket_id = st.text_input("Enter Ticket ID to View or Update")

if ticket_id:
    resp = requests.get(f"{API_BASE}/ticket/{ticket_id}")
    if resp.status_code == 200:
        ticket = resp.json().get("ticket", {})
        if not ticket:
            st.warning("Ticket not found in database.")
        else:
            st.success(f"Ticket Found: {ticket_id}")

            # Two-column layout for details
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🧾 Question:** {ticket.get('question', 'N/A')}")
                st.markdown(f"**📘 Category:** `{ticket.get('query_category', 'N/A')}`")
                st.markdown(f"**🏷 Tag:** {ticket.get('ticket_tag', 'N/A')}")
                st.markdown(f"**💬 Status:** {ticket.get('ticket_status', 'N/A')}")
                st.markdown(f"**🤖 Model:** {ticket.get('model_used', 'N/A')}")
            with col2:
                st.markdown(f"**📞 User:** {ticket.get('user_name', 'N/A')} ({ticket.get('user_phone', 'N/A')})")
                st.markdown(f"**🧮 Confidence:** {round(float(ticket.get('confidence', 0.0)), 2)}")
                st.markdown(f"**📅 Timestamp:** {ticket.get('timestamp', 'N/A')}")
                st.markdown(f"**🧩 Retrieval Mode:** {ticket.get('retrieval_mode', 'N/A')}")

            with st.expander("📜 Answer & Context"):
                st.write(ticket.get("answer", "No answer text found."))

            with st.expander("🧾 Sources (if any)"):
                import json
                sources = ticket.get("sources_json")
                if isinstance(sources, str):
                    try:
                        sources = json.loads(sources)
                    except Exception:
                        pass
                st.json(sources or [])

            # --- Update Status ---
            st.markdown("### 🛠 Update Ticket Status")
            new_status = st.selectbox(
                "Select new status",
                ["open", "in_review", "closed"],
                index=["open", "in_review", "closed"].index(ticket.get("ticket_status", "open"))
                if ticket.get("ticket_status", "open") in ["open", "in_review", "closed"]
                else 0,
            )

            if st.button("✅ Update Status"):
                update_resp = requests.post(
                    f"{API_BASE}/ticket/{ticket_id}/update",
                    params={"status": new_status},
                )
                if update_resp.status_code == 200:
                    st.success(f"✅ Ticket {ticket_id} updated to '{new_status}'.")
                    st.rerun()
                else:
                    st.error(f"⚠️ Update failed: {update_resp.text}")
    else:
        st.error("Ticket not found.")

# -------------------- AUTO REFRESH --------------------
if auto_refresh:
    st.info("⏳ Auto-refresh enabled (updates every 30 seconds)")
    time.sleep(30)
    st.rerun()

# -------------------- MANUAL REFRESH --------------------
if st.button("🔄 Refresh Tickets"):
    st.rerun()

# legalbot/web/src/pages/chat_ui.py

import streamlit as st
import requests
import uuid

API_BASE = "http://localhost:8705/api/v1"

st.set_page_config(page_title="⚖️ LegalBOT Chat", layout="wide")
st.title("⚖️ LegalBOT - AI Legal Assistant")
st.caption("Ask legal questions and get concise, evidence-backed answers.")

# Session setup
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Chat input
query = st.chat_input("Type your legal question here...")

# Handle chat submission
if query:
    with st.spinner("Thinking..."):
        resp = requests.post(
            f"{API_BASE}/chat",
            json={
                "query": query,
                "session_id": st.session_state["session_id"],
                "input_channel": "web",
                "kb": "legal_chunks_db",
            },
        )

        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer", "No answer.")
            category = data.get("query_category", "unknown")
            ticket_tag = data.get("ticket_tag", "")
            sources = data.get("sources", [])

            st.session_state["chat_history"].append({
                "user": query,
                "bot": answer,
                "category": category,
                "ticket_tag": ticket_tag,
                "sources": sources
            })
        else:
            st.error(f"Error: {resp.text}")

# Display chat history
for chat in st.session_state["chat_history"]:
    with st.chat_message("user"):
        st.markdown(chat["user"])
    with st.chat_message("assistant"):
        st.markdown(chat["bot"])
        st.caption(f"**Category:** {chat['category']} | **Route:** {chat['ticket_tag']}")
        if chat["sources"]:
            with st.expander("📚 Sources"):
                for src in chat["sources"]:
                    st.markdown(f"- {src.get('source')} — _{src.get('snippet')[:150]}..._")

# Sidebar info
st.sidebar.markdown("### ⚙️ Session Info")
st.sidebar.markdown(f"Session ID: `{st.session_state['session_id']}`")

if st.sidebar.button("🗑 Clear Chat"):
    st.session_state["chat_history"] = []
    st.rerun()
